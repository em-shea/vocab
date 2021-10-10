# Get list words API

The get list words function is a GET method at api.haohaotiantian.com/words.
This endpoint accepts a list id and returns list metadata and all the words that are part of the list.

Example payload:
````
{
  "body": "{\"list_id\": \"1234\"}"
}
````

Example output:
````
{
   "list_data":{
        "list_name":"HSK Level 1",
        "list_id":"12345",
        "character_set":"simplified",
        "date_created":"2021-06-16T23:06:48.467526",
        "created_by":"admin"
   },
   "words":[
      {
         "word_simplified":"叫",
         "word_traditional":"叫",
         "definition":"to shout; to call; to order; to ask; to be called; by (indicates agent in the passive mood)",
         "pronunciation":"jiào",
      },
      {
         "word_simplified":"欢迎",
         "word_traditional":"歡迎",
         "definition":"to welcome; welcome",
         "pronunciation":"huān yíng",
      }
   ]
}
````