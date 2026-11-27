"""Build outgoing emails as raw MIME so we can set headers SES's simple API can't.

The headers below tell mail servers these are automated messages, so they don't
send out-of-office or vacation replies back to us:

- Auto-Submitted: auto-generated  (RFC 3834; honoured by most auto-responders)
- X-Auto-Response-Suppress: All   (Microsoft Exchange / Outlook)
- Precedence: bulk                (older convention; Gmail and others; bulk sends only)

Responders that ignore all three will still reply, so this cuts out-of-office
mail down rather than to zero.
"""
from email.message import EmailMessage
from email.policy import SMTP


def build_raw_email(sender, recipient, subject, html, bulk=False):
    message = EmailMessage(policy=SMTP)
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = subject
    message['Auto-Submitted'] = 'auto-generated'
    message['X-Auto-Response-Suppress'] = 'All'
    if bulk:
        message['Precedence'] = 'bulk'
    message.set_content(html, subtype='html', charset='utf-8')
    return message.as_bytes()


def send_html_email(ses_client, sender, recipient, subject, html, bulk=False,
                    configuration_set=None, campaign=None):
    """configuration_set turns on SES click tracking (see record_email_click);
    campaign is sent as the message's 'campaign' tag so clicks can be grouped."""
    kwargs = {}
    if configuration_set:
        kwargs['ConfigurationSetName'] = configuration_set
        if campaign:
            kwargs['Tags'] = [{'Name': 'campaign', 'Value': campaign}]
    return ses_client.send_raw_email(
        Source=sender,
        Destinations=[recipient],
        RawMessage={'Data': build_raw_email(sender, recipient, subject, html, bulk)},
        **kwargs,
    )
