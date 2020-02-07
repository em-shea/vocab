# Unsubscribe API

The unsubscribe function is a POST method at api.haohaotiantian.com/unsub.
Example payload to unsub from a given HSK level:
````
{
  "body": "{\"email\": \"me@testemail.com\", \"level\": \"1\"}"
}
{
  "body": "{\"email\": \"me@testemail.com\", \"level\": \"1-trd\"}"
}
````
Example payload to unsub from all levels:
````
{
  "body": "{\"email\": \"me@testemail.com\", \"level\": \"all\"}"
}
````

