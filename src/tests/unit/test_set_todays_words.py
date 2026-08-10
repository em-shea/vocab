import unittest
from unittest import mock

import pytest

from set_todays_words.app import (
    lambda_handler, set_daily_words, get_lists_needing_a_daily_word,
)

TODAYS_WORDS = {"123": {"word_id": "WORD#1", "word": {"Simplified": "你"}}}

USER_LIST_ID = "user-list-1"


def _user_list_item(list_id=USER_LIST_ID, created_by="USER#abc"):
    return {
        "PK": "LIST#" + list_id,
        "SK": "METADATA",
        "List name": "My list",
        "List difficulty level": "Beginner",
        "Date created": "2026-01-01T00:00:00",
        "Created by": created_by,
        "Visibility": "private",
        "GSI1PK": "LIST",
        "GSI1SK": "LIST#" + list_id,
    }


def _subscription_item(list_id, uid="abc", status="subscribed"):
    return {
        "PK": f"USER#{uid}",
        "SK": f"LIST#{list_id}#SIMPLIFIED",
        "GSI1PK": "USER",
        "GSI1SK": f"USER#{uid}#LIST#{list_id}#SIMPLIFIED",
        "List name": "My list",
        "Status": status,
        "Character set": "simplified",
        "Date subscribed": "2026-01-01T00:00:00",
    }


class SetTodaysWordsTest(unittest.TestCase):

    @mock.patch('set_todays_words.app.send_event')
    @mock.patch('set_todays_words.app.store_words')
    @mock.patch('set_todays_words.app.set_daily_words', return_value=TODAYS_WORDS)
    def test_handler_stores_words_and_emits_event(self, set_words_mock, store_mock, event_mock):
        lambda_handler({}, "")

        self.assertEqual(set_words_mock.call_count, 1)
        store_mock.assert_called_once_with(TODAYS_WORDS)
        event_mock.assert_called_once_with(TODAYS_WORDS)


@mock.patch('list_word_service.get_words_in_list')
def test_set_daily_words_picks_one_word_per_list(get_words_mock, seeded_vocab_lists):
    get_words_mock.return_value = [
        {"list_id": "LIST#x", "word_id": "WORD#1", "word": {"Simplified": "你"}},
        {"list_id": "LIST#x", "word_id": "WORD#2", "word": {"Simplified": "好"}},
    ]

    todays_words = set_daily_words()

    # One entry per curated list.
    assert len(todays_words) == len(seeded_vocab_lists)
    for word in todays_words.values():
        assert word["word_id"] in ("WORD#1", "WORD#2")


@mock.patch('list_word_service.get_words_in_list', return_value=[])
def test_set_daily_words_handles_empty_list(get_words_mock, seeded_vocab_lists):
    # An empty word list must not raise; the list maps to None.
    todays_words = set_daily_words()

    assert len(todays_words) == len(seeded_vocab_lists)
    assert all(word is None for word in todays_words.values())


def test_curated_lists_always_get_a_word(seeded_vocab_lists, dynamodb_table):
    """No subscribers at all, but the public lists still need words for the home page."""
    lists = get_lists_needing_a_daily_word()

    assert len(lists) == len(seeded_vocab_lists)


def test_unsubscribed_user_list_is_skipped(seeded_vocab_lists, dynamodb_table):
    """The fan-out is bounded by demand, not by how many lists exist."""
    dynamodb_table.put_item(Item=_user_list_item())

    list_ids = {l['list_id'] for l in get_lists_needing_a_daily_word()}

    assert USER_LIST_ID not in list_ids
    assert len(list_ids) == len(seeded_vocab_lists)


def test_subscribed_user_list_gets_a_word(seeded_vocab_lists, dynamodb_table):
    dynamodb_table.put_item(Item=_user_list_item())
    dynamodb_table.put_item(Item=_subscription_item(USER_LIST_ID))

    list_ids = {l['list_id'] for l in get_lists_needing_a_daily_word()}

    assert USER_LIST_ID in list_ids


def test_user_list_with_only_lapsed_subscribers_is_skipped(seeded_vocab_lists, dynamodb_table):
    dynamodb_table.put_item(Item=_user_list_item())
    dynamodb_table.put_item(Item=_subscription_item(USER_LIST_ID, status="unsubscribed"))

    list_ids = {l['list_id'] for l in get_lists_needing_a_daily_word()}

    assert USER_LIST_ID not in list_ids


@mock.patch('user_service.get_subscribed_list_ids', side_effect=Exception("DynamoDB unavailable"))
def test_falls_back_to_all_lists_if_subscriptions_cannot_be_read(sub_mock, seeded_vocab_lists, dynamodb_table):
    """Better to set an unneeded word than to skip a list that has readers."""
    dynamodb_table.put_item(Item=_user_list_item())

    list_ids = {l['list_id'] for l in get_lists_needing_a_daily_word()}

    assert USER_LIST_ID in list_ids


if __name__ == '__main__':
    unittest.main()
