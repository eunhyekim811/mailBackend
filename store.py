import boto3
import json
# from datetime import datetime

class DatabaseAccess():
    def __init__(self, TABLE_NAME):
        # DynamoDB 세팅
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(TABLE_NAME)
    
    def get_data(self):
        res = self.table.scan()
        items = res['Items'] # 모든 item
        count = res['Count'] # item 개수
        return items, count
    
    def put_data(self, input_data):
        self.table.put_item(
            Item =  input_data
        )
        print("Putting data is completed!")

def lambda_handler(event, context):
    
    db_access = DatabaseAccess('UserHealthCheck')

    body=json.loads(event['body'])

    email = body.get('email')
    birth = body.get('birth')
    gender = body.get('gender')
    name = body.get('name')
    
    if event['httpMethod'] == 'POST':
        input_data = {
        # "email" : event['email'],
        # "birth"   : int(event['birth']), 
        # "gender"   : event['gender'], 
        # "name"   : event['name']
            "email" : email,
            "birth"   : birth, 
            "gender"   : gender, 
            "name"   : name
        }
        
        items, count=db_access.get_data()
        print(f"items: {items}, count: {count}")
        for item in items:
            emailDB=item['email']
            if email==emailDB:
                return {
                    'statusCode': 201, 
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type"
                    },
                    'body': json.dumps('This is Hey Tech Blog!')
                }
                
        
        db_access.put_data(input_data)
    
    elif event['httpMethod'] == 'GET':
        items, count = db_access.get_data()
        print(f"items: {items}, count: {count}")
    
    else:
        print("Confirm the method!")
        
    # TODO implement
    return {
        'statusCode': 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        'body': json.dumps('This is Hey Tech Blog!')
    }