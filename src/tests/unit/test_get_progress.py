"""GET /progress: words seen and proficient per list, against a fake table."""
import json
from datetime import datetime, timezone, timedelta

import progress_service
from get_progress.app import lambda_handler

LIST = '1ebcad3f-5dfd-6bfe-bda4-acde48001122'   # HSK Level 1 (seeded)
USER = 'user-1'


def _event(sub=USER):
    return {'body': None, 'requestContext': {'authorizer': {'claims': {'sub': sub}}}}


def _day(n):
    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime('%Y-%m-%d')


def _seed(table, subscribed=None, words=4, sent=('W1', 'W2', 'W3')):
    table.put_item(Item={'PK': f'USER#{USER}', 'SK': f'USER#{USER}', 'Email address': 'a@b.com',
                         'GSI1PK': 'USER', 'GSI1SK': f'USER#{USER}', 'Date created': '2026-01-01T00:00:00',
                         'Character set preference': 'simplified',
                         'User alias': 'Not set', 'User alias pinyin': 'Not set', 'User alias emoji': 'Not set'})
    table.put_item(Item={'PK': f'USER#{USER}', 'SK': f'LIST#{LIST}#SIMPLIFIED', 'List name': 'HSK Level 1',
                         'Status': 'subscribed', 'Character set': 'simplified',
                         'Date subscribed': subscribed or (_day(20) + 'T00:00:00'),
                         'GSI1PK': 'USER', 'GSI1SK': f'USER#{USER}#LIST#{LIST}#SIMPLIFIED'})
    for i in range(1, words + 1):
        table.put_item(Item={'PK': f'LIST#{LIST}', 'SK': f'WORD#W{i}', 'Word': {'Word id': f'W{i}', 'Simplified': f'字{i}'}})
    for n, word_id in enumerate(sent):
        table.put_item(Item={'PK': f'LIST#{LIST}', 'SK': f'DATESENT#{_day(n + 1)}', 'Word': {'Word id': word_id}})


def _quiz(table, day, answers):
    table.put_item(Item={'PK': f'USER#{USER}', 'SK': f'DATE#{day}#QUIZ#q{day}{len(answers)}', 'List id': LIST,
                         'Quiz data': [{'correct_answer': {'list_id': LIST, 'word': {'word_id': w}}, 'was_answer_correct': ok}
                                       for w, ok in answers]})


def _proficient_extras(table, word_id, day):
    table.put_item(Item={'PK': f'USER#{USER}', 'SK': f'DATE#{day}#SENTENCE#s{word_id}', 'List id': LIST,
                         'Sentence': '我爱你。', 'Word': {'word_id': word_id}})
    table.put_item(Item={'PK': f'USER#{USER}', 'SK': f'DATE#{day}#WRITING#{LIST}#{word_id}', 'List id': LIST, 'Word id': word_id})


def _body(response):
    assert response['statusCode'] == 200, response
    return json.loads(response['body'])['data']


def test_counts_words_seen_since_subscribing(seeded_vocab_lists, dynamodb_table):
    _seed(dynamodb_table)
    rows = _body(lambda_handler(_event(), ''))['lists']
    assert rows == [{'list_id': LIST, 'total': 4, 'seen': 3, 'proficient': 0, 'list_name': 'HSK Level 1'}]


def test_words_sent_before_subscribing_are_not_seen(seeded_vocab_lists, dynamodb_table):
    _seed(dynamodb_table, subscribed=_day(2) + 'T08:00:00')
    assert _body(lambda_handler(_event(), ''))['lists'][0]['seen'] == 2  # sent 1 and 2 days ago, not 3


def test_proficient_needs_quiz_accuracy_a_sentence_and_stroke_practice(seeded_vocab_lists, dynamodb_table, monkeypatch):
    # Every word here is recent enough for the full rule.
    monkeypatch.setattr(progress_service, 'FULL_RULE_FROM', '0000-00-00')
    _seed(dynamodb_table)
    # W1: 2 of 2 right, sentence, strokes -> proficient
    # W2: 4 of 5 right (80%), sentence, strokes -> proficient
    # W3: 2 of 2 right, no stroke practice -> not
    _quiz(dynamodb_table, _day(1), [('W1', True), ('W2', True), ('W2', True), ('W3', True)])
    _quiz(dynamodb_table, _day(2), [('W1', True), ('W2', False), ('W2', True), ('W2', True), ('W3', True)])
    for w in ('W1', 'W2'):
        _proficient_extras(dynamodb_table, w, _day(1))
    dynamodb_table.put_item(Item={'PK': f'USER#{USER}', 'SK': f'DATE#{_day(1)}#SENTENCE#sW3', 'List id': LIST,
                                  'Sentence': '好。', 'Word': {'word_id': 'W3'}})
    body = _body(lambda_handler(_event(), ''))
    assert body['lists'][0]['proficient'] == 2
    assert body['proficient_rule'] == {'min_quiz_answers': 2, 'min_quiz_accuracy': 0.8, 'sentence': True,
                                       'stroke_order': True, 'quizzes_only_before': '2026-11-23'}


def test_one_right_answer_or_low_accuracy_is_not_enough():
    stats = progress_service.tally([
        {'SK': 'DATE#2026-11-01#QUIZ#a', 'List id': 'L', 'Quiz data': [
            {'correct_answer': {'word': {'word_id': 'A'}}, 'was_answer_correct': True},
            {'correct_answer': {'word': {'word_id': 'B'}}, 'was_answer_correct': True},
            {'correct_answer': {'word': {'word_id': 'B'}}, 'was_answer_correct': False},
            {'correct_answer': {'word_id': 'C'}, 'was_answer_correct': True},  # older flat shape
        ]},
        {'SK': 'DATE#2026-11-01#SENTENCE#x', 'List id': 'L', 'Sentence': '  ', 'Word': {'word_id': 'A'}},
        {'SK': 'DATE#2026-11-01#WRITING#L#A', 'List id': 'L', 'Word id': 'A'},
    ])
    assert stats[('L', 'A')] == {'asked': 1, 'right': 1, 'sentence': False, 'stroke': True}
    assert stats[('L', 'B')]['asked'] == 2 and stats[('L', 'B')]['right'] == 1
    assert stats[('L', 'C')]['asked'] == 1
    assert not progress_service.is_proficient(stats[('L', 'A')])


def test_no_subscriptions_means_no_rows(seeded_vocab_lists, dynamodb_table):
    _seed(dynamodb_table)
    dynamodb_table.update_item(Key={'PK': f'USER#{USER}', 'SK': f'LIST#{LIST}#SIMPLIFIED'},
                               UpdateExpression='SET #s = :u', ExpressionAttributeNames={'#s': 'Status'},
                               ExpressionAttributeValues={':u': 'unsubscribed'})
    assert _body(lambda_handler(_event(), ''))['lists'] == []


def test_words_last_sent_before_stroke_order_existed_count_on_quizzes_alone():
    quizzed = {'asked': 3, 'right': 3, 'sentence': False, 'stroke': False}
    assert progress_service.is_proficient(quizzed, '2026-10-01')
    assert not progress_service.is_proficient(quizzed, progress_service.FULL_RULE_FROM)
    assert not progress_service.is_proficient({'asked': 3, 'right': 2, 'sentence': False, 'stroke': False}, '2026-10-01')


def test_a_word_sent_again_later_needs_the_full_rule():
    stats = {('L', 'W'): {'asked': 2, 'right': 2, 'sentence': False, 'stroke': False}}
    assert progress_service.list_progress('L', 10, {'W': '2026-10-01'}, stats)['proficient'] == 1
    assert progress_service.list_progress('L', 10, {'W': '2099-01-01'}, stats)['proficient'] == 0


def test_progress_includes_the_streak(seeded_vocab_lists, dynamodb_table):
    body = _body(lambda_handler(_event(), ''))
    assert set(body['streak']) >= {'current', 'best', 'buffer', 'buffer_max', 'today_done', 'recent'}
