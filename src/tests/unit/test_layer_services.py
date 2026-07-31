"""Unit tests for the shared Lambda-layer services (pure formatting/logic)."""
import json
import uuid

import api_response
import ksuid_service
import list_word_service
import quiz_results_service
import review_word_service


# --- api_response.response ---------------------------------------------------
def test_api_response_success():
    result = api_response.response(200, "ok", {"x": 1})
    body = json.loads(result["body"])

    assert result["statusCode"] == 200
    assert body["success"] is True
    assert body["message"] == "ok"
    assert body["data"] == {"x": 1}


def test_api_response_failure_defaults_data_to_none():
    result = api_response.response(502, "boom")
    body = json.loads(result["body"])

    assert result["statusCode"] == 502
    assert body["success"] is False
    assert body["data"] is None


# --- review_word_service -----------------------------------------------------
WORD_ITEM = {
    "Word id": "WORD#1",
    "Simplified": "你好",
    "Traditional": "你好",
    "Pinyin": "nǐ hǎo",
    "Definition": "hello",
    "Audio file key": "audio/key.mp3",
    "Difficulty level": "Beginner",
    "HSK Level": "1",
}


def test_format_word_body_maps_dynamo_keys_to_word():
    word = review_word_service.format_word_body(WORD_ITEM)

    assert word.word_id == "WORD#1"
    assert word.simplified == "你好"
    assert word.pinyin == "nǐ hǎo"
    assert word.definition == "hello"
    assert word.hsk_level == "1"


def test_format_review_word_splits_pk_and_sk():
    review_word = review_word_service.format_review_word({
        "PK": "LIST#abc",
        "SK": "DATESENT#2021-01-02",
        "Word": WORD_ITEM,
    })

    assert review_word.list_id == "abc"
    assert review_word.date_sent == "2021-01-02"
    assert review_word.word.simplified == "你好"


# --- quiz_results_service ----------------------------------------------------
def test_format_quiz_results_casts_counts_to_int():
    quiz = quiz_results_service.format_quiz_results({
        "SK": "QUIZ#q1",
        "Date created": "2021-01-02",
        "List id": "123",
        "Character set": "simplified",
        "Question quantity": "10",
        "Correct answers": "8",
        "Quiz data": [{"q": 1}],
    })

    assert quiz.quiz_id == "q1"
    assert quiz.list_id == "123"
    assert quiz.question_quantity == 10
    assert quiz.correct_answers == 8
    assert isinstance(quiz.question_quantity, int)


# --- list_word_service -------------------------------------------------------
def test_format_word_list_reshapes_items():
    word_list = list_word_service.format_word_list({
        "Items": [
            {"PK": "LIST#abc", "SK": "WORD#1", "Word": WORD_ITEM},
            {"PK": "LIST#abc", "SK": "WORD#2", "Word": WORD_ITEM},
        ]
    })

    assert len(word_list) == 2
    assert word_list[0] == {"list_id": "LIST#abc", "word_id": "WORD#1", "word": WORD_ITEM}


# --- ksuid_service -----------------------------------------------------------
def test_generate_ksuid_returns_unique_uuids():
    first = ksuid_service.generate_ksuid()
    second = ksuid_service.generate_ksuid()

    assert isinstance(first, uuid.UUID)
    assert first != second
    assert len(str(first)) == 36
