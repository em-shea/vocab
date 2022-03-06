import sys
import list_word_service

# Given a list id, retrieve an array with word ids and simplified characters for that list
# This function is part of a state machine that generates pronunciation audio files for a given list

def lambda_handler(event, context):
    print('event ', event)
    list_id = event['list_id']
    last_word_token = event['last_word_token']

    detailed_word_list = list_word_service.get_words_in_list(list_id, limit=20, last_word_token=last_word_token, audio_file_key_check=False)
    # print('detailed word list: ', detailed_word_list)

    if len(detailed_word_list) == 20:
        updated_last_word_token = detailed_word_list[-1]['word_id']
    else:
        updated_last_word_token = None
    word_list = format_and_filter_word_list(detailed_word_list)

    response_body = {
        "list_id": list_id,
        "word_list": word_list,
        "last_word_token": updated_last_word_token
    }

    print('response body ', response_body)
    return response_body

# Remove the word details that aren't needed to reduce the payload size for Step Functions
def format_and_filter_word_list(detailed_word_list):

    word_list = []

    for item in detailed_word_list:
        if item['word']['Audio file key'] == "":
            word_list.append(
                {
                    'list_id': item['list_id'],
                    'word_id': item['word_id'],
                    'text': item['word']['Simplified']
                }
            )

    return word_list