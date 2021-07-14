# Set subscriptions API

The get user data function is a POST method at api.haohaotiantian.com/set_subs.
This endpoint creates a user profile (if one doesn't exist) and creates or updates user subscriptions for a user authenticated through Cognito.

Example payload:
````
# new or returning user payload:
{
    "cognito_id":"123",
    "email":"me@testemail.com",
    "char_set_preference":"simplified",
    "set_lists": [
        {
            "list_id":"123",
            "list_name":"HSK Level 1",
            "char_set":"simplified"
        },
        {
            "list_id":"234",
            "list_name":"HSK Level 2",
            "char_set":"simplified"
        }
    ]
}
# unsubscribe all lists
{
    "cognito_id":"123",
    "email":"me@testemail.com",
    "char_set_preference":"simplified",
    "set_lists": []
}
````