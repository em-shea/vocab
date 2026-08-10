"""Root pytest configuration for the vocab app test suite.

This file is imported by pytest before any test module is collected, so the
environment variables below are set *before* the handler/layer modules run their
import-time boto3 setup (e.g. ``table = boto3.resource(...).Table(os.environ['TABLE_NAME'])``).
That removes the old need for each test to wrap its imports in
``mock.patch.dict('os.environ', ...)`` and the fragile reliance on import order.

It also provides ``moto`` fixtures so tests can exercise real DynamoDB behaviour
against an in-memory mock instead of hand-patching every service function.
"""

import os

import boto3
import pytest
from moto import mock_aws

# ---------------------------------------------------------------------------
# Environment — set before test modules import the code under test.
# Values are dummies; real infra is never touched. TABLE_NAME / IDEMPOTENCY_TABLE
# match the names created by the moto fixtures below so module-level Table()
# bindings resolve to the mocked tables.
# ---------------------------------------------------------------------------
_TEST_ENV = {
    "AWS_DEFAULT_REGION": "us-east-1",
    "AWS_REGION": "us-east-1",
    # Dummy credentials so boto3/moto never fall back to a real profile.
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "AWS_SECURITY_TOKEN": "testing",
    "AWS_SESSION_TOKEN": "testing",
    # Table + bucket + misc names read at import time or run time by handlers.
    "TABLE_NAME": "VocabAppTable-test",
    "IDEMPOTENCY_TABLE": "VocabAppIdempotencyTable-test",
    "BACKUPS_BUCKET_NAME": "hhtt-backups-test",
    "ANNOUNCEMENTS_BUCKET": "hhtt-announcements-test",
    "EVENT_BUS_NAME": "vocab-event-bus-test",
    "USER_POOL_ID": "us-east-1_testpool",
    "URL": "https://haohaotiantian.com",
    "OTP_SECRET_KEY": "test-otp-secret-key",
    "STAGE": "staging",
}

for _key, _value in _TEST_ENV.items():
    os.environ.setdefault(_key, _value)

TABLE_NAME = _TEST_ENV["TABLE_NAME"]
IDEMPOTENCY_TABLE = _TEST_ENV["IDEMPOTENCY_TABLE"]
REGION = _TEST_ENV["AWS_REGION"]


# ---------------------------------------------------------------------------
# moto fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def aws():
    """Activate moto so all AWS calls hit the in-memory mock backends."""
    with mock_aws():
        yield


@pytest.fixture
def dynamodb_table(aws):
    """Create the single-table DynamoDB table (PK/SK + GSI1) and yield the resource.

    Schema mirrors ``DynamoDBTable`` in template.yaml. The table name matches
    ``TABLE_NAME`` so handler/layer module-level ``Table(...)`` bindings resolve here.
    """
    client = boto3.client("dynamodb", region_name=REGION)
    client.create_table(
        TableName=TABLE_NAME,
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    yield boto3.resource("dynamodb", region_name=REGION).Table(TABLE_NAME)


@pytest.fixture
def seeded_vocab_lists(dynamodb_table):
    """Table with the six curated HSK list METADATA items written.

    Uses the same seed file and item builder as ``scripts/seed_vocab_lists.py``, so
    a change to the deployed item shape shows up here rather than drifting silently.
    Yields the parsed seed data.
    """
    import json

    from seed_vocab_lists import SEED_FILE, build_item

    with open(SEED_FILE) as fh:
        vocab_lists = json.load(fh)

    for vocab_list in vocab_lists:
        dynamodb_table.put_item(Item=build_item(vocab_list))

    yield vocab_lists


@pytest.fixture
def idempotency_table(aws):
    """Create the idempotency table (IdempotencyKey/Consumer) and yield the resource.

    Schema mirrors ``IdempotencyTable`` in template.yaml.
    """
    client = boto3.client("dynamodb", region_name=REGION)
    client.create_table(
        TableName=IDEMPOTENCY_TABLE,
        AttributeDefinitions=[
            {"AttributeName": "IdempotencyKey", "AttributeType": "S"},
            {"AttributeName": "Consumer", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "IdempotencyKey", "KeyType": "HASH"},
            {"AttributeName": "Consumer", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    yield boto3.resource("dynamodb", region_name=REGION).Table(IDEMPOTENCY_TABLE)
