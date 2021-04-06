# This function auto-confirms new users at sign-up
def lambda_handler(event, context):
    
    print(event)

    response = event.get('response')
    response.update({
        'autoConfirmUser': True
    })
    
    return event