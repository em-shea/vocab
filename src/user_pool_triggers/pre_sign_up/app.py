def lambda_handler(event, context):
    
    print(event)

    response = event.get('response')
    response.update({
        'autoConfirmUser': True
    })
    
    print(event)
    return event