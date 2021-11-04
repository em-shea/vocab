# Get user data API

The get user data function is a GET method at api.haohaotiantian.com/user_data.
This endpoint returns user data (metadata and list of current subscriptions) for a user authenticated through Cognito.

Example output:
````
{
   "user_data":{
      "email_address":"me@email.com",
      "user_id":"12345",
      "character_set_preference":"traditional",
      "date_created":"2021-06-16T23:06:48.467526",
      "user_alias":"小王",
      "user_alias_pinyin":"xiao wang",
      "user_alias_emoji":"📙"
   },
   "lists":[
      {
         "list_name":"HSK Level 6",
         "list_id":"12345",
         "unique_list_id":"12345#TRADITIONAL"
         "character_set":"traditional",
         "status":"subscribed",
         "date_subscribed":"2021-06-16T23:06:48.646688"
      },
      {
         "list_name":"HSK Level 3",
         "list_id":"23456",
         "unique_list_id":"12345#SIMPLIFIED"
         "character_set":"simplified",
         "status":"subscribed",
         "date_subscribed":"2021-06-16T23:06:48.646688"
      }
   ]
}
````