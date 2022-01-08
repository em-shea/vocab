import datetime
from typing import List
from dataclasses import dataclass

@dataclass
class Subscription:
    list_name: str
    unique_list_id: str
    list_id: str
    character_set: str
    status: str
    date_subscribed: str
    # def to_dict(self):
    #     return {
    #         'list_name': self.list_name
    #     }

@dataclass
class User:
    email_address: str
    user_id: str
    character_set_preference: str
    date_created: datetime.datetime
    user_alias: str
    user_alias_pinyin: str
    user_alias_emoji: str
    subscriptions: List[Subscription]

def format_user_data(user_data):

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