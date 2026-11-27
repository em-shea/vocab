"""Every sample email builds, and each shows the parts it is meant to show."""
import email_samples

SITE = 'https://staging.haohaotiantian.com'


def test_all_samples_build():
    emails = email_samples.samples(SITE)
    assert set(emails) == {'everything', 'new-subscriber', 'not-on-leaderboard', 'two-lists-traditional', 'no-announcement'}
    for name, html in emails.items():
        assert html and html.startswith('<!doctype html>'), name
        assert 'This app uses AI.' in html and 'ses:no-track' in html, name


def test_samples_cover_the_cases():
    e = email_samples.samples(SITE)
    assert 'A new look and new ways to study' in e['everything'] and '2nd this week' in e['everything']
    assert '-day streak' not in e['new-subscriber']
    assert 'Join the weekly leaderboard' in e['not-on-leaderboard']
    assert '龍' in e['two-lists-traditional'] and '一举两得' in e['two-lists-traditional']
    assert 'invite-print.jpg' not in e['no-announcement']
