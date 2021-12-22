# Get characters for list id API

This function is used inside a state machine that takes a list id and generates audio files for each word in the list. The function pulls batches of words from DynamoDB and passes a list of word ids and simplified characters to the next state machine step.

Example input:
````
{
  "list_id": "123456",
  "last_word_token": ""
}
````

Example output:
````
{
    "last_word_token": "WORD#123456"
    "word_list": [
        {
            'list_id': ""LIST#123456"",
            'word_id': "WORD#123456",
            'text': "怎么样"
        },
        {
            'list_id': ""LIST#123456"",
            'word_id': "WORD#123456",
            'text': "回答"
        },
        ...
    ]    
}
````