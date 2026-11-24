"""How far a user has got through each of their lists (GET /progress).

Read-only: queries only, never writes, updates or deletes.

For each list the user is subscribed to (either character set):
- total: words in the list.
- seen: distinct words of the list sent since the user subscribed.
- proficient: seen words that meet PROFICIENT (below).

Proficient (Emily, 2026-11-23): the word has been asked in quizzes at least
MIN_QUIZ_ANSWERS times with at least MIN_ACCURACY of those answers right,
and the user has written at least one sentence with it and practised its
stroke order at least once.
"""
from datetime import datetime, timezone
from collections import defaultdict

from boto3.dynamodb.conditions import Key

import dynamodb_service

MIN_QUIZ_ANSWERS = 2
MIN_ACCURACY = 0.8

PROFICIENT = {
    "min_quiz_answers": MIN_QUIZ_ANSWERS,
    "min_quiz_accuracy": MIN_ACCURACY,
    "sentence": True,
    "stroke_order": True,
}


def word_id_of(entry):
    """The word id inside a saved quiz answer or sentence word, whatever its shape."""
    if not isinstance(entry, dict):
        return ''
    if isinstance(entry.get('word'), dict):
        return entry['word'].get('word_id') or entry['word'].get('Word id') or ''
    return entry.get('word_id') or entry.get('Word id') or ''


def tally(activity_items):
    """Per (list id, word id): quiz answers, right answers, sentences, stroke practice."""
    stats = defaultdict(lambda: {"asked": 0, "right": 0, "sentence": False, "stroke": False})
    for item in activity_items:
        sk = item.get('SK', '')
        if '#QUIZ#' in sk:
            list_id = item.get('List id', '')
            for question in item.get('Quiz data') or []:
                word_id = word_id_of(question.get('correct_answer'))
                if not word_id:
                    continue
                s = stats[(list_id, word_id)]
                s["asked"] += 1
                if question.get('was_answer_correct') is True:
                    s["right"] += 1
        elif '#SENTENCE#' in sk:
            word_id = word_id_of(item.get('Word'))
            if word_id and str(item.get('Sentence', '')).strip():
                stats[(item.get('List id', ''), word_id)]["sentence"] = True
        elif '#WRITING#' in sk:
            word_id = item.get('Word id', '')
            if word_id:
                stats[(item.get('List id', ''), word_id)]["stroke"] = True
    return stats


def is_proficient(s):
    return (
        s["asked"] >= MIN_QUIZ_ANSWERS
        and s["right"] / s["asked"] >= MIN_ACCURACY
        and s["sentence"]
        and s["stroke"]
    )


def list_progress(list_id, total, seen_word_ids, stats):
    proficient = sum(1 for word_id in seen_word_ids if is_proficient(stats.get((list_id, word_id), {"asked": 0, "right": 0, "sentence": False, "stroke": False})))
    return {"list_id": list_id, "total": total, "seen": len(seen_word_ids), "proficient": proficient}


# ---- queries --------------------------------------------------------------

def count_words(table, list_id):
    items = dynamodb_service.query_all_pages(
        table,
        KeyConditionExpression=Key('PK').eq('LIST#' + list_id) & Key('SK').begins_with('WORD#'),
        ProjectionExpression='SK',
    )
    return len(items)


def sent_word_ids(table, list_id, since):
    """Distinct ids of the list's words sent from `since` (YYYY-MM-DD, or '' for all) to today."""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    start = 'DATESENT#' + (since or '0000-00-00')
    items = dynamodb_service.query_all_pages(
        table,
        KeyConditionExpression=Key('PK').eq('LIST#' + list_id) & Key('SK').between(start, 'DATESENT#' + today + '~'),
        ProjectionExpression='#w',
        ExpressionAttributeNames={'#w': 'Word'},
    )
    return {item['Word'].get('Word id') for item in items if isinstance(item.get('Word'), dict) and item['Word'].get('Word id')}


def activity_items(table, cognito_id):
    """Every dated activity item of the user: quizzes, sentences, stroke practice."""
    return dynamodb_service.query_all_pages(
        table,
        KeyConditionExpression=Key('PK').eq('USER#' + cognito_id) & Key('SK').begins_with('DATE#'),
    )


def get_progress(table, cognito_id, subscriptions):
    """subscriptions: the user's Subscription records (any status)."""
    # One row per list; the earliest subscription date across its character sets.
    since = {}
    for sub in subscriptions:
        if getattr(sub, 'status', 'subscribed') != 'subscribed':
            continue
        date = (getattr(sub, 'date_subscribed', '') or '')[:10]
        if sub.list_id not in since or (date and (not since[sub.list_id] or date < since[sub.list_id])):
            since[sub.list_id] = date
    if not since:
        return []
    stats = tally(activity_items(table, cognito_id))
    return [
        list_progress(list_id, count_words(table, list_id), sent_word_ids(table, list_id, date), stats)
        for list_id, date in since.items()
    ]
