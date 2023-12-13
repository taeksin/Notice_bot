import os
import sys
import time
import requests
from notice import Notice
from http.client import HTTPException
from bs4 import BeautifulSoup
# from module import notice_module

# firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# smtp (e-mail)
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# 

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

Hansung_BASE_URL = "https://www.hansung.ac.kr/"
Hansung_REQUEST_URL = Hansung_BASE_URL + "hansung/8385/subview.do"

#Firebase database 인증 및 앱 초기화
cred = credentials.Certificate('mykey.json')
firebase_admin.initialize_app(cred,{
    'databaseURL' : 'https://mango-project-e71fa-default-rtdb.firebaseio.com/' 
})

# ref = db.reference("Notice_List/Hansung_Notice") #db 위치 지정, 기본 가장 상단을 가르킴
# ref.update({'URL1' : 'Title1'}) #해당 변수가 없으면 생성한다.
# ref.update({'URL2' : 'Title2'}) #해당 변수가 없으면 생성한다.

# #리스트 전송시
# ref = db.reference() #db 위치 지정
# ref.update({'수강자' : ['구독자A','구독자B','구독자C','구독자D']})

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


def Hansung_scrapeNotices() -> list[Notice]:
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
        url = Hansung_BASE_URL + href.removeprefix("/")
        result.append(Notice(id, title, url))
        if result.__len__() == 10:
            break

    return result


def Hansung_find_new_post(std):
    with open("Hansung_IDS.txt") as f:
        lines = f.read().splitlines()
    print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
    print(lines)
    print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
    count = 0
    for line in lines:
        # print("mmmmmmmmmmmmmmmmmmmmmmmm")
        # print(line)
        if int(std) < int(line):
            count = count+1
    return count

# std 새로고침
# std에는 새로고침 했을 당시에 제일 최신의 ID값
def Hansung_std_F5():
    f = open("Hansung_IDS.txt", 'r')
    std2 = f.readline()
    f.close()
    f = open("Hansung_std.txt", 'w')
    f.write(std2)
    f.close()


while True:
    f = open("Hansung_std.txt", 'r')
    Hansung_std = f.readline()
    f.close()

    Hansung_Result = Hansung_scrapeNotices()
    f = open("Hansung_IDS.txt", 'w')
    for it in Hansung_Result:
        f.write(it.id)
        f.write("\n")
        print("mㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
        # print(it.id)
    f.close()
    
    # 이메일 수신동의 한 이메일을 받아와서 저장
    Hansung_receivers = ['yoyo2521@naver.com','teaksin@gmail.com']
    Hansung_ref = db.reference('hansungemailref')
    a=Hansung_ref.get()
    # print(type(a)) #json형태로 받아와 진다.
    # print(a)
    # print(a["anafVevjAbaoEw7CA53N5zMKDC83"])
    # print(a["anafVevjAbaoEw7CA53N5zMKDC83"]["-Nd-_wHurgRcX_9-IxSh"])
    print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
    print(len(a))

    for key in a.keys():
        print(key)
        print(a[key])
        b=a[key]
        for kk in b.keys():
            print(b[kk])
            Hansung_receivers.append(b[kk])
    print(Hansung_receivers)
    print("1111111111111111")
    
    
    # print(testResult[0].title)
    # print(testResult[0].id)
    # print(testResult[0].url)
    Hansung_index = Hansung_find_new_post(Hansung_std)
    # std_F5()
    if Hansung_index > 0:
        for i in reversed(range(int(Hansung_index))):
            Hansung_notice_title=str(Hansung_Result[i].title)
            Hansung_notice_url=str(Hansung_Result[i].url)
            Hansung_to_email = "yoyo2521@naver.com"
            Hansung_subject = "🔴📝 NEW 공지 📝🔴"
            Hansung_message = "한성대학교 NEW 공지가 올라왔습니다.\n"+Hansung_notice_title+"\n"+Hansung_notice_url

            # smtp messege
            Hansung_msg = MIMEMultipart()
            Hansung_msg["From"] = from_email
            Hansung_msg["To"] = ', '.join(Hansung_receivers)#수신 메일 리스트를 문자열로 변환 (,와 한칸 공백을 추가해서 구분)
            Hansung_msg["Subject"] = Hansung_subject
            Hansung_msg.attach(MIMEText(Hansung_message, "plain"))

            # sendmail
            server.sendmail(from_email, Hansung_receivers, Hansung_msg.as_string())
            
            # message = '\n\n[🔴📝 NEW 공지 📝🔴]'
            # message = message + '\n\n['+testResult[i].title+']'
            # # message = message + '\n['+testResult[i].url+']'
            # notice_module.send_telegram_message(message)
            
            
            time.sleep(2)
            print(Hansung_Result[i].title)
            print(Hansung_Result[i].url)
            
            # DB에 저장 
            Hansung_ref = db.reference("Notice_List/Hansung_Notice/ID_Title") #db 위치 지정, 기본 가장 상단을 가르킴
            Hansung_ref.update({Hansung_Result[i].id : Hansung_Result[i].title}) #해당 변수가 없으면 생성한다.
            Hansung_ref = db.reference("Notice_List/Hansung_Notice/ID_URL") #db 위치 지정, 기본 가장 상단을 가르킴
            Hansung_ref.update({Hansung_Result[i].id : Hansung_Result[i].url}) #해당 변수가 없으면 생성한다.
            
            
        Hansung_std_F5()
    else:
        print("새로운 게시물이 없다")
    
server.quit()