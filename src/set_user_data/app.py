import os
import json
import boto3
from boto3.dynamodb.conditions import Key

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# For a given user (requires sign-in), update user metadata
def lambda_handler(event, context):

    print('event', event)
    cognito_user_id = event['requestContext']['authorizer']['claims']['sub']
    print('user id',cognito_user_id)

    body = json.loads(event["body"])

    error_message = {
        'statusCode': 502,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : false}'
    }

    try:
        updated = update_user_data(cognito_user_id, body)
    except NothingToUpdate:
        print(f"No recognised fields to update - {cognito_user_id}.")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Origin': '*',
            },
            'body': '{"success" : false, "message" : "No recognised fields to update."}'
        }
    except Exception as e:
        print(f"Error: Failed to update user data - {cognito_user_id}.")
        print(e)
        return error_message

    return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Origin': '*',
            },
            'body': '{"success" : true}'
        }

class NothingToUpdate(Exception):
    """Raised when a request carries no field this endpoint knows how to set."""


# Request field -> DynamoDB attribute. Anything not listed here is ignored, so a
# caller cannot write arbitrary attributes onto a user record.
UPDATABLE_FIELDS = {
    'user_alias': 'User alias',
    'user_alias_pinyin': 'User alias pinyin',
    'user_alias_emoji': 'User alias emoji',
    'character_set_preference': 'Character set preference',
    'language_preference': 'Language preference',
}

# Guard against a typo or a bad client writing something unexpected.
ALLOWED_VALUES = {
    'character_set_preference': {'simplified', 'traditional'},
    'language_preference': {'en', 'cn'},
}


def update_user_data(cognito_user_id, body):
    """Update whichever known fields the request carries.

    Previously this required all four fields on every call and raised KeyError
    otherwise, so it could only ever be used by the full profile form. The
    preferences switch sends language and character set alone, so the update is
    now built from whatever is present.
    """
    names, values, assignments = {}, {}, []

    for i, (field, attribute) in enumerate(UPDATABLE_FIELDS.items()):
        if field not in body:
            continue
        value = body[field]
        allowed = ALLOWED_VALUES.get(field)
        if allowed and value not in allowed:
            print(f"Ignoring {field}: {value!r} is not one of {sorted(allowed)}.")
            continue
        names[f'#f{i}'] = attribute
        values[f':v{i}'] = value
        assignments.append(f'#f{i} = :v{i}')

    if not assignments:
        raise NothingToUpdate()

    return table.update_item(
        Key={
            'PK': "USER#" + cognito_user_id,
            'SK': "USER#" + cognito_user_id
        },
        UpdateExpression='set ' + ', '.join(assignments),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
        ReturnValues="UPDATED_NEW"
    )