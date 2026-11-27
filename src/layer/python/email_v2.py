"""The redesigned daily email (Phase 5, design A "Cards", agreed 2026-11-26).

Canvas: https://claude.ai/artifact/YXK9wx2e9SJ9GjSaEN6E5p

Email clients ignore most modern CSS, so this is table-based HTML with inline
styles, web-safe fonts (Arial; the reader's system font for Chinese) and images
for anything drawn: the 好 mark, the avatar, badges and the woodblock prints.
Images are served by the site under /email/ (frontend v2/public/email/).

Read-only: builds HTML from data the caller passes in.
"""
import html
import urllib.parse
from datetime import date

INK = '#1B2140'
PAPER = '#FAF5EA'
RED = '#C93F1F'
BODY = '#3E4257'
MUTED = '#5F6276'
WHITE = '#FFFFFF'
SANS = "Arial, Helvetica, sans-serif"
HANZI = "'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans SC', sans-serif"
HANZI_TC = "'PingFang TC', 'Hiragino Sans CNS', 'Microsoft JhengHei', 'Noto Sans TC', sans-serif"

# Rarest first; the email shows up to three.
BADGE_RARITY = ['founding_tester', 'first_stroke_order', 'first_sentence', 'first_quiz', 'new_user']
BADGE_NAMES = {
    'founding_tester': 'Early Tester',
    'first_stroke_order': 'First stroke order',
    'first_sentence': 'First sentence',
    'first_quiz': 'First quiz',
    'new_user': 'New learner',
}


def esc(text):
    return html.escape(str(text or ''), quote=True)


def tag(url, campaign='daily'):
    """Add ?from=email&c=<campaign> to links on the site, so visits from the
    email can be counted. Links to other sites are left as they are."""
    parts = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    query += [('from', 'email'), ('c', campaign)]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


def ordinal(n):
    suffix = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f'{n}{suffix}'


def rarest_badges(badges, limit=3):
    return [b for b in BADGE_RARITY if b in (badges or [])][:limit]


def _button(href, text, bg=INK, fg=PAPER, border=None):
    border_css = f'border: 2px solid {border};' if border else ''
    return (f'<a href="{esc(href)}" style="display: inline-block; background: {bg}; color: {fg}; '
            f'{border_css} font-family: {SANS}; font-size: 14px; font-weight: bold; '
            f'text-decoration: none; padding: 10px 16px; margin: 3px 2px;">{esc(text)}</a>')


def header(site, today):
    day = today.strftime('%A, %B ') + str(today.day)
    return f'''
<tr><td style="background: {INK}; padding: 16px 24px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td style="vertical-align: middle;">
      <a href="{esc(tag(site + '/'))}" style="text-decoration: none;"><img src="{site}/email/logo.png" width="40" height="40" alt="好" style="display: inline-block; vertical-align: middle; border: 0;"></a>
      <span style="font-family: {SANS}; font-size: 18px; font-weight: bold; color: {PAPER}; vertical-align: middle; padding-left: 8px;">Haohaotiantian</span>
    </td>
    <td align="right" style="vertical-align: middle; font-family: {SANS}; font-size: 14px; color: #C9CBD6;">{esc(day)}</td>
  </tr></table>
</td></tr>'''


def announcement_card(site, announcement):
    """announcement: {'title', 'message', 'button_text', 'button_url', 'campaign'}
    from the day's S3 JSON. Only 'message' is required."""
    if not announcement or not announcement.get('message'):
        return ''
    campaign = announcement.get('campaign') or 'announcement'
    title = announcement.get('title')
    button = ''
    if announcement.get('button_text') and announcement.get('button_url'):
        url = announcement['button_url']
        if url.startswith('/'):
            url = tag(site + url, campaign)
        button = f'<p style="margin: 14px 0 0;">{_button(url, announcement["button_text"], bg=PAPER, fg=INK, border=INK)}</p>'
    title_html = (f'<p style="margin: 0 0 8px; font-family: {SANS}; font-size: 20px; font-weight: bold; color: {WHITE};">{esc(title)}</p>'
                  if title else '')
    return f'''
<tr><td style="padding: 24px 24px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse: separate;"><tr>
    <td background="{site}/email/invite-print.jpg" bgcolor="{RED}" style="background-color: {RED}; background-image: url('{site}/email/invite-print.jpg'); background-size: cover; background-position: center; border: 2px solid {INK}; box-shadow: 4px 4px 0 {INK}; padding: 22px 24px;">
      {title_html}
      <p style="margin: 0; font-family: {SANS}; font-size: 15px; line-height: 1.5; color: {WHITE};">{esc(announcement['message'])}</p>
      {button}
    </td>
  </tr></table>
</td></tr>'''


def _stamp(day):
    letter = date.fromisoformat(day['date']).strftime('%a')[0]
    status = day['status']
    if status == 'done':
        style = f'background: {PAPER}; color: {INK};'
    elif status == 'saved':
        style = f'border: 2px solid {PAPER}; color: {PAPER};'
    elif status == 'open':
        style = f'border: 2px dashed {PAPER}; color: {PAPER};'
    else:
        style = f'border: 2px solid #4A5070; color: #8A8FA6;'
    size = 30 if status == 'done' else 26
    return (f'<td style="padding-right: 5px;"><div style="width: {size}px; height: {size}px; line-height: {size}px; '
            f'text-align: center; font-family: {SANS}; font-size: 12px; font-weight: bold; {style}">{letter}</div></td>')


def streak_and_profile(site, user, streak, rank, badges):
    """Two cards side by side. Left out entirely for someone with no practice yet."""
    if not streak or not streak.get('best'):
        return ''
    current = streak['current']
    stamps = ''.join(_stamp(d) for d in streak['recent'])
    if rank:
        rank_line = (f'<span>{ordinal(rank)} this week</span>'
                     f'</td><td align="right" style="font-family: {SANS}; font-size: 14px;">'
                     f'<a href="{esc(tag(site + "/leaderboard"))}" style="color: {PAPER}; font-weight: bold;">Weekly leaderboard</a>')
    else:
        rank_line = (f'<a href="{esc(tag(site + "/profile-settings#public"))}" style="color: {PAPER}; font-weight: bold;">'
                     f'Join the weekly leaderboard</a>')
    best_line = f'Best: {streak["best"]} {"day" if streak["best"] == 1 else "days"}'
    if streak.get('buffer'):
        best_line += f' · {streak["buffer"]} buffer {"day" if streak["buffer"] == 1 else "days"}'

    name = user.user_alias if user.user_alias not in (None, '', 'Not set') else None
    avatar = f'<img src="{site}/email/avatar.png" width="40" height="40" alt="" style="display: inline-block; vertical-align: middle; border: 0;">'
    name_html = (f'<span style="font-family: {HANZI}; font-size: 20px; color: {INK}; vertical-align: middle; padding-left: 8px;">{esc(name)}</span>'
                 if name else '')
    badge_imgs = ''.join(
        f'<img src="{site}/email/badges/{b}.jpg" width="24" height="24" alt="{esc(BADGE_NAMES[b])}" title="{esc(BADGE_NAMES[b])}" '
        f'style="display: inline-block; border: 1px solid {INK}; margin: 0 2px;">'
        for b in rarest_badges(badges))
    badge_row = f'<p style="margin: 8px 0 0;">{badge_imgs}</p>' if badge_imgs else ''

    return f'''
<tr><td style="padding: 24px 24px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td class="col" style="background: {INK}; border: 2px solid {INK}; padding: 20px; vertical-align: top;">
      <p style="margin: 0 0 12px; font-family: {SANS}; font-size: 22px; font-weight: bold; color: {PAPER};">{current}-day streak</p>
      <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>{stamps}</tr></table>
      <p style="margin: 12px 0 0; font-family: {SANS}; font-size: 14px; color: #C9CBD6;">{esc(best_line)}</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 12px; border-top: 1px solid #4A5070;"><tr>
        <td style="padding-top: 10px; font-family: {SANS}; font-size: 14px; color: {PAPER};">{rank_line}</td>
      </tr></table>
    </td>
    <td class="gap" width="16" style="font-size: 0;">&nbsp;</td>
    <td class="col col-profile" width="150" align="center" style="background: {WHITE}; border: 2px solid {INK}; padding: 20px 12px; vertical-align: middle;">
      <p style="margin: 0;">{avatar}{name_html}</p>
      {badge_row}
      <p style="margin: 12px 0 0;">{_button(tag(site + '/profile'), 'Your profile')}</p>
    </td>
  </tr></table>
</td></tr>'''


def word_card(site, subscription, word, example_link):
    traditional = subscription.character_set != 'simplified'
    hanzi = word['traditional'] if traditional else word['simplified']
    set_mark = '繁' if traditional else '简'
    list_qs = f'list_id={urllib.parse.quote(subscription.list_id)}&char={subscription.character_set}'
    quiz = tag(f'{site}/quiz?{list_qs}&date_range=30&ques=10')
    buttons = ' '.join([
        _button(quiz, 'Take quiz'),
        _button(tag(site + '/sentences'), 'Write a sentence'),
        _button(tag(site + '/write'), 'Stroke order'),
    ])
    return f'''
<tr><td style="padding: 24px 24px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td align="center" style="background: {WHITE}; border: 2px solid {INK}; padding: 24px;">
      <p style="margin: 0; font-family: {SANS}; font-size: 12px; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; color: {MUTED};">{esc(subscription.list_name)} · {set_mark}</p>
      <p style="margin: 6px 0 0; font-family: {HANZI_TC if traditional else HANZI}; font-size: 56px; line-height: 1.2; color: {INK};">{esc(hanzi)}</p>
      <p style="margin: 4px 0 0; font-family: {SANS}; font-size: 20px; color: {RED};">{esc(word['pinyin'])}</p>
      <p style="margin: 4px 0 0; font-family: {SANS}; font-size: 16px; color: {BODY};">{esc(word['definition'])}</p>
      <p style="margin: 14px 0 0;">{buttons}</p>
      <p style="margin: 6px 0 0;"><a href="{esc(example_link)}" style="font-family: {SANS}; font-size: 13px; color: {RED};">Example sentences</a></p>
    </td>
  </tr></table>
</td></tr>'''


def footer(site, unsubscribe_link):
    return f'''
<tr><td style="padding: 28px 24px 0;">
  <img src="{site}/email/print-strip.jpg" width="548" alt="" style="display: block; width: 100%; max-width: 548px; height: auto; border: 2px solid {INK};">
</td></tr>
<tr><td align="center" style="padding: 20px 24px 32px; font-family: {SANS}; font-size: 13px; line-height: 1.6; color: {MUTED};">
  <p style="margin: 0 0 10px;">This app uses AI. Spot a mistake? Reply to this email or write to <a href="mailto:nihao@haohaotiantian.com" style="color: {RED};">nihao@haohaotiantian.com</a>.</p>
  <p style="margin: 0;">A Chinese vocabulary word a day from <a href="{esc(tag(site + '/'))}" style="color: {RED};">haohaotiantian.com</a></p>
  <p style="margin: 0;"><a href="{esc(tag(site + '/profile'))}" style="color: {RED};">Your profile</a> · <a href="{esc(tag(site + '/manage-lists'))}" style="color: {RED};">Manage your lists</a> · <a href="{esc(unsubscribe_link)}" style="color: {RED};">Unsubscribe</a></p>
</td></tr>'''


def build(site, today, user, word_cards, unsubscribe_link, announcement=None,
          streak=None, rank=None, badges=None):
    """The whole email. word_cards: the HTML of each word_card(), in order."""
    if not word_cards:
        return None
    body = ''.join([
        header(site, today),
        announcement_card(site, announcement),
        streak_and_profile(site, user, streak, rank, badges),
        ''.join(word_cards),
        footer(site, unsubscribe_link),
    ])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Today's word</title>
<style>
@media (max-width: 520px) {{
  .col {{ display: block !important; width: auto !important; }}
  .gap {{ display: none !important; }}
  .col-profile {{ margin-top: 16px !important; }}
}}
</style></head>
<body style="margin: 0; padding: 0; background: {PAPER};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background: {PAPER};"><tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width: 100%; max-width: 600px; background: {PAPER};">
{body}
</table>
</td></tr></table>
</body></html>'''
