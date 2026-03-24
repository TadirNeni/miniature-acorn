import json

def handler(request):
    data = request.get_json()

    # your ML or IDS logic here
    result = "Normal Traffic"

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"result": result})
    }