import json
import boto3

from datetime import datetime
import pytz

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
    
def user_age(birth_db, current_year, current_month, current_day):
    birth=str(birth_db)
    birth_year=int(birth[:4])
    birth_month=int(birth[4:6])
    birth_day=int(birth[6:])
    
    #만 나이 계산
    age=0
    if current_month<birth_month:  #생일 안지난 경우
        age=current_year-birth_year-1
    elif current_month>birth_month:  #생일 지난 경우
        age=current_year-birth_year
    else:
        if current_day<birth_day:  #생일 안지난 경우
            age=current_year-birth_year-1
        else:  #생일 지난 경우
            age=current_year-birth_year
            
    return age

def checklist(age, gender):
    common_2=[
        '진찰 및 상담', '신체계측', '시력 및 청력 검사', '혈압측정', '흉부방사선 검사', '혈액검사', '구강검사'
        ]
    add=list()
    
    #연령별
    if age<19 and age>64:
        common_2.clear()
        
    if age%20==0:
        add.append('정신건강검사_우울증')
    if age==40:
        add.append('B형간염검사')
        add.append('치면세균막검사')
        add.append('생활습관평가')
        # common_2.append('위암검진(위장조영검사/위내시경)')
    if age>=40:
        common_2.append('위암검진(위장조영검사/위내시경)')
        add.append('간암검진(초음파검사, 혈액검사)')
        if age>=50:
            add.append('대장암(분변잠혈 검사, 대장내시경검사/대장 이중조영 검사)')
    if age in [50, 60, 70]:
        add.append('생활습관평가')
    if age>=60:
        common_2.append('인지기능장애검사')
    if age==66 or age==70 or age==80:
        add.append('노인신체기능검사')
    
    #성별    
    if gender=='여자':
        common_2.append('자궁경부세포검사')
        
        if age>=40:
            common_2.append('유방암검진')
            if age%4==0:
                add.append('이상지질혈증(총콜레스테롤, HDL콜레스테롤, LDL콜레스테롤, 중성지방)')
                
        if age==54 or age==66:
            add.append('골다공증')
    else:
        if age>=24 and age%4==0:
            add.append('이상지질혈증(총콜레스테롤, HDL콜레스테롤, LDL콜레스테롤, 중성지방)')
            
    return common_2, add


def send_email(email, name, inspection):
    client = boto3.client("ses", region_name="ap-northeast-2")
    
    sender='eunhyekim811@gmail.com'  #SES에서 인증 받은 이메일
    to_email=email  #받는 사람 이메일 주소
    subject='건강검진 안내드립니다.'  #메일 제목
    content_type='Text'
    
    add_items = ', '.join(item for item in inspection)
    #메일 내용
    content=f"""
    안녕하세요, {name}님.
    귀하의 건강과 행복을 기원하며, 정기 건강검진 안내드립니다.
    
    올해 건강검진에서 진행해야 할 검사항목은 다음과 같습니다: 
    <{add_items}>
    
    
    건강검진 전날에는 20시 이후로는 금식 부탁드리며, 기름진 음식 및 과식과 음주, 과격한 운동은 피해주세요. 또한, 모든 수검자께서는 반드시 신분증을 지참해주셔야 합니다.

    혈액응고 억제제를 복용하시는 경우 담당 의사와 상의 후 검진을 진행하시길 권장하며, 전립선, 자궁 초음파 검사의 경우 검진 당일 아침 첫 소변은 참아주시길 바랍니다.

    여성분의 경우 생리 종료일로부터 7일 이후에 검사가 가능합니다. 또한, 모유수유 중단 후 최소 6개월 뒤부터 유방 검사가 가능하며, 자궁경부암 검사 시 24시간 내 성관계, 크림 사용, 질세척과 72시간 내 질정 사용은 금하고 있습니다.

    추가 문의사항에 대해서는 아래 정보로 연락 주시길 바랍니다.
    감사합니다.

    문의: {sender}
    """

    try:
        response = client.send_email(
            Destination={
                "ToAddresses": [
                    to_email
                ],
            },
            Message={
                "Body": {
                    content_type: {
                        "Charset": "UTF-8",
                        "Data": content,
                    }
                },
                "Subject": {
                    "Charset": "UTF-8",
                    "Data": subject,
                },
            },
            Source=sender,
        )
    except Exception as e:
        print(f"An error occured while sending email: {e}")


def lambda_handler(event, context):
    # today=datetime.utcnow().date()
    korea_tz=pytz.timezone('Asia/Seoul')
    current=datetime.now(korea_tz)
    
    current_year = current.year
    current_month = current.month
    current_day = current.day
    
    db_access = DatabaseAccess('UserHealthCheck')
    
    items, count = db_access.get_data()
    print(f"items: {items}, count: {count}")
    
    for item in items:
        # event_name = item['EventName']['S']
        email=item['email']
        birth=item['birth']
        gender=item['gender']
        name=item['name']
        
        age=user_age(birth, current_year, current_month, current_day)
        two, add=checklist(age, gender)
        
        birth_str=str(birth)
        birth_year=int(birth_str[:4])
        if birth_year%2==0 and current_year%2==0:
            add.extend(two)
        elif birth_year%2!=0 and current_year%2!=0:
            add.extend(two)
        
        if len(add)!=0:
            send_email(email, name, add)
    

    return {
        'statusCode': 200,
        'body': json.dumps('Emails sent successfully')
    }