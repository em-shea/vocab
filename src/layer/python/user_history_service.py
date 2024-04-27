import os
import json
import boto3
from dataclasses import asdict
from models import Quiz, Sentence 
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta

import sys
sys.path.append('../tests/')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

def retrieve_user_history(cognito_id, date_range=10):
    
    user_data = query_user_lists_and_recent_quizzes_and_sentences(cognito_id, date_range)
    user_data_with_recent_words = query_recent_words_for_user_lists(user_data, date_range) # review_word_service

    return user_data_with_recent_words

def query_user_lists_and_recent_quizzes_and_sentences(cognito_id, date_range=10):

    # Query for between DATE# (quiz and sentence in date range) and USER# - LIST# is stored next to most recent quizzes/sentences
    
    return user_data

def query_recent_words_for_user_lists(user_data, date_range=10):

    # For list in user_data['user_lists'], query for X most recent words and append to user_data

    return user_data_with_recent_words