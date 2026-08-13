import json

import sys
sys.path.append('../tests/')

def response(status_code, message, data=None):

    # Derived from the status code rather than matched against a list of known ones.
    # This previously only assigned for 200 and 502, so any other code - a 403, say -
    # raised UnboundLocalError instead of returning a response.
    success_status = 200 <= status_code < 300

    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({"success" : success_status, "message" : message, "data" : data })
    }