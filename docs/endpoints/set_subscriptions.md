# Set subscriptions API

The set subscriptions function is a POST method at api.haohaotiantian.com/set_subs.
This endpoint creates a user profile (if one doesn't exist) and creates or updates user subscriptions for a user authenticated through Cognito.

Example payload:
````
# new or returning user payload:
{
    "cognito_id":"123",
    "email":"me@testemail.com",
    "character_set_preference":"simplified",
    "lists": [
        {
            "list_id":"123",
            "list_name":"HSK Level 1",
            "character_set":"simplified"
        },
        {
            "list_id":"234",
            "list_name":"HSK Level 2",
            "character_set":"simplified"
        }
    ]
}

# unsubscribe all lists (logged in user)
{
    "cognito_id":"123",
    "email":"me@testemail.com",
    "character_set_preference":"simplified",
    "lists": []
}
````