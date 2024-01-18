# ##################
#  파이어베이스 O   #
#  디스코드     O   #
#  이메일      X    #
# ##################
import os
import sys
import time
import requests
import yaml
from datetime import datetime
from http.client import HTTPException
from bs4 import BeautifulSoup

# Firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Import Notice class from notice module (assuming you have it)
from notice import Notice

Hansung_BASE_URL = "https://www.hansung.ac.kr/"
Hansung_REQUEST_URL = Hansung_BASE_URL + "hansung/8385/subview.do"
Computer_BASE_URL = "http://cse.hansung.ac.kr/"
Computer_REQUEST_URL = Computer_BASE_URL + "news?searchCondition"

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

with open('config.yaml', encoding='UTF-8') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

DISCORD_WEBHOOK_URL = config['DISCORD_WEBHOOK_URL']

# Firebase database 인증 및 앱 초기화
cred = credentials.Certificate('notice_bot.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://notice-bot-bbf3c-default-rtdb.firebaseio.com/'
})


def send_message(message):
    requests.post(DISCORD_WEBHOOK_URL, data=message)


def extract_number_from(string: str) -> int:
    return int(''.join(filter(str.isdigit, string)))


def scrape_notices(request_url, base_url, limit=10):
    try:
        response = requests.get(request_url)
        soup = BeautifulSoup(response.text, "html.parser")

        if response.status_code != requests.codes['ok']:
            raise HTTPException(
                f'잘못된 URL을 요청했습니다. (status code: {response.status_code})')
    except Exception as e:
        raise e

    result = []
    a_tags = soup.select('tbody a')
    for a_tag in reversed(a_tags[-limit:]):
        subject = a_tag.text
        href = a_tag['href']

        notice_id = str(extract_number_from(href))
        title = subject.strip()
        url = base_url + \
            href if href.startswith("/") else base_url + "/" + href
        result.append(Notice(notice_id, title, url))

    result.sort(key=lambda x: int(x.id), reverse=True)
    return result


def count_new_post(last_key, id_list):
    count = 0
    for notice_id in id_list:
        if int(last_key) < int(notice_id):
            count += 1
    return count


def notify_and_update(ref, result, last_key):
    id_list = [notice.id for notice in result]

    index = count_new_post(last_key, id_list)
    print(f"새로운 공지 개수: {index}개")

    if index > 0:
        for i in range(index):
            current_timestamp = int(time.time())
            formatted_timestamp = datetime.fromtimestamp(
                current_timestamp).strftime('%Y-%m-%d %H:%M:%S')

            notice_title = result[i].title.replace('\t', '').replace('\n', '')
            notice_url = str(result[i].url)

            ref.update({result[i].id: {'title': result[i].title,'url': result[i].url, 'time': formatted_timestamp}})
            print(
                f"ID: {result[i].id} / Title: {notice_title} / URL: {result[i].url}")
            print(" -> DB 저장 완료\n")

            message = {'content': ''}
            new_content = f"🟢📝 NEW 공지 📝🟢\n{notice_title}\n{notice_url}"
            message['content'] += new_content
            send_message(message)
            print(" -> 디스코드 알림 및 DB 저장 완료\n")
            time.sleep(2)
    else:
        print("New 공지가 없다")
    time.sleep(2)


while True:
    try:    
        print("\n\n한성대 공지사항 크롤링을 시작합니다")
        # db 위치 지정, /Notice_List/Hansung_Notice/ID_Title_Url을 가르킴
        Hansung_ref = db.reference('/Notice_List/Hansung_Notice/ID_Title_Url')

        # limit_to_last를 사용하여 마지막의 데이터만 가져옴
        a = Hansung_ref.order_by_key().limit_to_last(1).get()

        # 마지막 데이터의 key값만 가져옴
        # a가 None이면 기본값으로 1을 설정
        hansung_last_key = list(a.keys())[0] if a is not None else "1"

        print(f"hansung_last_key: {hansung_last_key}")

        # 공지사항을 크롤링해서 10개를 class:`notice`형태의 리스트로 반환한다.
        Hansung_result = scrape_notices(Hansung_BASE_URL + "hansung/8385/subview.do",
                                        Hansung_BASE_URL, limit=10)

        notify_and_update(Hansung_ref, Hansung_result, hansung_last_key)

        print("\n\n컴공 공지사항 크롤링을 시작합니다")

        # db 위치 지정, /Notice_List/Computer_Notice/ID_Title_Url을 가르킴
        Computer_ref = db.reference('/Notice_List/Computer_Notice/ID_Title_Url')

        # limit_to_last를 사용하여 마지막의 데이터만 가져옴
        b = Computer_ref.order_by_key().limit_to_last(1).get()

        # 마지막 데이터의 key값만 가져옴
        # b가 None이면 기본값으로 1을 설정
        computer_last_key = list(b.keys())[0] if b is not None else "1"

        print(f"computer_last_key: {computer_last_key}")

        # 공지사항을 크롤링해서 10개를 class:`notice`형태의 리스트로 반환한다.
        Computer_result = scrape_notices(Computer_BASE_URL + "news?searchCondition",
                                        Computer_BASE_URL, limit=10)

        notify_and_update(Computer_ref, Computer_result, computer_last_key)

        print("한바퀴 돌았습니다. \n 5분간 대기를 시작합니다")
        time.sleep(300)
        
    except Exception as e:
        # 예상치 못한 예외를 처리하고 로그에 기록합니다.
        print(f"Unexpected error occurred: {e}")
        print("Sleeping for 24 hours before retrying.")
        send_message({"content": f"Unexpected error occurred: {e}. Sleeping for 24 hours before retrying."})
        time.sleep(86400)