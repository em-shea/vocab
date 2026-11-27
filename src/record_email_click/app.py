"""Record clicks on links in the daily email (staging only until cutover).

The daily email is sent with an SES configuration set that has click tracking
on. SES rewrites each link to go through its own redirect, then publishes a
Click event to an SNS topic, which invokes this function.

Each click becomes one new item in EmailClicksTable-<stage>, a table of its own:
  PK  Email      the subscriber's address
  SK  ClickedAt  ISO timestamp, then '#' and the SES message ID
plus Campaign (the message's 'campaign' tag), Link (the link's 'link' tag) and Url.

Writes: put_item into EmailClicksTable only. It never reads, changes or deletes
anything in the main VocabAppTable.
"""
import os
import json

import boto3

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['CLICKS_TABLE'])


def lambda_handler(event, context):
    for record in event['Records']:
        item = click_item(json.loads(record['Sns']['Message']))
        if item:
            table.put_item(Item=item)


def _first(tags, name):
    values = (tags or {}).get(name) or []
    return values[0] if values else ''


def click_item(notification):
    if notification.get('eventType') != 'Click':
        return None
    mail = notification.get('mail', {})
    click = notification.get('click', {})
    recipients = mail.get('destination') or []
    if not recipients:
        return None
    return {
        'Email': recipients[0].lower(),
        'ClickedAt': f"{click.get('timestamp', '')}#{mail.get('messageId', '')}",
        'Campaign': _first(mail.get('tags'), 'campaign'),
        'Link': _first(click.get('linkTags'), 'link'),
        'Url': click.get('link', ''),
    }
