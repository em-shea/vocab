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

# @dataclass
# class List

# @dataclass
# class Word

# @dataclass
# class ReviewWord