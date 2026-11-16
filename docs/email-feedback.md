# Bounces, complaints and out-of-office replies

## What used to happen

SES's default "email feedback forwarding" emailed every bounce and complaint to the
sending address (`vocab@` / `signin@haohaotiantian.com`). A typo'd sign-up bounced
the sign-in email, then bounced the daily email every day after. Out-of-office
auto-replies landed in the same inboxes.

## What happens now

- **Bounces and complaints** go to the `EmailFeedbackTopic` SNS topic, and the
  `HandleEmailFeedback` function unsubscribes the address from every list. Only
  permanent (hard) bounces count; soft bounces are ignored.
- **Out-of-office replies:** every email is sent with `Auto-Submitted: auto-generated`
  and `X-Auto-Response-Suppress: All`, and the daily email also with
  `Precedence: bulk`. Gmail, Outlook/Exchange and most other auto-responders skip
  mail carrying these. Some badly behaved responders will still reply.

## One-off setup (per AWS account, after deploying to prod)

The `haohaotiantian.com` SES identity is not managed by this stack, so point it at the
topic by hand. Staging and prod share the domain, so use the **prod** topic; the
handler skips addresses it can't find in its own user pool.

```bash
TOPIC=$(aws cloudformation describe-stacks --stack-name vocab --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='EmailFeedbackTopicArn'].OutputValue" --output text)

aws ses set-identity-notification-topic --region us-east-1 \
  --identity haohaotiantian.com --notification-type Bounce --sns-topic "$TOPIC"
aws ses set-identity-notification-topic --region us-east-1 \
  --identity haohaotiantian.com --notification-type Complaint --sns-topic "$TOPIC"

# Only allowed once both topics above are set.
aws ses set-identity-feedback-forwarding-enabled --region us-east-1 \
  --identity haohaotiantian.com --no-forwarding-enabled
```

If `vocab@` or `signin@` is also verified as its own SES identity, its settings
override the domain's: run the same three commands for that identity too
(`aws ses list-identities --region us-east-1` to check).

To test: subscribe `bounce@simulator.amazonses.com` on staging. The prod
`HandleEmailFeedback-prod` log should show "No user for bounce address…", and no
bounce email should arrive in the inbox.
