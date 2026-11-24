"""Daily streak, worked out from the user's dated activity items (read-only).

Basic rules before heroes launch (Emily, 2026-11-24):
- A day counts when the user does at least one thing: saves a quiz, writes a
  sentence or practices stroke order. Days are UTC dates, the same "today" the
  rest of the backend uses.
- Each extra thing done on a day, beyond the first, banks one buffer day, up
  to BUFFER_MAX.
- A missed day spends one buffer day and the streak carries on (the missed day
  doesn't add to it). A missed day with no buffer ends the streak.
- Today with nothing done yet is still open, so it doesn't break the streak.
"""
from collections import Counter
from datetime import date, datetime, timedelta, timezone

BUFFER_MAX = 3
RECENT_DAYS = 7
MARKERS = ('#QUIZ#', '#SENTENCE#', '#WRITING#')


def action_day(item):
    """The UTC day the user did it. Sentences can be filed under an earlier
    word's date, so 'Date written' wins when it is there."""
    written = str(item.get('Date written') or '')[:10]
    if len(written) == 10:
        return written
    parts = item.get('SK', '').split('#')
    return parts[1][:10] if len(parts) > 1 else ''


def actions_per_day(items):
    counts = Counter()
    for item in items:
        sk = item.get('SK', '')
        if not any(m in sk for m in MARKERS):
            continue
        if '#SENTENCE#' in sk and not str(item.get('Sentence', '')).strip():
            continue
        day = action_day(item)
        if day:
            counts[day] += 1
    return counts


def get_streak(items, today=None):
    today = today or datetime.now(timezone.utc).date()
    counts = actions_per_day(items)
    days = sorted(d for d in counts if d <= today.isoformat())

    status = {}
    current = best = buffer = 0
    if days:
        day = date.fromisoformat(days[0])
        while day <= today:
            key = day.isoformat()
            n = counts.get(key, 0)
            if n:
                current += 1
                buffer = min(BUFFER_MAX, buffer + n - 1)
                status[key] = 'done'
            elif day == today:
                status[key] = 'open'
            elif current and buffer:
                buffer -= 1
                status[key] = 'saved'
            else:
                current = buffer = 0
                status[key] = 'missed'
            best = max(best, current)
            day += timedelta(days=1)

    recent = []
    for back in range(RECENT_DAYS - 1, -1, -1):
        key = (today - timedelta(days=back)).isoformat()
        recent.append({
            'date': key,
            'actions': counts.get(key, 0),
            'status': status.get(key, 'open' if back == 0 else 'missed'),
        })

    return {
        'current': current,
        'best': best,
        'buffer': buffer,
        'buffer_max': BUFFER_MAX,
        'today': today.isoformat(),
        'today_done': counts.get(today.isoformat(), 0) > 0,
        'recent': recent,
    }
