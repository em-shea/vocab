"""Give the Founding Tester badge to the beta cohort.

Usage (on your laptop, after `awsp em`):
    python scripts/grant_founding_tester.py prod testers.txt            # dry run
    python scripts/grant_founding_tester.py prod testers.txt --apply

testers.txt: one email address per line.

Writes only one attribute, 'Founding tester' = true, on each matching user item
(update_item with attribute_exists, so it never creates a user). Nothing is
deleted or replaced. Without --apply it only prints who would get the badge.
"""
import sys

import boto3
from boto3.dynamodb.conditions import Key


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    apply = '--apply' in sys.argv
    if len(args) != 2 or args[0] not in ('staging', 'prod'):
        sys.exit(__doc__)
    stage, path = args
    wanted = {l.strip().lower() for l in open(path) if l.strip()}
    table = boto3.resource('dynamodb', region_name='us-east-1').Table(f'VocabAppTable-{stage}')

    found = {}
    kwargs = {'IndexName': 'GSI1', 'KeyConditionExpression': Key('GSI1PK').eq('USER')}
    while True:
        page = table.query(**kwargs)
        for item in page['Items']:
            if item.get('SK') != item.get('PK'):
                continue  # subscriptions share GSI1PK 'USER'
            email = str(item.get('Email address', '')).lower()
            if email in wanted:
                found[email] = item['PK']
        if 'LastEvaluatedKey' not in page:
            break
        kwargs['ExclusiveStartKey'] = page['LastEvaluatedKey']

    for email in sorted(wanted):
        pk = found.get(email)
        if not pk:
            print(f'not found   {email}')
            continue
        if apply:
            table.update_item(
                Key={'PK': pk, 'SK': pk},
                UpdateExpression='SET #f = :t',
                ConditionExpression='attribute_exists(PK)',
                ExpressionAttributeNames={'#f': 'Founding tester'},
                ExpressionAttributeValues={':t': True},
            )
            print(f'granted     {email}')
        else:
            print(f'would grant {email}')
    if not apply:
        print('\nDry run. Add --apply to write.')


if __name__ == '__main__':
    main()
