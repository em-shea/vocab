"""Sample daily emails for checking the design (email_v2.py) by eye.

Used by scripts/send_test_emails.py (sends them to your own inboxes),
scripts/render_email_previews.py (screenshots) and the unit tests.
Builds HTML only: no database reads, no sends.
"""
import json
from datetime import date

import email_v2
from models import User, Subscription

LIST_ID = '1ebcad41-197a-6700-95a3-acde48001122'
TODAY = date(2026, 11, 27)

WORDS = {
    'simplified': {'simplified': '爱护', 'traditional': '愛護', 'pinyin': 'ài hù', 'definition': 'to cherish; to take good care of'},
    'traditional': {'simplified': '龙', 'traditional': '龍', 'pinyin': 'lóng', 'definition': 'dragon'},
    'long': {'simplified': '一举两得', 'traditional': '一舉兩得', 'pinyin': 'yī jǔ liǎng dé',
             'definition': 'to kill two birds with one stone; one move, two gains; to achieve two things at once'},
}

ANNOUNCEMENT = {
    'title': 'A new look and new ways to study',
    'message': "Write your own sentences with each day's word, learn to write characters stroke by stroke, "
               "and build a daily streak. There's lots more on the way.",
    'button_text': 'Try it now',
    'button_url': '/profile',
    'campaign': 'test',
}


def _streak(current, best, buffer=0, today_done=False):
    recent = []
    for i, d in enumerate(range(21, 28)):
        # The current streak counts today only once today is done.
        done_before_today = current - 1 if today_done else current
        if d == 27:
            status = 'done' if today_done else 'open'
        elif i >= 6 - done_before_today:
            status = 'done'
        else:
            status = 'missed'
        recent.append({'date': f'2026-11-{d}', 'status': status, 'actions': 1})
    return {'current': current, 'best': best, 'buffer': buffer, 'recent': recent}


def _sub(char='simplified', name='HSK Level 3'):
    return Subscription(list_name=name, unique_list_id=f'{LIST_ID}#{char.upper()}', list_id=LIST_ID,
                        character_set=char, status='subscribed', date_subscribed='2026-01-01T00:00:00')


def _user(alias='小陈', subs=None):
    return User(email_address='sample@example.com', user_id='sample', character_set_preference='simplified',
                user_alias=alias, user_alias_pinyin='', user_alias_emoji='Not set',
                subscriptions=subs or [_sub()], quizzes=[], sentences=[])


def samples(site, announcement=ANNOUNCEMENT):
    """{name: html} for each case worth checking."""
    def card(sub, word):
        return email_v2.word_card(site, sub, word, 'https://example.org/examples')

    def build(user, cards, **kw):
        return email_v2.build(site, TODAY, user, cards, site + '/unsub?email=sample%40example.com',
                              announcement=announcement, **kw)

    return {
        'everything': build(_user(), [card(_sub(), WORDS['simplified'])],
                            streak=_streak(5, 21, buffer=2), rank=2,
                            badges=['new_user', 'first_quiz', 'founding_tester', 'first_sentence', 'first_stroke_order']),
        'new-subscriber': build(_user(alias='Not set'), [card(_sub(), WORDS['simplified'])]),
        'not-on-leaderboard': build(_user(alias='小黄'),
                                    [card(_sub(), WORDS['simplified'])],
                                    streak=_streak(1, 1), rank=None, badges=['new_user']),
        'two-lists-traditional': build(_user(subs=[_sub('traditional', 'HSK Level 1'), _sub('simplified', 'HSK Level 6')]),
                                       [card(_sub('traditional', 'HSK Level 1'), WORDS['traditional']),
                                        card(_sub('simplified', 'HSK Level 6'), WORDS['long'])],
                                       streak=_streak(7, 7, today_done=True), rank=11,
                                       badges=['new_user', 'first_quiz']),
        'no-announcement': email_v2.build(site, TODAY, _user(), [card(_sub(), WORDS['simplified'])],
                                          site + '/unsub', streak=_streak(3, 9), rank=1,
                                          badges=['new_user', 'first_quiz', 'first_sentence']),
    }


def load_announcement(path):
    with open(path) as f:
        return json.load(f)
