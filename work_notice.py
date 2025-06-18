import os
import time
import requests
import yaml
import logging
import asyncio
import aiohttp
from datetime import datetime
from bs4 import BeautifulSoup
from logging.handlers import TimedRotatingFileHandler
from pg_config_connect import get_pg_pool

# ---------------------------
# 사용자 정의 날짜 기반 FileHandler
# ---------------------------
class DateBasedFileHandler(logging.FileHandler):
    def __init__(self, directory, filename_format, encoding=None, delay=False):
        self.directory = directory
        self.filename_format = filename_format
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
# 로그 설정
# ---------------------------
log_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

file_handler = DateBasedFileHandler("log", "{date}_work.log", encoding="utf-8")
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# ---------------------------
# 설정 로드
# ---------------------------
with open('config.yaml', encoding='UTF-8') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
DISCORD_WEBHOOK_URL = config['DISCORD_WEBHOOK_URL']

# ---------------------------
# 키워드 DB 조회 함수
# ---------------------------
async def get_keywords():
    pool = await get_pg_pool()
    try:
        keywords_list = await pool.fetch("SELECT keyword FROM notice_bot.work_keywords")
        keywords_list = [row['keyword'].lower() for row in keywords_list]
        logging.info(f"DB에서 가져온 키워드: {keywords_list}")
        return keywords_list
    finally:
        await pool.close()

# ---------------------------
# 디스코드 웹훅 전송
# ---------------------------
async def send_discord_alert(message_content):
    message = {"content": message_content}
    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_WEBHOOK_URL, data=message) as response:
            if response.status not in (200, 204):
                logging.error(f"디스코드 웹훅 전송 실패: {response.status}")
            else:
                logging.info("디스코드 웹훅 전송 성공")

# ---------------------------
# 채용 정보 크롤링
# ---------------------------
async def fetch_work_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                logging.error(f"URL 요청 실패, 상태 코드: {response.status} / URL: {url}")
                return []
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            table_ul = soup.find('ul', {'data-role': 'table', 'class': 'black'})
            if not table_ul:
                logging.error("지정한 테이블 요소를 찾을 수 없습니다.")
                return []

            tbody_items = table_ul.select("li.tbody, li.tbody.notice")
            data_list = []

            for item in tbody_items:
                loopnum_tag = item.find('span', class_='loopnum')
                if not loopnum_tag:
                    continue
                record_id = loopnum_tag.get_text(strip=True)
                org_span = item.find('span', class_='org')
                company_text = org_span.get_text(strip=True) if org_span else ""
                title_span = item.find('span', class_='title')
                if title_span:
                    a_tag = title_span.find('a')
                    if a_tag:
                        href = a_tag.get('href')
                        full_url = href if href.startswith("http") else "https://career.hansung.ac.kr" + href
                        title_text = a_tag.get_text(strip=True)
                    else:
                        full_url, title_text = "", ""
                else:
                    full_url, title_text = "", ""
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

async def fetch_work_recommend():
    return await fetch_work_data("https://career.hansung.ac.kr/ko/recruitment/recommend")

async def fetch_work_general():
    return await fetch_work_data("https://career.hansung.ac.kr/ko/recruitment/general")

# ---------------------------
# 키워드 검사 및 DB 저장
# ---------------------------
async def check_work_type(url, keywords):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logging.error(f"게시글 URL 요청 실패 (상태 코드: {response.status})")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
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

async def store_data_to_db(data_list, table_name):
    pool = await get_pg_pool()
    try:
        current_timestamp = datetime.now()
        keywords = await get_keywords()

        for record in data_list:
            record_key = f"{record['id']}_{record['company']}" if record['company'] else record['id']
            
            # 이미 저장된 게시글인지 확인
            row = await pool.fetchrow(f"SELECT 1 FROM notice_bot.{table_name} WHERE record_key = $1", record_key)
            if row:
                logging.info(f"이미 저장된 게시글 - KEY: {record_key}")
                continue

            # 게시글 타입 확인
            work_type = await check_work_type(record["url"], keywords=keywords)
            
            # 데이터 삽입
            await pool.execute(f"""
                INSERT INTO notice_bot.{table_name} (record_key, time, title, url, company, deadline, work_type)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, record_key, current_timestamp, record["title"], record["url"], record["company"], record["deadline"], work_type)

            logging.info(f"저장 완료 - KEY: {record_key}, 제목: {record['title']}, URL: {record['url']}")

            # 개발자 관련 공고인 경우 디스코드 알림
            if work_type:
                header = "📝🟢새로운 추천채용 공고" if "recommend" in record["url"] else "📝🔵새로운 일반채용 공고"
                discord_message = f"""
{header}
회사: {record['company']}
제목: {record['title']}
마감일: {record['deadline']}
URL: {record['url']}
"""
                await send_discord_alert(discord_message)
                await asyncio.sleep(1)
    finally:
        await pool.close()

# ---------------------------
# 메인 실행
# ---------------------------
async def main_async():
    while True:
        # 추천 채용 페이지 크롤링
        recommend_list = await fetch_work_recommend()
        if recommend_list:
            logging.info("추천 채용 페이지 - 추출된 데이터:")
            for record in recommend_list:
                logging.info(record)
            await store_data_to_db(recommend_list, 'work_recommend')
        else:
            logging.warning("추천 채용 페이지 데이터를 추출하지 못했습니다.")

        # 일반 채용 페이지 크롤링
        general_list = await fetch_work_general()
        if general_list:
            logging.info("일반 채용 페이지 - 추출된 데이터:")
            for record in general_list:
                logging.info(record)
            await store_data_to_db(general_list, 'work_general')
        else:
            logging.warning("일반 채용 페이지 데이터를 추출하지 못했습니다.")

        logging.info("5분 대기 중...")
        await asyncio.sleep(300)

def main():
    # 비동기 메인 함수 실행
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
