import json

import sys
sys.path.append('../tests/')

def response(status_code, message, data=None):

    if status_code == 200:
        success_status = True
    if status_code == 502:
        success_status = False

    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({"success" : success_status, "message" : message, "data" : data })
    }