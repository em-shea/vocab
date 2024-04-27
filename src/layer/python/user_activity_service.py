from user_service import get_single_user_with_activity
from review_word_service import get_review_words

import sys
sys.path.append('../tests/')

def get_user_activity(cognito_id, date_range=10):
    
    user_data = get_single_user_with_activity(cognito_id, date_range)
    print('user activity: ', user_data)
    
    # Add recent words for subscribed lists
    
    # for list in user_data['subscriptions']:
    #     get_review_words(list['list_id'], date_range)
        # append

    return user_data