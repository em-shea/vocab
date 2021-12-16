import list_word_service

# Given a list id, retrieve an array with word ids and simplified characters for that list
# This function is part of a state machine that generates pronunciation audio files for a given list

def lambda_handler(event, context):
    print('event', event)
    list_id = event['listId']

    detailed_word_list = list_word_service.get_words_in_list(list_id)

    word_list = format_word_list(detailed_word_list)
    response_body = {
        "word_list": word_list
    }

    print(response_body)
    return response_body

# Remove the word details that aren't needed to reduce the payload size for Step Functions
def format_word_list(detailed_word_list):

    word_list = []

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

    return word_list