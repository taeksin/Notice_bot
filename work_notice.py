import os
import time
import requests
import yaml
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from logging.handlers import TimedRotatingFileHandler

# ---------------------------
# 사용자 정의 날짜 기반 FileHandler
# ---------------------------
class DateBasedFileHandler(logging.FileHandler):
    """
    현재 날짜를 기준으로 파일명을 생성하여 로그를 기록합니다.
    파일명 형식은 filename_format에 지정된 형식({date}_work.log)으로 생성됩니다.
    날짜가 바뀌면 자동으로 새 파일을 열어 기록합니다.
    """
    def __init__(self, directory, filename_format, encoding=None, delay=False):
        self.directory = directory
        self.filename_format = filename_format  # 예: "{date}_work.log"
        self.current_date = datetime.now().strftime("%Y_%m_%d")
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        filename = os.path.join(self.directory, self.filename_format.format(date=self.current_date))
        super().__init__(filename, mode="a", encoding=encoding, delay=delay)

    def emit(self, record):
        new_date = datetime.now().strftime("%Y_%m_%d")
        if new_date != self.current_date:
            self.current_date = new_date
            self.acquire()
            try:
                self.close()
                new_filename = os.path.join(self.directory, self.filename_format.format(date=new_date))
                self.baseFilename = os.path.abspath(new_filename)
                self.stream = self._open()
            finally:
                self.release()
        super().emit(record)

# ---------------------------
# 로그 설정 (log 폴더 내 날짜별 로그 파일: {YYYY_MM_DD}_work.log)
# ---------------------------
log_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 콘솔 핸들러
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# 날짜 기반 파일 핸들러 (log 폴더에 {YYYY_MM_DD}_work.log 로 생성)
file_handler = DateBasedFileHandler("log", "{date}_work.log", encoding="utf-8")
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# ---------------------------
# Firebase 초기화 및 설정
# ---------------------------
import firebase_admin
from firebase_admin import credentials, db

with open('config.yaml', encoding='UTF-8') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
FIREBASE_DB_URL = config['FIREBASE_DB_URL']
DISCORD_WEBHOOK_URL = config['DISCORD_WEBHOOK_URL']

cred = credentials.Certificate('notice_bot.json')
firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})

# ---------------------------
# 함수 정의
# ---------------------------
def get_keywords():
    """
    Firebase의 '/Notice_List/Work_Notice/Keyword' 경로에서 키워드를 가져옵니다.
    데이터가 리스트 형태일 경우 각 문자열을 소문자로 변환하여 리스트로 반환합니다.
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

def fetch_work_data(url):
    """
    지정한 URL에서 채용 게시글 정보를 추출합니다.
    추출하는 정보는 ID, 회사, 제목, URL, 그리고 마감일(deadline)입니다.
    li 요소 선택 시 class가 "tbody" 또는 "tbody notice" 모두 사용합니다.
    """
    response = requests.get(url)
    if response.status_code != 200:
        logging.error(f"URL 요청 실패, 상태 코드: {response.status_code} / URL: {url}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    table_ul = soup.find('ul', {'data-role': 'table', 'class': 'black'})
    if not table_ul:
        logging.error("지정한 테이블 요소를 찾을 수 없습니다.")
        return []
    
    # li.tbody와 li.tbody.notice 모두 선택
    tbody_items = table_ul.select("li.tbody, li.tbody.notice")
    data_list = []
    
    for item in tbody_items:
        # ID 추출
        loopnum_tag = item.find('span', class_='loopnum')
        if not loopnum_tag:
            continue
        record_id = loopnum_tag.get_text(strip=True)
        
        # 회사명 추출
        org_span = item.find('span', class_='org')
        company_text = org_span.get_text(strip=True) if org_span else ""
        
        # title과 url 추출
        title_span = item.find('span', class_='title')
        if title_span:
            a_tag = title_span.find('a')
            if a_tag:
                href = a_tag.get('href')
                if href.startswith("http"):
                    full_url = href
                else:
                    full_url = "https://career.hansung.ac.kr" + href
                title_text = a_tag.get_text(strip=True)
            else:
                full_url, title_text = "", ""
        else:
            full_url, title_text = "", ""
        
        # 마감일(deadline) 추출 (없으면 빈 문자열)
        deadline_span = item.find('span', class_='deadline center')
        deadline_text = deadline_span.get_text(strip=True) if deadline_span else ""
        
        data_list.append({
            "id": record_id,
            "company": company_text,
            "title": title_text,
            "url": full_url,
            "deadline": deadline_text
        })
    
    return data_list

def fetch_work_recommend():
    """추천 채용 페이지에서 데이터를 추출합니다."""
    url = "https://career.hansung.ac.kr/ko/recruitment/recommend"
    return fetch_work_data(url)

def fetch_work_general():
    """일반 채용 페이지에서 데이터를 추출합니다."""
    url = "https://career.hansung.ac.kr/ko/recruitment/general"
    return fetch_work_data(url)

def check_work_type(url, keywords):
    """
    게시글 URL을 방문하여 data-role="post" 요소 내 텍스트에서 
    지정된 키워드(소문자로 변환한 상태)가 존재하는지 확인합니다.
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
            content_text = post_article.get_text().lower()
            for keyword in keywords:
                if keyword in content_text:
                    return "developer"
        return None
    except Exception as e:
        logging.error(f"게시글 처리 중 에러 발생: {e}")
        return None

def store_data_to_firebase(data_list, ref_path):
    """
    추출한 게시글 중 DB에 없는 항목을 Firebase에 저장합니다.
    저장 시, 게시글 URL을 방문하여 키워드가 존재하면 workType을 'developer'로 설정하며,
    키워드가 매칭될 때만 디스코드 알림을 전송합니다.
    
    저장 경로(ref_path)는 추천 채용과 일반 채용에 따라 다르게 지정됩니다.
    """
    ref = db.reference(ref_path)
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    firebase_keywords = get_keywords()
    
    for record in data_list:
        record_key = f"{record['id']}_{record['company']}" if record['company'] else record['id']
        existing_record = ref.child(record_key).get()
        if not existing_record:
            work_type = check_work_type(record["url"], keywords=firebase_keywords)
            data_to_store = {
                "time": current_timestamp,
                "title": record["title"],
                "url": record["url"],
                "company": record["company"],
                "deadline": record["deadline"]
            }
            if work_type:
                data_to_store["workType"] = work_type
            
            ref.child(record_key).set(data_to_store)
            logging.info(f"저장 완료 - KEY: {record_key}, 제목: {record['title']}, URL: {record['url']}")
            
            if work_type:
                # 채용 유형에 따른 메시지 헤더 결정
                if "recommend" in record["url"]:
                    header = "📝🟢새로운 추천채용 공고"
                else:
                    header = "📝🔵새로운 일반채용 공고"
                discord_message = f"""
{header}
회사: {record['company']}
제목: {record['title']}
마감일: {record['deadline']}
URL: {record['url']}
"""
                send_discord_alert(discord_message)
            
            time.sleep(1)
        else:
            logging.info(f"이미 저장된 게시글 - KEY: {record_key}")

def main():
    """
    5분마다 추천 채용과 일반 채용 페이지에서 데이터를 추출하고,
    각각 지정된 Firebase 경로에 저장하며, 디스코드 알림 전송을 수행합니다.
    """
    while True:
        # 추천 채용 페이지 처리
        recommend_list = fetch_work_recommend()
        if recommend_list:
            logging.info("추천 채용 페이지 - 추출된 데이터:")
            for record in recommend_list:
                logging.info(record)
            store_data_to_firebase(recommend_list, '/Notice_List/Work_Notice/Work_Recommend')
        else:
            logging.warning("추천 채용 페이지 데이터를 추출하지 못했습니다.")
        
        # 일반 채용 페이지 처리
        general_list = fetch_work_general()
        if general_list:
            logging.info("일반 채용 페이지 - 추출된 데이터:")
            for record in general_list:
                logging.info(record)
            store_data_to_firebase(general_list, '/Notice_List/Work_Notice/Work_General')
        else:
            logging.warning("일반 채용 페이지 데이터를 추출하지 못했습니다.")
        
        logging.info("5분 대기 중...")
        time.sleep(300)

if __name__ == "__main__":
    main()
