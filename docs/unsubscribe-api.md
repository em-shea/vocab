# Unsubscribe API

The unsubscribe function is a POST method at api.haohaotiantian.com/unsub.
Example payload to unsub from a given HSK level:
````
{
  "body": "{\"email\": \"me@testemail.com\", \"level\": \"1\"}"
}
````
Example payload to unsub from all levels:
````
{
  "body": "{\"email\": \"me@testemail.com\", \"level\": \"all\"}"
}
````

Example query string parameters:

````
https://api.haohaotiantian.com/unsub?email=me@testemail.com&level=1

https://api.haohaotiantian.com/unsub?email=me@testemail.com&level=all
````


