"""Integration tests for user_service against a moto-mocked DynamoDB table.

Unlike the other tests, these do not patch the service functions — they write real
items into the in-memory table (via the ``dynamodb_table`` fixture in conftest.py)
and read them back through the actual boto3 query code paths.
"""
import user_service


def _user_item(uid, **overrides):
    item = {
        "PK": f"USER#{uid}",
        "SK": f"USER#{uid}",
        "GSI1PK": "USER",
        "GSI1SK": f"USER#{uid}",
        "Email address": f"{uid}@test.com",
        "Character set preference": "simplified",
        "Date created": "2021-01-01T00:00:00",
        "User alias": "Not set",
        "User alias pinyin": "Not set",
        "User alias emoji": "Not set",
    }
    item.update(overrides)
    return item


def test_get_single_user_reads_metadata_and_subscribed_lists(dynamodb_table):
    dynamodb_table.put_item(Item=_user_item("abc"))
    dynamodb_table.put_item(Item={
        "PK": "USER#abc",
        "SK": "LIST#123#SIMPLIFIED",
        "GSI1PK": "USER",
        "GSI1SK": "USER#abc#LIST#123#SIMPLIFIED",
        "List name": "HSK Level 1",
        "Status": "subscribed",
        "Character set": "simplified",
        "Date subscribed": "2021-01-02T00:00:00",
    })

    user = user_service.get_single_user("abc")

    assert user.email_address == "abc@test.com"
    assert user.character_set_preference == "simplified"
    assert len(user.subscriptions) == 1
    assert user.subscriptions[0].list_name == "HSK Level 1"
    assert user.subscriptions[0].list_id == "123"


def test_get_all_users_queries_the_gsi(dynamodb_table):
    dynamodb_table.put_item(Item=_user_item("u1"))
    dynamodb_table.put_item(Item=_user_item("u2"))

    users = user_service.get_all_users()

    assert len(users) == 2
    assert {u.email_address for u in users} == {"u1@test.com", "u2@test.com"}
