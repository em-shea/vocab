import list_word_service

# Given a list id, retrieve an array with word ids and simplified characters for that list
# This function is part of a state machine that generates pronunciation audio files for a given list

def lambda_handler(event, context):
    print('event', event)
    list_id = event['listId']

    detailed_word_list = list_word_service.get_words_in_list(list_id, limit=None, last_word_token=None)

    word_list = format_word_list(detailed_word_list)
    response_body = {
        "word_list": word_list,
        "last_word_id_processed": word_list[-1]['word_id']
    }

    print(response_body)
    return response_body

# Remove the word details that aren't needed to reduce the payload size for Step Functions
def format_word_list(detailed_word_list):

    word_list = []

    while len(word_list) < 1250:
        for item in detailed_word_list:
            # Add this condition once initial upload complete
            # if item['Word']['Audio file key'] != "":
            word_list.append(
                {
                    'list_id': item['list_id'],
                    'word_id': item['word_id'],
                    'text': item['word']['Simplified']
                }
            )

    # if word list is less than 1250, set 'last word processed', if not leave null

    return word_list