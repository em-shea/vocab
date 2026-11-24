import os
import json
import boto3
from boto3.dynamodb.conditions import Key

import user_service
import review_word_service
import dynamodb_service

# Sends each device that opted in a notification with today's word for each
# list its user takes (Emily, 2026-11-23). Runs on the same "todays-words-set"
# event as the daily email, as a separate function, so a push problem can never
# hold up or break the email.
#
# Reads users, today's words and PUSH# items. The only write is removing a
# PUSH# item the push service says no longer exists (404/410): that device
# turned notifications off or uninstalled the app. Nothing else is changed.

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])
idempotency_table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['IDEMPOTENCY_TABLE'])

CONSUMER = "SendPush"
SITE = os.environ.get('SITE_URL', 'https://haohaotiantian.com')
TTL_SECONDS = 20 * 60 * 60  # undelivered after 20 hours: the next day's word is nearly due

TEXT = {
    'en': {'title': "Today's word", 'title_many': "Today's words"},
    'cn': {'title': "今日词语", 'title_many': "今日词语"},
}


def lambda_handler(event, context):
    print('event: ', event)
    key = event['detail']['idempotency-key']
    if idempotency_table.query(KeyConditionExpression=Key('IdempotencyKey').eq(key) & Key('Consumer').eq(CONSUMER))['Items']:
        print(f'Push already sent for {key}')
        return
    idempotency_table.put_item(Item={'IdempotencyKey': key, 'Consumer': CONSUMER, 'Date': event.get('time', '')})

    todays_words = dict(review_word_service.get_review_words(list_id=None, date_range=0))
    devices = devices_by_user(push_items())
    if not devices:
        print('No devices have notifications on.')
        return

    private_key = vapid_private_key()
    sent = removed = failed = 0
    for user in user_service.get_all_users():
        user_devices = devices.get(user.user_id)
        if not user_devices:
            continue
        message = build_message(user, todays_words)
        if message is None:
            continue
        for item in user_devices:
            outcome = send(item, message, private_key)
            if outcome == 'sent':
                sent += 1
            elif outcome == 'gone':
                remove(item)
                removed += 1
            else:
                failed += 1
    print(f"{sent} notifications sent, {removed} expired devices removed, {failed} failed.")


def push_items():
    return dynamodb_service.query_all_pages(table, IndexName='GSI1', KeyConditionExpression=Key('GSI1PK').eq('PUSH'))


def devices_by_user(items):
    devices = {}
    for item in items:
        user_id = item.get('PK', '')[len('USER#'):]
        if user_id and item.get('Endpoint'):
            devices.setdefault(user_id, []).append(item)
    return devices


def build_message(user, todays_words):
    """The notification for one user, or None when none of their lists has a word today."""
    lines, seen = [], set()
    for sub in user.subscriptions or []:
        if sub.status != 'subscribed' or sub.list_id in seen:
            continue
        seen.add(sub.list_id)
        words = todays_words.get(sub.list_id) or []
        if not words:
            continue
        word = words[0]['word']
        chars = word.get('traditional') if sub.character_set == 'traditional' else word.get('simplified')
        chars = chars or word.get('simplified', '')
        lines.append(f"{chars} {word.get('pinyin', '')} · {word.get('definition', '').split(';')[0].strip()}")
    if not lines:
        return None
    text = TEXT.get(getattr(user, 'language_preference', 'en'), TEXT['en'])
    return {
        'title': text['title'] if len(lines) == 1 else text['title_many'],
        'body': '\n'.join(lines),
        'url': SITE + '/profile',
        'tag': 'daily-word',
    }


def vapid_private_key():
    ssm = boto3.client('ssm', region_name=os.environ['AWS_REGION'])
    return ssm.get_parameter(Name=os.environ['VAPID_KEY_PARAM'], WithDecryption=True)['Parameter']['Value']


def send(item, message, private_key):
    """'sent', 'gone' (the device unsubscribed; remove it) or 'failed'."""
    from pywebpush import webpush, WebPushException
    try:
        webpush(
            subscription_info={'endpoint': item['Endpoint'], 'keys': {'p256dh': item['P256dh'], 'auth': item['Auth']}},
            data=json.dumps(message, ensure_ascii=False),
            vapid_private_key=private_key,
            vapid_claims={'sub': 'mailto:nihao@haohaotiantian.com'},
            ttl=TTL_SECONDS,
        )
        return 'sent'
    except WebPushException as e:
        status = getattr(getattr(e, 'response', None), 'status_code', None)
        if status in (404, 410):
            return 'gone'
        print(f"Error: push failed ({status}) for {item.get('PK')}: {e}")
        return 'failed'
    except Exception as e:
        print(f"Error: push failed for {item.get('PK')}: {e}")
        return 'failed'


def remove(item):
    # Only ever a PUSH# item, by its exact key.
    if not str(item.get('SK', '')).startswith('PUSH#'):
        return
    table.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})
