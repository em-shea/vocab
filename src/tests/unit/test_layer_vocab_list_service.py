"""Tests for vocab_list_service against a moto-mocked DynamoDB table.

Vocab lists moved out of a hardcoded Python list into LIST#<id> / METADATA items.
Visibility governs who may read a list, and two of the endpoints that read lists
(GET /review, GET /sample_vocab) have no authorizer at all - so the filtering here
is the only thing standing between a private list and an anonymous caller.
"""
import vocab_list_service


def _list_item(list_id, name="A list", created_by="admin", visibility="public", **overrides):
    item = {
        "PK": "LIST#" + list_id,
        "SK": "METADATA",
        "List name": name,
        "List difficulty level": "Beginner",
        "Date created": "2026-01-01T00:00:00",
        "Created by": created_by,
        "Visibility": visibility,
        "GSI1PK": "LIST",
        "GSI1SK": "LIST#" + list_id,
    }
    item.update(overrides)
    return item


def test_seeded_lists_keep_their_original_ids(seeded_vocab_lists):
    """Every existing subscription references these UUIDs - they must not change."""
    lists = vocab_list_service.get_vocab_lists()

    assert len(lists) == 6
    by_name = {l['list_name']: l for l in lists}
    assert by_name['HSK Level 1']['list_id'] == '1ebcad3f-5dfd-6bfe-bda4-acde48001122'
    assert by_name['HSK Level 6']['list_id'] == '1ebcad41-197a-6700-95a3-acde48001122'
    assert by_name['HSK Level 3']['list_difficulty_level'] == 'Intermediate'
    assert all(l['visibility'] == 'public' for l in lists)
    assert all(l['created_by'] == 'admin' for l in lists)


def test_get_public_vocab_lists_excludes_private(dynamodb_table):
    dynamodb_table.put_item(Item=_list_item("pub"))
    dynamodb_table.put_item(Item=_list_item("priv", created_by="USER#abc", visibility="private"))

    public = vocab_list_service.get_public_vocab_lists()

    assert [l['list_id'] for l in public] == ["pub"]


def test_get_vocab_lists_for_user_includes_own_private_lists(dynamodb_table):
    dynamodb_table.put_item(Item=_list_item("pub"))
    dynamodb_table.put_item(Item=_list_item("mine", created_by="USER#abc", visibility="private"))
    dynamodb_table.put_item(Item=_list_item("theirs", created_by="USER#xyz", visibility="private"))

    visible = vocab_list_service.get_vocab_lists_for_user("abc")

    assert {l['list_id'] for l in visible} == {"pub", "mine"}


def test_missing_visibility_defaults_to_public(dynamodb_table):
    """Lists seeded before the field existed are the original admin HSK lists."""
    item = _list_item("legacy")
    del item['Visibility']
    del item['Created by']
    dynamodb_table.put_item(Item=item)

    vocab_list = vocab_list_service.get_vocab_list("legacy")

    assert vocab_list['visibility'] == 'public'
    assert vocab_list['created_by'] == 'admin'


def test_get_vocab_list_returns_none_when_missing(dynamodb_table):
    assert vocab_list_service.get_vocab_list("does-not-exist") is None


class TestIsListReadableBy:

    def test_public_list_is_readable_anonymously(self, dynamodb_table):
        dynamodb_table.put_item(Item=_list_item("pub"))
        vocab_list = vocab_list_service.get_vocab_list("pub")

        assert vocab_list_service.is_list_readable_by(vocab_list) is True
        assert vocab_list_service.is_list_readable_by(vocab_list, "anyone") is True

    def test_private_list_is_not_readable_anonymously(self, dynamodb_table):
        dynamodb_table.put_item(Item=_list_item("priv", created_by="USER#abc", visibility="private"))
        vocab_list = vocab_list_service.get_vocab_list("priv")

        assert vocab_list_service.is_list_readable_by(vocab_list) is False

    def test_private_list_is_readable_by_its_owner(self, dynamodb_table):
        dynamodb_table.put_item(Item=_list_item("priv", created_by="USER#abc", visibility="private"))
        vocab_list = vocab_list_service.get_vocab_list("priv")

        assert vocab_list_service.is_list_readable_by(vocab_list, "abc") is True

    def test_private_list_is_not_readable_by_another_user(self, dynamodb_table):
        dynamodb_table.put_item(Item=_list_item("priv", created_by="USER#abc", visibility="private"))
        vocab_list = vocab_list_service.get_vocab_list("priv")

        assert vocab_list_service.is_list_readable_by(vocab_list, "xyz") is False

    def test_missing_list_is_not_readable(self):
        assert vocab_list_service.is_list_readable_by(None, "abc") is False
