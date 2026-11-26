"""Opt-in public profiles, badges and the weekly leaderboard (Emily, 2026-11-25).

Nothing is public unless the user switches it on in profile settings.

Items written (new, nothing existing is replaced or deleted):
- On the user item (PK = SK = USER#<sub>): 'Public profile' (bool) and
  'Public handle' (random, set once and kept).
- A pointer item PK = SK = PUBLIC#<handle> with 'Cognito id' and 'Public profile',
  and GSI1PK = 'PUBLIC' so the leaderboard can list every public profile through
  the existing GSI1 index. Turning the profile off sets 'Public profile' false
  on both; the items stay.

What a public page shows: profile name (the chosen name, never the email), the
month they joined, streak, badges and this week's activity. Badges are worked
out on read from activity, so there is nothing else to store.
"""
import secrets
from datetime import datetime, timedelta, timezone

from boto3.dynamodb.conditions import Key

import dynamodb_service
import progress_service
import streak_service

HANDLE_ALPHABET = 'abcdefghjkmnpqrstuvwxyz23456789'  # no 0/o, 1/l/i
HANDLE_LENGTH = 8
LEADERBOARD_SIZE = 50

# Order is the order shown on the page (Emily, 2026-11-25: four badges).
BADGES = [
    'new_user',
    'first_quiz',
    'first_sentence',
    'first_stroke_order',
]


def new_handle():
    return ''.join(secrets.choice(HANDLE_ALPHABET) for _ in range(HANDLE_LENGTH))


def _user_item(table, cognito_id):
    key = 'USER#' + cognito_id
    return table.get_item(Key={'PK': key, 'SK': key}).get('Item')


def _pointer_key(handle):
    return {'PK': 'PUBLIC#' + handle, 'SK': 'PUBLIC#' + handle}


def set_public(table, cognito_id, public):
    """Switch the user's public profile on or off. Returns {'public', 'handle'}."""
    user = _user_item(table, cognito_id)
    if not user:
        raise LookupError(cognito_id)

    handle = user.get('Public handle')
    for _ in range(5):
        candidate = handle or new_handle()
        try:
            # Claim (or update our own) pointer; never take over someone else's handle.
            table.update_item(
                Key=_pointer_key(candidate),
                UpdateExpression='SET #c = :c, #p = :p, GSI1PK = :g, GSI1SK = :gs',
                ConditionExpression='attribute_not_exists(PK) OR #c = :c',
                ExpressionAttributeNames={'#c': 'Cognito id', '#p': 'Public profile'},
                ExpressionAttributeValues={':c': cognito_id, ':p': bool(public),
                                           ':g': 'PUBLIC', ':gs': 'PUBLIC#' + candidate},
            )
            handle = candidate
            break
        except table.meta.client.exceptions.ConditionalCheckFailedException:
            if handle:  # our stored handle belongs to someone else: should never happen
                raise
    else:
        raise RuntimeError('Could not find a free handle')

    table.update_item(
        Key={'PK': 'USER#' + cognito_id, 'SK': 'USER#' + cognito_id},
        UpdateExpression='SET #p = :p, #h = if_not_exists(#h, :h)',
        ConditionExpression='attribute_exists(PK)',
        ExpressionAttributeNames={'#p': 'Public profile', '#h': 'Public handle'},
        ExpressionAttributeValues={':p': bool(public), ':h': handle},
    )
    return {'public': bool(public), 'handle': handle}


def badges(user_item, items, best_streak):
    kinds = set()
    for item in items:
        sk = item.get('SK', '')
        if '#QUIZ#' in sk:
            kinds.add('quiz')
        elif '#SENTENCE#' in sk and str(item.get('Sentence', '')).strip():
            kinds.add('sentence')
        elif '#WRITING#' in sk:
            kinds.add('writing')
    earned = {
        'new_user': True,
        'first_quiz': 'quiz' in kinds,
        'first_sentence': 'sentence' in kinds,
        'first_stroke_order': 'writing' in kinds,
    }
    return [b for b in BADGES if earned[b]]


def week_start(today):
    """Monday of today's week (UTC)."""
    return today - timedelta(days=today.weekday())


def week_activity(items, today, start=None):
    """Active days and activities from start (default: this Monday) to today."""
    start = (start or week_start(today)).isoformat()
    end = today.isoformat()
    counts = streak_service.actions_per_day(items)
    days = {d: n for d, n in counts.items() if start <= d <= end}
    return {'active_days': len(days), 'actions': sum(days.values())}


def _name(user_item):
    alias = user_item.get('User alias', 'Not set')
    pinyin = user_item.get('User alias pinyin', 'Not set')
    return (None if alias in ('', 'Not set') else alias,
            None if pinyin in ('', 'Not set') else pinyin)


def summary(table, handle, cognito_id, today):
    user = _user_item(table, cognito_id)
    if not user or not user.get('Public profile'):
        return None
    items = progress_service.activity_items(table, cognito_id)
    streak = streak_service.get_streak(items, today)
    name, pinyin = _name(user)
    return {
        'handle': handle,
        'name': name,
        'name_pinyin': pinyin,
        'joined': str(user.get('Date created') or '')[:7] or None,
        'streak': {'current': streak['current'], 'best': streak['best']},
        'badges': badges(user, items, streak['best']),
        'week': week_activity(items, today),
        # Monday to Sunday before this week; used for last week's top 3.
        '_last_week': week_activity(items, week_start(today) - timedelta(days=1),
                                    week_start(today) - timedelta(days=7)),
    }


def get_public_profile(table, handle, today=None):
    """The public view of one profile, or None if it doesn't exist or isn't public."""
    today = today or datetime.now(timezone.utc).date()
    if not handle or len(handle) > 32:
        return None
    pointer = table.get_item(Key=_pointer_key(handle)).get('Item')
    if not pointer or not pointer.get('Public profile'):
        return None
    profile = summary(table, handle, pointer['Cognito id'], today)
    if profile:
        profile.pop('_last_week', None)
    return profile


def _rank(rows, week_key):
    rows = [r for r in rows if r[week_key]['active_days'] > 0] if week_key == '_last_week' else list(rows)
    rows.sort(key=lambda r: (-r[week_key]['active_days'], -r[week_key]['actions'],
                             -r['streak']['current'], r['handle']))
    return rows


def get_leaderboard(table, today=None):
    """Every public profile ranked for this week (Monday to today, UTC): active
    days, then activities, then current streak. Also last week's top 3
    (Monday to Sunday before), for showing on Mondays. Read-only."""
    today = today or datetime.now(timezone.utc).date()
    pointers = dynamodb_service.query_all_pages(
        table, IndexName='GSI1', KeyConditionExpression=Key('GSI1PK').eq('PUBLIC'),
    )
    rows = []
    for p in pointers:
        if not p.get('Public profile'):
            continue
        handle = p.get('GSI1SK', '')[len('PUBLIC#'):]
        row = summary(table, handle, p['Cognito id'], today)
        if row:
            rows.append(row)

    last_week = []
    for i, row in enumerate(_rank(rows, '_last_week')[:3], 1):
        entry = {k: v for k, v in row.items() if k not in ('week', '_last_week')}
        last_week.append({**entry, 'week': row['_last_week'], 'rank': i})

    ranked = _rank(rows, 'week')[:LEADERBOARD_SIZE]
    entries = []
    for i, row in enumerate(ranked, 1):
        row = {k: v for k, v in row.items() if k != '_last_week'}
        row['rank'] = i
        entries.append(row)
    start = week_start(today)
    return {'week_start': start.isoformat(), 'today': today.isoformat(),
            'last_week_start': (start - timedelta(days=7)).isoformat(),
            'entries': entries, 'last_week': last_week}
