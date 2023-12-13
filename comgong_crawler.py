import os
import sys
import time
import requests
from notice import Notice
from http.client import HTTPException
from bs4 import BeautifulSoup

# firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# smtp (e-mail)
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

BASE_URL = "http://cse.hansung.ac.kr/"
REQUEST_URL = BASE_URL + "news?searchCondition"

#Firebase database 인증 및 앱 초기화
cred = credentials.Certificate('mykey.json')
firebase_admin.initialize_app(cred,{
    'databaseURL' : 'https://mango-project-e71fa-default-rtdb.firebaseio.com/' 
})

# smtp 변수
from_email = "booogiii12@gmail.com"
password = "pdbksfjyoqrqvwew"
# --------------------------
to_email = "yoyo2521@naver.com"
subject = "Your Subject"
message = "Your message goes here."

# smtp messege
msg = MIMEMultipart()
msg["From"] = from_email
msg["To"] = to_email
msg["Subject"] = subject
msg.attach(MIMEText(message, "plain"))

# connect server
server = smtplib.SMTP("smtp.gmail.com", 587)  # Use appropriate SMTP server and port
server.starttls()  # Encrypt the connection
server.login(from_email, password)

# href를 id로 변환
def extractNumberFrom(string: str) -> int:
    return int(''.join(filter(str.isdigit, string)))


def scrapeNotices() -> list[Notice]:
    r"""
    한성대학교 전체 공지사항 첫 페이지를 헤더 공지를 제외하고 스크래핑하여 :class:`notice` 리스트를 반환한다.

    `BASE_URL`이 잘못된 경우 :class:`HTTPException`을 raise한다.
    """

    try:
        response = requests.get(REQUEST_URL)
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
        
        subject=a_tag.text
        href = a_tag['href']
        
        
        id = str(extractNumberFrom(href))
        title = subject.strip()
        url = BASE_URL + href.removeprefix("/")
        result.append(Notice(id, title, url))
        if result.__len__() == 10:
            break
    
    return result

# 새로운 공지가 몇 개 인지 카운트
def find_new_post(cstd):
    with open("cIDS.txt") as f:
        lines = f.read().splitlines()
    print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
    print(lines)
    print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
    count = 0
    for line in lines:
        # print("mmmmmmmmmmmmmmmmmmmmmmmm")
        # print(line)
        if int(cstd) < int(line):
            count = count+1
    return count

# std 새로고침
# std에는 새로고침 했을 당시에 제일 최신의 ID값
def cstd_F5():
    f = open("cIDS.txt", 'r')
    cstd2 = f.readline()
    f.close()
    f = open("cstd.txt", 'w')
    f.write(cstd2)
    f.close()


    

while True:

    f = open("cstd.txt", 'r')
    cstd = f.readline()
    f.close()
    testResult = scrapeNotices()
    
    f = open("cIDS.txt", 'w')
    for it in testResult:
        f.write(it.id)
        f.write("\n")
        print("mㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
        # print(it.id)
    f.close()
    
    # 이메일 수신동의 한 이메일을 받아와서 저장
    receivers = ['yoyo2521@naver.com','teaksin@gmail.com']
    ref = db.reference('computeremailref')
    a=ref.get()
    
    for k in a.keys():
        print(k)
        print(a[k])
        b=a[k]
        for kk in b.keys():
            print(b[kk])
            receivers.append(b[kk])
    print(receivers)
    print("1111111111111111")
    
    # print(testResult[0].title)
    # print(testResult[0].id)
    # print(testResult[0].url)
    index = find_new_post(cstd)
    # cstd_F5()
    if index > 0:
        for i in reversed(range(int(index))):
            notice_title=str(testResult[i].title)
            notice_url=str(testResult[i].url)
            to_email = "yoyo2521@naver.com"
            subject = "🔴📝 NEW 공지 📝🔴"
            message = "새로운 공지 올라왔어\n"+notice_title+"\n"+notice_url
            
            # smtp messege
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = ', '.join(receivers)#수신 메일 리스트를 문자열로 변환 (,와 한칸 공백을 추가해서 구분)
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain"))

            # sendmail
            server.sendmail(from_email, receivers, msg.as_string())
            
            time.sleep(2)
            print(testResult[i].title)
            print(testResult[i].url)
        
        cstd_F5()
    else:
        print("새로운 게시물이 없다")
        time.sleep(500)

server.quit()