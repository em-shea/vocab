from models import User, Subscription

def _format_user_data(user_data):

    user = None
    subscription_list = []

    #  Loop through all users and subs
    for item in user_data:
        # print(item)

        # If Dynamo item is user metadata, create User class
        if 'Email address' in item:
            print('user', item['Email address'])
            user = User(
                email_address = item['Email address'],
                user_id = item['PK'][5:], 
                character_set_preference = item['Character set preference'], 
                date_created = item['Date created'], 
                user_alias = item['User alias'], 
                user_alias_pinyin = item['User alias pinyin'], 
                user_alias_emoji = item['User alias emoji'],
                subscriptions = []
            )

        # If Dynamo item is a list subscription, add the list to the user's lists dict
        if 'List name' in item:
            print('list', item['List name'])
            # Shortening list id from unique id (ex, LIST#1ebcad40-bb9e-6ece-a366-acde48001122#SIMPLIFIED)
            if 'SIMPLIFIED' in item['SK']:
                list_id = item['SK'][5:-11]
            if 'TRADITIONAL' in item['SK']:
                list_id = item['SK'][5:-12]

            sub = Subscription(
                list_name = item['List name'], 
                unique_list_id = item['SK'][5:], 
                list_id = list_id, 
                character_set = item['Character set'], 
                status = item['Status'], 
                date_subscribed = item['Date subscribed']
            )
            subscription_list.append(sub)

        # Sort lists by list id to appear in order (Level 1, Level 2, etc.)
        subscription_list = sorted(subscription_list, key=lambda k: k.list_id, reverse=False)

    user.subscriptions = subscription_list

    print('formatted user ', user)
    return user