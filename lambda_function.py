import json

def hello_handler(body):
    return {"message": "Hello there, welcome!"}, 200

def goodbye_handler(body):
    return {"message": "Okay, goodbye then!"}, 200

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
    except Exception:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "Invalid JSON in request body"})
        }

    endpoint = body.get("endpoint")
    if not endpoint:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "No endpoint provided in request body"})
        }

    # Route to the appropriate handler based on the "endpoint" field
    if endpoint == "hello":
        result, status = hello_handler(body)
    elif endpoint == "goodbye":
        result, status = goodbye_handler(body)
    else:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": f"Unknown endpoint: {endpoint}"})
        }

    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result)
    }
