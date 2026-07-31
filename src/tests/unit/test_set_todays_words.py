import unittest
from unittest import mock

from set_todays_words.app import lambda_handler, set_daily_words

TODAYS_WORDS = {"123": {"word_id": "WORD#1", "word": {"Simplified": "你"}}}


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
    def test_set_daily_words_picks_one_word_per_list(self, get_words_mock):
        get_words_mock.return_value = [
            {"list_id": "LIST#x", "word_id": "WORD#1", "word": {"Simplified": "你"}},
            {"list_id": "LIST#x", "word_id": "WORD#2", "word": {"Simplified": "好"}},
        ]

        todays_words = set_daily_words()

        # One entry per HSK list (six lists from vocab_list_service).
        self.assertEqual(len(todays_words), 6)
        for word in todays_words.values():
            self.assertIn(word["word_id"], ("WORD#1", "WORD#2"))

    @mock.patch('list_word_service.get_words_in_list', return_value=[])
    def test_set_daily_words_handles_empty_list(self, get_words_mock):
        # An empty word list must not raise; the list maps to None.
        todays_words = set_daily_words()

        self.assertEqual(len(todays_words), 6)
        self.assertTrue(all(word is None for word in todays_words.values()))


if __name__ == '__main__':
    unittest.main()
