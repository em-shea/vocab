"""Screenshot the sample daily emails at desktop (600px) and phone (375px) widths.

    pip install playwright && playwright install chromium
    python scripts/render_email_previews.py [--site https://staging.haohaotiantian.com]

Writes email-previews/<sample>-desktop.png and -phone.png. This catches layout
breaks after code changes; it renders like a browser, not like Gmail or Outlook,
so check real inboxes with send_test_emails.py too. Reads and writes nothing in AWS.

Images load from <site>/email/. Before the images are deployed, serve them from the
frontend repo instead:
    (cd ../vocab-frontend-vue/v2/public && python -m http.server 8765) &
    python scripts/render_email_previews.py --site http://localhost:8765
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'layer', 'python'))

import email_samples  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', default='https://staging.haohaotiantian.com')
    parser.add_argument('--out', default='email-previews')
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width, label in ((600, 'desktop'), (375, 'phone')):
            page = browser.new_page(viewport={'width': width, 'height': 800}, device_scale_factor=2)
            for name, html in email_samples.samples(args.site).items():
                page.set_content(html, wait_until='networkidle')
                path = os.path.join(args.out, f'{name}-{label}.png')
                page.screenshot(path=path, full_page=True)
                print(path)
        browser.close()


if __name__ == '__main__':
    main()
