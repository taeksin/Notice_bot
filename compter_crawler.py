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

Computer_BASE_URL = "http://cse.hansung.ac.kr/"
Computer_REQUEST_URL = Computer_BASE_URL + "news?searchCondition"

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


def Computer_scrapeNotices() -> list[Notice]:
    r"""
    한성대학교 전체 공지사항 첫 페이지를 헤더 공지를 제외하고 스크래핑하여 :class:`notice` 리스트를 반환한다.

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
        
        subject=a_tag.text
        href = a_tag['href']
        
        
        id = str(extractNumberFrom(href))
        title = subject.strip()
        url = Computer_BASE_URL + href.removeprefix("/")
        result.append(Notice(id, title, url))
        if result.__len__() == 10:
            break
    
    return result

# 새로운 공지가 몇 개 인지 카운트
def Computer_find_new_post(Computer_std):
    with open("Computer_IDS.txt") as f:
        lines = f.read().splitlines()
    print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
    print(lines)
    print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
    count = 0
    for line in lines:
        # print("mmmmmmmmmmmmmmmmmmmmmmmm")
        # print(line)
        if int(Computer_std) < int(line):
            count = count+1
    return count

# std 새로고침
# std에는 새로고침 했을 당시에 제일 최신의 ID값
def Computer_std_F5():
    f = open("Computer_IDS.txt", 'r')
    std2 = f.readline()
    f.close()
    f = open("Computer_std.txt", 'w')
    f.write(std2)
    f.close()


    

while True:
    f = open("Computer_std.txt", 'r')
    Computer_std = f.readline()
    f.close()
    Computer_Result = Computer_scrapeNotices()
    
    f = open("Computer_IDS.txt", 'w')
    for it in Computer_Result:
        f.write(it.id)
        f.write("\n")
        print("mㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
        # print(it.id)
    f.close()
    
    # 이메일 수신동의 한 이메일을 받아와서 저장
    Computer_receivers = ['yoyo2521@naver.com','teaksin@gmail.com']
    Computer_ref = db.reference('computeremailref')
    a=Computer_ref.get()
    
    for key in a.keys():
        print(key)
        print(a[key])
        b=a[key]
        for kk in b.keys():
            print(b[kk])
            Computer_receivers.append(b[kk])
    print(Computer_receivers)
    print("1111111111111111")
    
    # print(testResult[0].title)
    # print(testResult[0].id)
    # print(testResult[0].url)
    Computer_index = Computer_find_new_post(Computer_std)
    # cstd_F5()
    if Computer_index > 0:
        for i in reversed(range(int(Computer_index))):
            Computer_notice_title=str(Computer_Result[i].title)
            Computer_notice_url=str(Computer_Result[i].url)
            Computer_to_email = "yoyo2521@naver.com"
            Computer_subject = "🔴📝 NEW 공지 📝🔴"
            Computer_message = "컴퓨터공학부 NEW 공지가 올라왔습니다.\n"+Computer_notice_title+"\n"+Computer_notice_url
            
            # smtp messege
            Computer_msg = MIMEMultipart()
            Computer_msg["From"] = from_email
            Computer_msg["To"] = ', '.join(Computer_receivers)#수신 메일 리스트를 문자열로 변환 (,와 한칸 공백을 추가해서 구분)
            Computer_msg["Subject"] = Computer_subject
            Computer_msg.attach(MIMEText(Computer_message, "plain"))

            # sendmail
            server.sendmail(from_email, Computer_receivers, Computer_msg.as_string())
            
            time.sleep(2)
            print(Computer_Result[i].title)
            print(Computer_Result[i].url)
        
        Computer_std_F5()
    else:
        print("새로운 게시물이 없다")
        time.sleep(500)

server.quit()