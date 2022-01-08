import sys
sys.path.append('../tests/')

# Temporary service until vocab lists are dynamic and stored in DynamoDB

def get_vocab_lists():
    return [
    {
      "list_name": "HSK Level 1",
      "list_id": "1ebcad3f-5dfd-6bfe-bda4-acde48001122",
      "list_difficulty_level": "Beginner",
      "date_created": "2018-12-16T23:06:48.467526",
      "created_by": "admin"
    },
    {
      "list_name": "HSK Level 2",
      "list_id": "1ebcad3f-adc0-6f42-b8b1-acde48001122",
      "list_difficulty_level": "Beginner",
      "date_created": "2018-12-16T23:06:48.467526",
      "created_by": "admin"
    },
    {
      "list_name": "HSK Level 3",
      "list_id": "1ebcad3f-f815-6b92-b3e8-acde48001122",
      "list_difficulty_level": "Intermediate",      
      "date_created": "2018-12-16T23:06:48.467526",
      "created_by": "admin"
    },
    {
      "list_name": "HSK Level 4",
      "list_id": "1ebcad40-414f-6bc8-859d-acde48001122",
      "list_difficulty_level": "Intermediate",
      "date_created": "2018-12-16T23:06:48.467526",
      "created_by": "admin"
    },
    {
      "list_name": "HSK Level 5",
      "list_id": "1ebcad40-bb9e-6ece-a366-acde48001122",
      "list_difficulty_level": "Advanced",      
      "date_created": "2018-12-16T23:06:48.467526",
      "created_by": "admin"
    },
    {
      "list_name": "HSK Level 6",
      "list_id": "1ebcad41-197a-6700-95a3-acde48001122",
      "list_difficulty_level": "Advanced",
      "date_created": "2018-12-16T23:06:48.467526",
      "created_by": "admin"
    }
]