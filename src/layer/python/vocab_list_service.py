import os
import boto3
from boto3.dynamodb.conditions import Key

import dynamodb_service

import sys
sys.path.append('../tests/')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Vocab list metadata lives in DynamoDB as LIST#<list_id> / METADATA items, indexed
# on GSI1 under GSI1PK 'LIST' so the whole set can be read with one query.
#
# Visibility governs who may read a list. The six HSK lists (and any future curated
# list such as 成语) are admin-owned and public; user-uploaded lists default to
# private. Anonymous read paths - the home page sample endpoint and the public
# /review endpoint - must use get_public_vocab_lists() so a user's own list can
# never be served to someone else.
GSI1PK_LIST = 'LIST'
SK_METADATA = 'METADATA'

VISIBILITY_PUBLIC = 'public'
VISIBILITY_PRIVATE = 'private'

CREATED_BY_ADMIN = 'admin'


def get_vocab_lists():
    """Every list, regardless of visibility. For internal/admin paths only."""
    items = dynamodb_service.query_all_pages(
        table,
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq(GSI1PK_LIST)
    )
    return [_format_list(item) for item in items]


def get_public_vocab_lists():
    """Lists any caller may read. Use this on unauthenticated paths."""
    return [l for l in get_vocab_lists() if l['visibility'] == VISIBILITY_PUBLIC]


def get_vocab_lists_for_user(cognito_id):
    """Public lists plus the lists this user owns."""
    owner = 'USER#' + cognito_id
    return [
        l for l in get_vocab_lists()
        if l['visibility'] == VISIBILITY_PUBLIC or l['created_by'] == owner
    ]


def get_vocab_list(list_id):
    """Single list's metadata, or None if it does not exist."""
    response = table.get_item(
        Key={'PK': 'LIST#' + list_id, 'SK': SK_METADATA}
    )
    item = response.get('Item')
    if item is None:
        return None
    return _format_list(item)


def is_list_readable_by(vocab_list, cognito_id=None):
    """Authorisation check for a single list.

    A missing list is not readable. A public list is readable by anyone, including
    anonymous callers. A private list is readable only by its owner.
    """
    if vocab_list is None:
        return False
    if vocab_list['visibility'] == VISIBILITY_PUBLIC:
        return True
    if cognito_id is None:
        return False
    return vocab_list['created_by'] == 'USER#' + cognito_id


def _format_list(item):
    # .get() with defaults so lists written before a field existed still load
    return {
        "list_name": item.get('List name', ''),
        "list_id": item['PK'].split('#')[1],
        "list_difficulty_level": item.get('List difficulty level', ''),
        "date_created": item.get('Date created', ''),
        "created_by": item.get('Created by', CREATED_BY_ADMIN),
        # Absent Visibility means a list seeded before the field existed, i.e. one of
        # the original admin HSK lists. Defaulting those to public preserves today's
        # behaviour; user lists are always written with an explicit value.
        "visibility": item.get('Visibility', VISIBILITY_PUBLIC),
    }
