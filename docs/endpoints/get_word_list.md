# Get word list function

The get word list function is triggered as part of the generate list audio files Step Function.
It takes in a list ID and queries DynamoDB to return a list of all word IDs and simplified characters for that list.

Example input:
````
{
    "listID":"12345678"
}
````


Example output:
````
{
    "list_id": "12345678",
    "word_list": [
        {
            "word_id": "1ec4a4cc-4277-6a38-b218-acde48001122",
            "text": "爱"
        },
        {
            "word_id": "1ec4a4cc-4277-6cea-b218-acde48001122",
            "text": "八"
        },
        {
            "word_id": "1ec4a4cc-4277-6d94-b218-acde48001122",
            "text": "爸爸"
        },
        {
            "word_id": "1ec4a4cc-4277-6e34-b218-acde48001122",
            "text": "杯子"
        }
    ]
}