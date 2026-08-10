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


def test_get_all_users_reads_past_the_1mb_page_limit(dynamodb_table):
    """Every user must come back, not just the first page.

    DynamoDB caps a query response at 1MB. query_all_users reads a single GSI
    partition holding every user, so without a LastEvaluatedKey loop the daily
    email silently skips everyone past the cap.
    """
    # ~50KB of padding each, so 40 users comfortably exceeds one 1MB page.
    padding = "x" * 50_000
    user_count = 40
    for i in range(user_count):
        dynamodb_table.put_item(Item=_user_item(f"u{i:03d}", Padding=padding))

    users = user_service.get_all_users()

    assert len(users) == user_count


def test_unknown_item_types_do_not_corrupt_the_user(dynamodb_table):
    """Phase 6/7 item types land inside these queries' key ranges.

    They must fall through to the else branch rather than being matched by a
    substring test and routed into the wrong field.
    """
    dynamodb_table.put_item(Item=_user_item("abc"))
    # SK sorts between LIST# and USER#, so it is inside query_single_user's range.
    dynamodb_table.put_item(Item={
        "PK": "USER#abc",
        "SK": "PROGRESS",
        "Current streak": 4,
    })

    user = user_service.get_single_user("abc")

    assert user.email_address == "abc@test.com"
    assert user.subscriptions == []
    assert user.quizzes == []
    assert user.sentences == []


def test_user_record_missing_optional_attributes_still_loads(dynamodb_table):
    """Records written before an attribute existed must not raise."""
    dynamodb_table.put_item(Item={
        "PK": "USER#abc",
        "SK": "USER#abc",
        "GSI1PK": "USER",
        "GSI1SK": "USER#abc",
        "Email address": "abc@test.com",
    })

    user = user_service.get_single_user("abc")

    assert user.email_address == "abc@test.com"
    assert user.character_set_preference == "simplified"
    assert user.user_alias == "Not set"


def test_traditional_subscription_list_id_is_parsed(dynamodb_table):
    """The list id is split out of the key rather than sliced by suffix length."""
    dynamodb_table.put_item(Item=_user_item("abc"))
    dynamodb_table.put_item(Item={
        "PK": "USER#abc",
        "SK": "LIST#1ebcad40-bb9e-6ece-a366-acde48001122#TRADITIONAL",
        "List name": "HSK Level 5",
        "Status": "subscribed",
        "Character set": "traditional",
        "Date subscribed": "2021-01-02T00:00:00",
    })

    user = user_service.get_single_user("abc")

    assert len(user.subscriptions) == 1
    assert user.subscriptions[0].list_id == "1ebcad40-bb9e-6ece-a366-acde48001122"
    assert user.subscriptions[0].unique_list_id == "1ebcad40-bb9e-6ece-a366-acde48001122#TRADITIONAL"


def test_quizzes_and_sentences_are_dispatched_by_key_shape(dynamodb_table):
    dynamodb_table.put_item(Item=_user_item("abc"))
    dynamodb_table.put_item(Item={
        "PK": "USER#abc",
        "SK": "DATE#2021-11-04#SENTENCE#s1",
        "Sentence": "我喜欢学中文。",
        "Sentence id": "s1",
        "Date created": "2021-11-04",
        "List id": "123",
        "Character set": "simplified",
        "Word": {"Word id": "w1", "Simplified": "中文"},
    })

    user = user_service.get_single_user_with_activity("abc", date_range=3650)

    assert len(user.sentences) == 1
    assert user.sentences[0].sentence_id == "s1"
    # Missing word attributes fall back rather than raising.
    assert user.sentences[0].word.simplified == "中文"
    assert user.sentences[0].word.hsk_level == ""
