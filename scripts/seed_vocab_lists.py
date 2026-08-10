#!/usr/bin/env python3
"""Write the curated vocab list METADATA items into DynamoDB.

The six HSK lists used to be hardcoded in vocab_list_service.py. Their words have
always lived in DynamoDB under LIST#<id> / WORD#<id>; this seeds the matching
LIST#<id> / METADATA item so the list set itself is data-driven too.

The list ids are the original UUIDs - every existing subscription references them,
so they must not change.

Usage:
    python scripts/seed_vocab_lists.py --table VocabAppTable-staging
    python scripts/seed_vocab_lists.py --table VocabAppTable-prod --dry-run

Re-running is safe: existing items are left alone unless --overwrite is passed.
"""
import argparse
import json
import os
import sys

import boto3
from botocore.exceptions import ClientError

SEED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'seed', 'vocab_lists.json')


def build_item(vocab_list):
    return {
        'PK': 'LIST#' + vocab_list['list_id'],
        'SK': 'METADATA',
        'List name': vocab_list['list_name'],
        'List difficulty level': vocab_list['list_difficulty_level'],
        'Date created': vocab_list['date_created'],
        'Created by': vocab_list['created_by'],
        'Visibility': vocab_list['visibility'],
        # Indexed so the whole list set is one GSI1 query
        'GSI1PK': 'LIST',
        'GSI1SK': 'LIST#' + vocab_list['list_id'],
    }


def seed(table_name, region, dry_run=False, overwrite=False):
    with open(SEED_FILE) as fh:
        vocab_lists = json.load(fh)

    table = boto3.resource('dynamodb', region_name=region).Table(table_name)

    written, skipped = 0, 0
    for vocab_list in vocab_lists:
        item = build_item(vocab_list)

        if dry_run:
            print(f"[dry-run] would write {item['PK']} / {item['SK']} - {item['List name']}")
            written += 1
            continue

        put_kwargs = {'Item': item}
        if not overwrite:
            # Never clobber a list that already exists - its metadata may have been
            # edited since seeding
            put_kwargs['ConditionExpression'] = 'attribute_not_exists(PK)'

        try:
            table.put_item(**put_kwargs)
            print(f"wrote {item['PK']} - {item['List name']}")
            written += 1
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(f"exists, skipping {item['PK']} - {item['List name']}")
                skipped += 1
            else:
                raise

    print(f"\n{written} written, {skipped} skipped.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--table', required=True, help='DynamoDB table name, e.g. VocabAppTable-staging')
    parser.add_argument('--region', default='us-east-1')
    parser.add_argument('--dry-run', action='store_true', help='Print what would be written and exit')
    parser.add_argument('--overwrite', action='store_true', help='Replace list metadata that already exists')
    args = parser.parse_args()

    seed(args.table, args.region, dry_run=args.dry_run, overwrite=args.overwrite)


if __name__ == '__main__':
    sys.exit(main())
