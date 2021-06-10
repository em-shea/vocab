# When a user signs up, 
def lambda_handler(event, context):
    
    print(event)

    response = event.get('response')
    print(response)

    response.update({
        'autoConfirmUser': True
    })
    
    print(event)
    return event