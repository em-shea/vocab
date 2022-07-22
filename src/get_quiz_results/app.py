import json

import api_response
import quiz_results_service

# validate query params
# query for users quiz results
# based on query parameters, return one week or one month (use Attr to filter?)
# return whether a user took a quiz for each day and their highest score

# Return quiz status for past week or month
def lambda_handler(event, context):
    print(event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']

    body = json.loads(event["body"])
    if event['body']['date_range'] == 7 or event['body']['date_range'] == 30:
        date_range = event['body']['date_range']
    else:
        date_range = 7
    
    try:
        quiz_results = quiz_results_service.retrieve_quiz_results(cognito_id, date_range)
    except Exception as e:
        print(e)
        return api_response.response(502, "Failed to retrieve quiz results")

    return api_response.response(200, "Successfully retrieved quiz results", quiz_results)