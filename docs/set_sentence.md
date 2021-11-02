# Set sentence API

The set sentence function is a POST method at api.haohaotiantian.com/sentence.
This endpoint requires Cognito authentication. It creates, udpates, or erases a user's practice sentence for a given daily word.

Example payload:
````
{
    "cognito_id":"123",
    "list_id": "123",
    "character_set": "simplified",
    "sentence_id":"123", # sentence ID will be generated if none is provided
    "sentence": "我喜欢学习汉语。"
}
````