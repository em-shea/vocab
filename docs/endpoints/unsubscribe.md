# POST /unsub
#
# Public - no Cognito authorizer, so the email in the body is unverified.
#
# Responses:
#   200 {"success": true}   the address was unsubscribed, OR no user exists for it.
#                           The two are deliberately indistinguishable: a different
#                           reply would let anyone test whether an email is a
#                           subscriber. An unknown address is normal traffic on a
#                           public form, so it is not logged as an error either.
#   502 {"success": false}  something actually failed (Cognito or DynamoDB).

# unsubscribe by email only - cognito_id and list default to empty, meaning
# "look the user up and unsubscribe them from everything". This is what the bounce
# handler in receive-ses-email posts when a delivery failure names a dead address.
{
    "email":"person@email.com"
}

# unsubscribe all lists (anonymous user)
{
    "cognito_id":"",
    "email":"me@testemail.com",
    "character_set_preference":"simplified",
    "list": ""
}

# unsubscribe a single list (anonymous user)
{
    "cognito_id":"",
    "email":"me@testemail.com",
    "character_set_preference":"simplified",
    "list": {
            "list_id":"123",
            "list_name":"HSK Level 1",
            "character_set":"simplified"
        }
}