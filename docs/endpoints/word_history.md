# Word History API

The word history function is a GET method at api.haohaotiantian.com/history.

If an HSK level and a number of days are passed as query string parameters, the API call will return that many days of past words for the given level.

If no parameters are passed, it will return the past 7 days of words for each of the 6 HSK levels.

If an HSK level is passed, it will return the past 90 days of words for the given level.

Example query string parameters:

````
https://api.haohaotiantian.com/history?list=HSKLevel4

https://api.haohaotiantian.com/history?list=HSKLevel1&date_range=30

````

Example of the API response:

````json
{
  "HSKLevel1": [
    {
      "Word": {
          "Definition": "dish (type of food); vegetables; vegetable; cuisine; CL:盤|盘[pan2],道[dao4]",
          "HSK Level": "1",
          "Word": "菜",
          "Pronunciation": "cài",
          "Word-Traditional": "菜"
      },
      "Date": "2020-01-03",
      "ListId": "HSKLevel1"
    },
    {...}
  ],
  "HSKLevel2": [...]
}
````