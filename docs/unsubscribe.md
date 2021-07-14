# Unsubscribe API

The unsubscribe function is a POST method at api.haohaotiantian.com/unsub.
Example payload to unsub from a given HSK level:
````
{
  "body": "{\"email\": \"me@testemail.com\", \"list\": \"1-simplified\"}"
}
{
  "body": "{\"email\": \"me@testemail.com\", \"list\": \"1-traditional\"}"
}
````
Example payload to unsub from all levels:
````
{
  "body": "{\"email\": \"me@testemail.com\", \"list\": \"all\"}"
}
````

