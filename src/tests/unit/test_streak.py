"""The daily streak rules (streak_service)."""
from datetime import date

from streak_service import get_streak, BUFFER_MAX

TODAY = date(2026, 11, 24)


def quiz(day, n=1):
    return [{'SK': f'DATE#{day}#QUIZ#q{day}{i}'} for i in range(n)]


def sentence(filed, written):
    return {'SK': f'DATE#{filed}#SENTENCE#s{written}', 'Sentence': '我爱护环境。', 'Date written': f'{written}T10:00:00+00:00'}


def test_no_activity_is_no_streak():
    s = get_streak([], TODAY)
    assert (s['current'], s['best'], s['buffer'], s['today_done']) == (0, 0, 0, False)
    assert len(s['recent']) == 7 and s['recent'][-1] == {'date': '2026-11-24', 'actions': 0, 'status': 'open'}


def test_consecutive_days_count_and_today_still_open_keeps_it():
    items = quiz('2026-11-21') + quiz('2026-11-22') + quiz('2026-11-23')
    s = get_streak(items, TODAY)
    assert s['current'] == 3 and s['best'] == 3 and s['buffer'] == 0 and not s['today_done']


def test_a_missed_day_without_buffer_ends_it():
    items = quiz('2026-11-20') + quiz('2026-11-21') + quiz('2026-11-23') + quiz('2026-11-24')
    s = get_streak(items, TODAY)
    assert s['current'] == 2 and s['best'] == 2
    assert [d['status'] for d in s['recent'][-5:]] == ['done', 'done', 'missed', 'done', 'done']


def test_extra_actions_bank_buffer_that_covers_a_missed_day():
    items = quiz('2026-11-21', 3) + quiz('2026-11-23')  # 2 extra on the 21st, miss the 22nd
    s = get_streak(items, TODAY)
    assert s['current'] == 2  # the saved day keeps the streak but doesn't add to it
    assert s['buffer'] == 1
    assert [d['status'] for d in s['recent'][-4:]] == ['done', 'saved', 'done', 'open']


def test_buffer_is_capped():
    s = get_streak(quiz('2026-11-23', 10), TODAY)
    assert s['buffer'] == BUFFER_MAX


def test_sentence_counts_on_the_day_it_was_written_not_the_words_day():
    s = get_streak([sentence('2026-11-18', '2026-11-24')], TODAY)
    assert s['today_done'] and s['current'] == 1
    assert s['recent'][0]['status'] == 'missed'  # 2026-11-18 had nothing done


def test_other_items_and_empty_sentences_dont_count():
    items = [{'SK': 'DATE#2026-11-24#SENTENCE#x', 'Sentence': '  '}, {'SK': 'PUSH#abc'}, {'SK': 'DATE#2026-11-24#WRITING#L1#w1'}]
    s = get_streak(items, TODAY)
    assert s['recent'][-1]['actions'] == 1
