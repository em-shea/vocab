"""Unsubscribe addresses that hard-bounce or mark our email as spam.

SES publishes bounce and complaint notifications to an SNS topic (set on the
haohaotiantian.com identity), which invokes this function. Once that's in place,
SES's "email feedback forwarding" can be switched off, which is what stops the
bounce emails landing in the vocab@/signin@ inboxes.

Only permanent bounces unsubscribe someone. Transient bounces (mailbox full,
server down, some auto-replies) are left alone.
"""
import os
import json
import datetime

import boto3

import user_service

cognito_client = boto3.client('cognito-idp', region_name=os.environ['AWS_REGION'])
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])


def lambda_handler(event, context):
    for record in event['Records']:
        notification = json.loads(record['Sns']['Message'])
        for address in addresses_to_unsubscribe(notification):
            unsubscribe_address(address, reason(notification))


def reason(notification):
    if notification.get('notificationType') == 'Complaint':
        return 'complaint'
    return 'bounce'


def addresses_to_unsubscribe(notification):
    # Identity notifications use 'notificationType'; event publishing uses 'eventType'.
    kind = notification.get('notificationType') or notification.get('eventType')

    if kind == 'Bounce':
        bounce = notification.get('bounce', {})
        if bounce.get('bounceType') != 'Permanent':
            print(f"Ignoring {bounce.get('bounceType')} bounce.")
            return []
        recipients = bounce.get('bouncedRecipients', [])
    elif kind == 'Complaint':
        recipients = notification.get('complaint', {}).get('complainedRecipients', [])
    else:
        print(f"Ignoring notification type {kind}.")
        return []

    return [r['emailAddress'].strip().lower() for r in recipients if r.get('emailAddress')]


def unsubscribe_address(email, why):
    try:
        response = cognito_client.admin_get_user(
            UserPoolId=os.environ['USER_POOL_ID'],
            Username=email,
        )
    except cognito_client.exceptions.UserNotFoundException:
        # Staging and prod share the sending domain, so the other stage's
        # addresses arrive here too. Nothing to do.
        print(f"No user for {why} address {email}, skipping.")
        return

    cognito_id = response['Username']
    user = user_service.get_single_user(cognito_id)
    date = datetime.datetime.now().isoformat()

    count = 0
    for subscription in user.subscriptions or []:
        if subscription.status != 'subscribed':
            continue
        table.update_item(
            Key={
                "PK": "USER#" + cognito_id,
                "SK": "LIST#" + subscription.list_id + "#" + subscription.character_set.upper(),
            },
            UpdateExpression="set #s = :status, #d = :date",
            ExpressionAttributeValues={":status": "unsubscribed", ":date": date},
            ExpressionAttributeNames={"#s": "Status", "#d": "Date unsubscribed"},
        )
        count += 1

    print(f"Unsubscribed {cognito_id} from {count} list(s) after a {why}.")
