import os
import time
import requests
import yaml
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from logging.handlers import TimedRotatingFileHandler

# 로그 폴더가 없으면 생성
if not os.path.exists("log"):
    os.makedirs("log")

# 로깅 설정: 콘솔과 파일 모두 출력하도록 구성
log_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 콘솔 핸들러
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# TimedRotatingFileHandler를 이용해 매일 자정마다 로그 파일 회전 (백업 파일은 최대 30개 보관)
log_file = os.path.join("log", "notice_bot.log")
file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=30, encoding='utf-8')
# 회전 시 파일 이름에 날짜가 붙도록 suffix 설정 (예: notice_bot.log.2025-04-01.log)
file_handler.suffix = "%Y-%m-%d.log"
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Firebase 관련 모듈 임포트
import firebase_admin
from firebase_admin import credentials, db

# config.yaml 파일에서 설정값 읽기 (FIREBASE_DB_URL, DISCORD_WEBHOOK_URL)
with open('config.yaml', encoding='UTF-8') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
FIREBASE_DB_URL = config['FIREBASE_DB_URL']
DISCORD_WEBHOOK_URL = config['DISCORD_WEBHOOK_URL']

# Firebase 인증 및 앱 초기화 (인증키 파일: notice_bot.json)
cred = credentials.Certificate('notice_bot.json')
firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})

def get_keywords():
    """
    Firebase의 '/Notice_List/Work_Notice/Keyword' 경로에서 키워드를 가져옵니다.
    데이터가 리스트 형태로 저장되어 있을 때를 가정하여,
    각 값(문자열)을 소문자로 변환하여 리스트로 반환합니다.
    """
    keyword_ref = db.reference('/Notice_List/Work_Notice/Keyword')
    data = keyword_ref.get()
    keywords_list = []
    
    if data and isinstance(data, list):
        for value in data:
            if isinstance(value, str):
                keywords_list.append(value.lower())
    else:
        logging.warning("키워드 목록이 비어있거나, 리스트 형태가 아닙니다.")
    
    logging.info(f"Firebase에서 가져온 키워드: {keywords_list}")
    return keywords_list

def send_discord_alert(message_content):
    """디스코드 웹훅을 통해 알림 메시지를 전송합니다."""
    message = {"content": message_content}
    response = requests.post(DISCORD_WEBHOOK_URL, data=message)
    if response.status_code not in (200, 204):
        logging.error(f"디스코드 웹훅 전송 실패: {response.status_code}")
    else:
        logging.info("디스코드 웹훅 전송 성공")

def fetch_work_recommend():
    """채용 추천 페이지에서 게시글 정보를 추출합니다."""
    url = "https://career.hansung.ac.kr/ko/recruitment/recommend"
    response = requests.get(url)
    if response.status_code != 200:
        logging.error(f"URL 요청 실패, 상태 코드: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # data-role="table"과 class="black"를 가진 <ul> 요소 찾기
    table_ul = soup.find('ul', {'data-role': 'table', 'class': 'black'})
    if not table_ul:
        logging.error("지정한 테이블 요소를 찾을 수 없습니다.")
        return []
    
    # <li class="thead">는 무시하고, <li class="tbody"> 요소들만 추출
    tbody_items = table_ul.find_all('li', class_='tbody')
    data_list = []
    
    for item in tbody_items:
        # ID 추출
        loopnum_tag = item.find('span', class_='loopnum')
        if not loopnum_tag:
            continue
        record_id = loopnum_tag.get_text(strip=True)
        
        # 회사명 추출
        org_span = item.find('span', class_='org')
        if org_span:
            company_text = org_span.get_text(strip=True)
        else:
            company_text = ""
        
        # title과 url 추출
        title_span = item.find('span', class_='title')
        if title_span:
            a_tag = title_span.find('a')
            if a_tag:
                href = a_tag.get('href')
                # URL이 상대경로일 경우 절대 URL로 변환
                if href.startswith("http"):
                    full_url = href
                else:
                    full_url = "https://career.hansung.ac.kr" + href
                title_text = a_tag.get_text(strip=True)
            else:
                full_url = ""
                title_text = ""
        else:
            full_url = ""
            title_text = ""
        
        data_list.append({
            "id": record_id,
            "company": company_text,
            "title": title_text,
            "url": full_url
        })
    
    return data_list

def check_work_type(url, keywords):
    """
    게시글 URL을 방문하여 data-role="post" 요소 내 텍스트에서 
    지정된 키워드(모두 소문자로 변환된 상태)가 존재하는지 확인합니다.
    존재하면 "developer"를 반환하고, 없으면 None을 반환합니다.
    """
    try:
        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f"게시글 URL 요청 실패 (상태 코드: {response.status_code})")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        post_article = soup.find("article", {"data-role": "post"})
        if post_article:
            content_text = post_article.get_text().lower()  # 소문자로 변환하여 비교
            for keyword in keywords:
                if keyword in content_text:
                    return "developer"
        return None
    except Exception as e:
        logging.error(f"게시글 처리 중 에러 발생: {e}")
        return None

def store_data_to_firebase(data_list):
    """
    추출한 게시글 중 DB에 없는 항목을 Firebase에 저장하고,
    저장 시 새 게시글 URL을 방문하여 키워드가 존재하면 workType을 'developer'로 설정하며,
    키워드가 매칭될 때만 디스코드 알림을 전송합니다.
    """
    # /Notice_List/Work_Notice/ID_Title_Url 경로 참조
    ref = db.reference('/Notice_List/Work_Notice/ID_Title_Url')
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Firebase에서 키워드 가져오기 (소문자 형태로 사용)
    firebase_keywords = get_keywords()
    
    for record in data_list:
        # Firebase에 저장할 키: "ID_회사이름" 형태
        record_key = f"{record['id']}_{record['company']}" if record['company'] else record['id']
        
        # 기존에 저장된 데이터가 있는지 확인
        existing_record = ref.child(record_key).get()
        if not existing_record:
            # 새 게시글이면, 게시글 URL을 방문하여 키워드 판별
            work_type = check_work_type(record["url"], keywords=firebase_keywords)
            # 저장할 데이터 구성
            data_to_store = {
                "time": current_timestamp,
                "title": record["title"],
                "url": record["url"],
                "company": record["company"]
            }
            if work_type:
                data_to_store["workType"] = work_type
            
            # Firebase에 저장
            ref.child(record_key).set(data_to_store)
            logging.info(f"저장 완료 - KEY: {record_key}, 제목: {record['title']}, URL: {record['url']}")
            
            # 키워드 매칭이 된 경우에만 디스코드 알림 전송
            if work_type:
                discord_message = f"""
📝새로운 추천채용 공고 (키워드 매칭됨)
회사: {record['company']}
제목: {record['title']}
URL: {record['url']}
"""
                send_discord_alert(discord_message)
            
            # 연속 요청 시 서버 부하 방지를 위해 잠시 대기
            time.sleep(1)
        else:
            logging.info(f"이미 저장된 게시글 - KEY: {record_key}")

def main():
    """
    5분마다 새로운 게시글이 있는지 확인하고,
    Firebase에 저장 및 디스코드 알림 전송을 수행합니다.
    """
    while True:
        data_list = fetch_work_recommend()
        if data_list:
            logging.info("추출된 데이터:")
            for record in data_list:
                logging.info(record)
            store_data_to_firebase(data_list)
        else:
            logging.warning("데이터를 추출하지 못했습니다.")
        
        logging.info("5분 대기 중...")
        time.sleep(300)

if __name__ == "__main__":
    main()
