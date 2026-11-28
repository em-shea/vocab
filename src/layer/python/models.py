import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Subscription:
    list_name: str
    unique_list_id: str
    list_id: str
    character_set: str
    status: str
    date_subscribed: str

@dataclass
class Word:
    word_id: str
    simplified: str
    traditional: str
    pinyin: str
    definition: str
    audio_file_key: str
    difficulty_level: str
    hsk_level: str

@dataclass
class VocabList:
    list_id: str
    words: List[Word]

@dataclass
class ReviewWord:
    list_id: str
    date_sent: str
    word: Dict[str, Word]

@dataclass
class QuizQuestionData:
    answer_submitted: ReviewWord
    correct_answer: ReviewWord
    test_set: Dict[str, str]
    was_answer_correct: bool

@dataclass
class Quiz:
    quiz_id: str
    date_created: datetime.datetime
    list_id: str
    character_set: str
    quiz_data: List[QuizQuestionData]
    question_quantity: int
    correct_answers: int

@dataclass
class Sentence:
    sentence_id: str
    sentence: str
    date_created: str
    list_id: str
    character_set: str
    word: Dict[str, Word]

@dataclass
class Writing:
    # A word whose characters the user practised writing on the site.
    list_id: str
    word_id: str
    date_created: str
    character_set: str = ''

@dataclass
class User:
    email_address: str
    user_id: str
    # How study content renders: 'simplified' or 'traditional'.
    character_set_preference: str
    user_alias: str
    user_alias_pinyin: str
    user_alias_emoji: str
    # Which language the interface is written in: 'en' or 'cn'. A separate axis
    # from character_set_preference - a learner can read an English interface
    # while studying traditional characters. Defaults for records written before
    # the field existed.
    language_preference: str = 'en'
    subscriptions: Optional [List[Subscription]] = None
    quizzes: Optional [List[Quiz]] = None
    sentences: Optional [List[Sentence]] = None
    writings: Optional [List[Writing]] = None
    date_created: Optional [datetime.datetime] = None
    # Opt-in public profile and leaderboard entry (public_profile_service).
    public_profile: bool = False
    public_handle: Optional [str] = None
    founding_tester: bool = False
