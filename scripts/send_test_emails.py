"""Send the sample daily emails to your own inboxes, to check them in real clients.

    python scripts/send_test_emails.py you@gmail.com you@outlook.com            # dry run
    python scripts/send_test_emails.py you@gmail.com you@outlook.com --send

Options:
    --only everything,new-subscriber   send just these samples
    --announcement path/to/file.json   use this announcement instead of the built-in one
    --site https://...                 where images and links point (default staging)

Dry run writes each sample to email-samples/<name>.html and sends nothing.
--send sends one email per sample to each address you list, through SES from
vocab@haohaotiantian.com, with no configuration set (so no click tracking) and
subject "[Test] <sample>". It reads and writes nothing in DynamoDB.

Images load from <site>/email/, so the frontend email images must be deployed there.
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'layer', 'python'))

import email_samples  # noqa: E402

SENDER = 'Haohaotiantian <vocab@haohaotiantian.com>'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('addresses', nargs='+')
    parser.add_argument('--send', action='store_true')
    parser.add_argument('--only')
    parser.add_argument('--announcement')
    parser.add_argument('--site', default='https://staging.haohaotiantian.com')
    args = parser.parse_args()

    announcement = (email_samples.load_announcement(args.announcement)
                    if args.announcement else email_samples.ANNOUNCEMENT)
    emails = email_samples.samples(args.site, announcement)
    if args.only:
        wanted = args.only.split(',')
        emails = {k: v for k, v in emails.items() if k in wanted}

    os.makedirs('email-samples', exist_ok=True)
    for name, html in emails.items():
        with open(f'email-samples/{name}.html', 'w') as f:
            f.write(html)
    print(f'Wrote {len(emails)} samples to email-samples/')

    if not args.send:
        print(f'Dry run: would send {len(emails)} emails to each of {", ".join(args.addresses)}. Add --send to send.')
        return

    import boto3
    from email_message import send_html_email
    ses = boto3.client('ses', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    for address in args.addresses:
        for name, html in emails.items():
            send_html_email(ses, SENDER, address, f'[Test] {name}', html)
            print(f'Sent {name} to {address}')


if __name__ == '__main__':
    main()
