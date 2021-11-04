# Set sentence API

The set sentence function is a GET method at api.haohaotiantian.com/sentence.
This endpoint requires Cognito authentication. It creates, udpates, or erases a user's practice sentence for a given daily word.

Example output:
````
{
    "sentences":[
        {
            "sentence_id":"123",
            "sentence": "我喜欢学习汉语。",
            "date_created": "2021-06-16T23:06:48.467526"
            "list_id": "123",
            "character_set": "simplified"
        },
        {
            "sentence_id":"234",
            "sentence": "我喜欢写句子。",
            "date_created": "2021-06-16T23:06:48.467526"
            "list_id": "234",
            "character_set": "simplified"
        }
    ]   
}