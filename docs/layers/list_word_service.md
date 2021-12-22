# List word service

This layer returns the words associated with a given list_id. Optional parameters are limit (how many words to return) and last_word_token (for pagination through results),

Example input:
````python
get_words_in_list(list_id, limit=None, last_word_token=None)
````

Example output: 
````
[
    {
        "list_id": "LIST#123456",
        "word_id": "WORD#123456",
        "word": {
                    "Simplified": "叉子",
                    "Traditional": "叉子",
                    "Pronunciation": "chā zi",
                    "Definition": "fork; CL:把[ba3]",
                    "HSK Level": "5",
                    "Difficulty level": "Advanced",
                    "Audio file key": ""
                }
    },
    ...
]
````