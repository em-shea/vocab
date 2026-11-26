"""The redesigned daily email (email_v2.py) and its assembly in send_daily_email."""
import os
from datetime import date
from unittest import mock

import email_v2
from models import User, Subscription

SITE = 'https://staging.haohaotiantian.com'
LIST_ID = '1ebcad41-197a-6700-95a3-acde48001122'
TODAY = date(2026, 11, 26)


def _sub(char='simplified', name='HSK Level 3', status='subscribed'):
    return Subscription(list_name=name, unique_list_id=f'{LIST_ID}#{char.upper()}', list_id=LIST_ID,
                        character_set=char, status=status, date_subscribed='2026-01-01T00:00:00')


def _user(**kw):
    base = dict(email_address='a@example.com', user_id='u1', character_set_preference='simplified',
                user_alias='小陈', user_alias_pinyin='xiǎo chén', user_alias_emoji='Not set',
                subscriptions=[_sub()], quizzes=[], sentences=[])
    base.update(kw)
    return User(**base)


WORD = {'simplified': '爱护', 'traditional': '愛護', 'pinyin': 'ài hù', 'definition': 'to cherish; <to take care of>'}
STREAK = {'current': 12, 'best': 21, 'buffer': 2, 'recent': [
    {'date': f'2026-11-{d}', 'status': 'done' if d < 26 else 'open', 'actions': 1} for d in range(20, 27)]}


def test_tag_adds_campaign_and_keeps_query():
    assert email_v2.tag(SITE + '/quiz?list_id=x') == SITE + '/quiz?list_id=x&from=email&c=daily'
    assert email_v2.tag(SITE + '/', 'beta') == SITE + '/?from=email&c=beta'


def test_word_card_escapes_and_links():
    card = email_v2.word_card(SITE, _sub(), WORD, 'https://example.org/x')
    assert '爱护' in card and '&lt;to take care of&gt;' in card
    assert '/quiz?list_id=' in card and 'from=email' in card
    trad = email_v2.word_card(SITE, _sub('traditional'), WORD, 'https://example.org/x')
    assert '愛護' in trad and '繁' in trad


def test_full_email_with_everything():
    card = email_v2.word_card(SITE, _sub(), WORD, 'https://example.org/x')
    html = email_v2.build(SITE, TODAY, _user(), [card], SITE + '/unsub?x=1',
                          announcement={'title': 'Help shape the new Haohaotiantian', 'message': 'Lots more planned.',
                                        'button_text': 'Become a founding tester', 'button_url': '/founding-testers',
                                        'campaign': 'founding'},
                          streak=STREAK, rank=4, badges=['new_user', 'first_quiz', 'founding_tester', 'first_sentence'])
    assert 'Thursday, November 26' in html
    assert '/founding-testers?from=email&amp;c=founding' in html
    assert '12-day streak' in html and 'Best: 21 days · 2 buffer days' in html
    assert '4th this week' in html and '/leaderboard?from=email' in html
    # three rarest badges, rarest first
    assert html.index('badges/founding_tester') < html.index('badges/first_sentence') < html.index('badges/first_quiz')
    assert 'badges/new_user' not in html
    assert '小陈' in html and 'This app uses AI.' in html and '/unsub?x=1' in html


def test_no_streak_card_without_practice_and_join_prompt_without_rank():
    card = email_v2.word_card(SITE, _sub(), WORD, '#')
    plain = email_v2.build(SITE, TODAY, _user(), [card], '#')
    assert 'streak' not in plain and 'Your profile' in plain  # footer link only
    joined = email_v2.build(SITE, TODAY, _user(), [card], '#', streak=STREAK, rank=None, badges=['new_user'])
    assert 'Join the weekly leaderboard' in joined


def test_no_cards_no_email():
    assert email_v2.build(SITE, TODAY, _user(), [], '#') is None


def test_ordinals():
    assert [email_v2.ordinal(n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 22, 101)] == \
        ['1st', '2nd', '3rd', '4th', '11th', '12th', '13th', '21st', '22nd', '101st']


@mock.patch.dict(os.environ, {'URL': SITE})
def test_assemble_v2_reads_activity_and_rank(dynamodb_table):
    from send_daily_email import app
    dynamodb_table.put_item(Item={'PK': 'USER#u1', 'SK': 'DATE#2026-11-25#QUIZ#q1'})
    user = _user(public_profile=True, public_handle='abcd1234', founding_tester=True)
    with mock.patch.object(app, 'table', dynamodb_table):
        html = app.assemble_v2_content(user, {LIST_ID: [{'word': WORD}]}, None, {'abcd1234': 2})
    assert 'streak' in html and '2nd this week' in html and 'badges/founding_tester' in html
    with mock.patch.object(app, 'table', dynamodb_table):
        assert app.assemble_v2_content(_user(subscriptions=[_sub(status='unsubscribed')]), {}, None, {}) is None
