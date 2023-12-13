# ###################
#  파이어베이스 O   #
#  디스코드     O   #
#  이메일      X    #
# ###################
import os
import sys
import time
import requests
import yaml
from datetime import datetime
from notice import Notice
from http.client import HTTPException
from bs4 import BeautifulSoup

# firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

with open('config.yaml', encoding='UTF-8') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
DISCORD_WEBHOOK_URL = config['DISCORD_WEBHOOK_URL']

Hansung_BASE_URL = "https://www.hansung.ac.kr/"
Hansung_REQUEST_URL = Hansung_BASE_URL + "hansung/8385/subview.do"
Computer_BASE_URL = "http://cse.hansung.ac.kr/"
Computer_REQUEST_URL = Computer_BASE_URL + "news?searchCondition"

# Firebase database 인증 및 앱 초기화
cred = credentials.Certificate('notice_bot.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://notice-bot-bbf3c-default-rtdb.firebaseio.com/'
})


def send_message(message):
    requests.post(DISCORD_WEBHOOK_URL, data=message)


# href를 id로 변환
def extractNumberFrom(string: str) -> int:
    return int(''.join(filter(str.isdigit, string)))


def Hansung_scrapeNotices():
    r"""
    한성대학교 전체 공지사항 첫 페이지를 헤더 공지를 제외하고 스크래핑하여 :class:`notice` 리스트를 반환한다.

    `BASE_URL`이 잘못된 경우 :class:`HTTPException`을 raise한다.
    """

    try:
        response = requests.get(Hansung_REQUEST_URL)
        soup = BeautifulSoup(response.text, "html.parser")

        if response.status_code is not requests.codes['ok']:
            raise HTTPException(
                '잘못된 URL을 요청했습니다. (status code: {response.status_code})')
    except Exception as e:
        raise e

    result = []
    tableRows = soup.select('tbody>tr')
    for tableRow in tableRows:
        # 헤더 공지 혹은 블라인드 처리된 공지는 건너뛴다.
        if any(className in tableRow.attrs['class'] for className in ['notice', 'blind']):
            continue

        subject = tableRow.select_one('.td-subject > a[href]')
        href = subject['href']

        id = str(extractNumberFrom(href))
        title = subject.text.strip()
        
        #url = Hansung_BASE_URL + href.removeprefix("/")
        url = Hansung_BASE_URL + href if href.startswith("/") else Hansung_BASE_URL + "/" + href
        result.append(Notice(id, title, url))
        if result.__len__() == 10:
            break
    # ID를 기준으로 내림차순 정렬
    result.sort(key=lambda x: int(x.id), reverse=True)

    return result


def count_new_post(hansungLastkey, hansung_id_list ):

    print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
    print("id_list: "+str(hansung_id_list))
    print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
    count = 0
    for hansung_id in hansung_id_list:
        if int(hansungLastkey) < int(hansung_id):
            count = count+1
    return count


def Computer_scrapeNotices():
    r"""
    컴퓨터공학부 전체 공지사항 리스트를 반환한다.

    `BASE_URL`이 잘못된 경우 :class:`HTTPException`을 raise한다.
    """

    try:
        response = requests.get(Computer_REQUEST_URL)
        soup = BeautifulSoup(response.text, "html.parser")

        if response.status_code is not requests.codes['ok']:
            raise HTTPException(
                '잘못된 URL을 요청했습니다. (status code: {response.status_code})')
    except Exception as e:
        raise e

    result = []
    # tbody 태그 아래의 a 태그에 접근
    a_tags = soup.select('tbody a')  # tbody 태그 아래의 모든 a 태그 선택
    for a_tag in reversed(a_tags[-10:]):

        subject = a_tag.text
        href = a_tag['href']

        id = str(extractNumberFrom(href))
        title = subject.strip()
        # url = Computer_BASE_URL + href.removeprefix("/")
        url = Computer_BASE_URL + href if href.startswith("/") else Computer_BASE_URL + "/" + href
        result.append(Notice(id, title, url))
        if result.__len__() == 10:
            break
          
    # ID를 기준으로 내림차순 정렬
    result.sort(key=lambda x: int(x.id), reverse=True)
              
    return result


while True:
    print("\n\n한성대 공지사항 크롤링을 시작합니다")
    # db 위치 지정, /Notice_List/Hansung_Notice/ID_Title_Url을 가르킴
    Hansung_ref = db.reference('/Notice_List/Hansung_Notice/ID_Title_Url')
    
    # limit_to_last를 사용하여 마지막의 데이터만 가져옴
    a = Hansung_ref.order_by_key().limit_to_last(1).get()
    
    # 마지막 데이터의 key값만 가져옴
    # a가 None이면 기본값으로 1을 설정
    hansungLastkey = list(a.keys())[0] if a is not None else "1"

    print(f"hansungLastkey: {hansungLastkey}")

    # 공지사항을 크롤링해서 10개를 class:`notice`형태의 리스트로 반환한다.
    Hansung_Result = Hansung_scrapeNotices()
    
    hansung_id_list = []
    for i in range(len(Hansung_Result)):
        hansung_id_list.append(Hansung_Result[i].id)
        
    Hansung_index = count_new_post(hansungLastkey, hansung_id_list)
    print("새로운 공지 개수 : "+str(Hansung_index)+"개")
    
    if Hansung_index > 0:
        for i in range(int(Hansung_index)):
            # 현재 타임스탬프를 얻어와서 timestamp 필드에 추가
            current_timestamp = int(time.time())
            formatted_timestamp = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            # Hansung_notice_title = str(Hansung_Result[i].title)

            Hansung_notice_title = Hansung_Result[i].title.replace('\t', '').replace('\n', '')
            Hansung_notice_url = str(Hansung_Result[i].url)
            # 해당 데이터가 없으면 생성한다.
            Hansung_ref.update({Hansung_Result[i].id: {'title': Hansung_Result[i].title, 'url': Hansung_Result[i].url, 'time': formatted_timestamp}})
            print(f"ID: {Hansung_Result[i].id} / Title: {Hansung_notice_title} / URL: {Hansung_Result[i].url} ")
            print(" -> DB 저장 완료\n")
            
          
            message = {'content': ''}
            new_content = "🔴📝 NEW 한성 공지 📝 🔴\n"+ Hansung_notice_title+"\n"+Hansung_notice_url
            message['content'] += new_content
            send_message(message)
            print(" ->디스코드 알림  및  DB 저장 완료\n")
            time.sleep(2)
    else:
        print("한성대 New 공지가 없다")
    time.sleep(2)

    print("\n\n컴공 공지사항 크롤링을 시작합니다")
    
    # db 위치 지정, /Notice_List/Computer_Notice/ID_Title_Url을 가르킴
    Computer_ref = db.reference('/Notice_List/Computer_Notice/ID_Title_Url')
    
    # limit_to_last를 사용하여 마지막의 데이터만 가져옴
    b = Computer_ref.order_by_key().limit_to_last(1).get()

    # 마지막 데이터의 key값만 가져옴
    # b가 None이면 기본값으로 1을 설정
    computerLastkey = list(b.keys())[0] if b is not None else "1"
    
    print(f"computerLastkey: {computerLastkey}")
    
    # 공지사항을 크롤링해서 10개를 class:`notice`형태의 리스트로 반환한다.
    Computer_Result = Computer_scrapeNotices()

    computer_id_list = []
    for i in range(len(Computer_Result)):
        computer_id_list.append(Computer_Result[i].id)
        
    Computer_index = count_new_post(computerLastkey, computer_id_list)
    print("새로운 공지 개수 : "+str(Computer_index)+"개")
    
    if Computer_index > 0:
        for i in reversed(range(int(Computer_index))):
        # 현재 타임스탬프를 얻어와서 timestamp 필드에 추가
            current_timestamp = int(time.time())
            formatted_timestamp = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            # Computer_notice_title = str(Computer_Result[i].title)
            Computer_notice_title = Computer_Result[i].title.replace('\t', '').replace('\n', '')
            Computer_notice_url = str(Computer_Result[i].url)
            # 해당 데이터가 없으면 생성한다.
            Computer_ref.update({Computer_Result[i].id: {'title': Computer_Result[i].title, 'url': Computer_Result[i].url, 'time': formatted_timestamp}})
            print(f"ID: {Hansung_Result[i].id} / Title: {Computer_notice_title} / URL: {Hansung_Result[i].url} ")
            print(" -> DB 저장 완료\n")
            
            
            message = {'content': ''}
            new_content = "🟢📝 NEW 컴공 공지 📝🟢\n"+Computer_notice_title+"\n"+Computer_notice_url
            message['content'] += new_content
            send_message(message)
            print(" ->디스코드 알림  및  DB 저장 완료\n")
            time.sleep(2)
    else:
        print("컴공 New 공지가 없다")
        
    print("한바퀴 돌았습니다. \n 5분간 대기를 시작합니다")
    time.sleep(300)
