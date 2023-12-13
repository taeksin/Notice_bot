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

Hansung_BASE_URL = "https://www.hansung.ac.kr/"
Hansung_REQUEST_URL = Hansung_BASE_URL + "hansung/8385/subview.do"
Computer_BASE_URL = "http://cse.hansung.ac.kr/"
Computer_REQUEST_URL = Computer_BASE_URL + "news?searchCondition"

#Firebase database 인증 및 앱 초기화
cred = credentials.Certificate('Boogikey.json')
firebase_admin.initialize_app(cred,{
    'databaseURL' : 'https://boogienotice-default-rtdb.firebaseio.com/' 
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
    print("id_list: "+str(lines))
    print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
    count = 0
    for line in lines:
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

def Computer_scrapeNotices() -> list[Notice]:
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
    print("id_list: "+str(lines))
    print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
    count = 0
    for line in lines:
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
    print("\n\n한성대 공지사항 크롤링을 시작합니다")
    f = open("Hansung_std.txt", 'r')
    Hansung_std = f.readline()
    f.close()

    Hansung_Result = Hansung_scrapeNotices()
    f = open("Hansung_IDS.txt", 'w')
    for it in Hansung_Result:
        f.write(it.id)
        f.write("\n")
    f.close()
    
    # 이메일 수신동의 한 이메일을 받아와서 저장
    Hansung_receivers = ['yoyo2521@naver.com','teaksin@gmail.com']
    Hansung_ref = db.reference('hansungemailref')
    a=Hansung_ref.get()
    # print(type(a)) #json형태로 받아와 진다.
    # print(a)
    # print(a["anafVevjAbaoEw7CA53N5zMKDC83"])
    # print(a["anafVevjAbaoEw7CA53N5zMKDC83"]["-Nd-_wHurgRcX_9-IxSh"])

    for key in a.keys():
        # print(key)
        # print(a[key])
        b=a[key]
        for kk in b.keys():
            # print(b[kk])
            Hansung_receivers.append(b[kk])
    print("    Hansung_receivers: "+str(len(Hansung_receivers))+"명\n    "+str(Hansung_receivers))
    
    
    # print(testResult[0].title)
    # print(testResult[0].id)
    # print(testResult[0].url)
    Hansung_index = Hansung_find_new_post(Hansung_std)
    print("새로운 공지 개수 : "+str(Hansung_index)+"개")
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
            
            time.sleep(2)
            print(Hansung_Result[i].title)
            print(Hansung_Result[i].url)
            
            # DB에 저장 
            Hansung_ref = db.reference("Notice_List/Hansung_Notice/ID_Title") #db 위치 지정, 기본 가장 상단을 가르킴
            Hansung_ref.update({Hansung_Result[i].id : Hansung_Result[i].title}) #해당 변수가 없으면 생성한다.
            Hansung_ref = db.reference("Notice_List/Hansung_Notice/ID_URL") #db 위치 지정, 기본 가장 상단을 가르킴
            Hansung_ref.update({Hansung_Result[i].id : Hansung_Result[i].url}) #해당 변수가 없으면 생성한다.
            print("->이메일 알림  및  DB 저장 완료\n")
        Hansung_std_F5()
    else:
        print("한성대 New 공지가 없다")
    time.sleep(2)
    
    print("\n\n컴공 공지사항 크롤링을 시작합니다")
    f = open("Computer_std.txt", 'r')
    Computer_std = f.readline()
    f.close()
    Computer_Result = Computer_scrapeNotices()
    
    f = open("Computer_IDS.txt", 'w')
    for it in Computer_Result:
        f.write(it.id)
        f.write("\n")
    f.close()
    
    # 이메일 수신동의 한 이메일을 받아와서 저장
    Computer_receivers = ['yoyo2521@naver.com','teaksin@gmail.com']
    Computer_ref = db.reference('computeremailref')
    a=Computer_ref.get()
    
    for key in a.keys():
        # print(key)
        # print(a[key])
        b=a[key]
        for kk in b.keys():
            # print(b[kk])
            Computer_receivers.append(b[kk])
    print("Computer_receivers: "+str(len(Computer_receivers))+"명\n"+str(Computer_receivers))
    
    # print(testResult[0].title)
    # print(testResult[0].id)
    # print(testResult[0].url)
    Computer_index = Computer_find_new_post(Computer_std)
    print("새로운 공지 개수 : "+str(Computer_index)+"개")
    # cstd_F5()
    if Computer_index > 0:
        for i in reversed(range(int(Computer_index))):
            Computer_notice_title=str(Computer_Result[i].title)
            Computer_notice_url=str(Computer_Result[i].url)
            Computer_to_email = "yoyo2521@naver.com"
            Computer_subject = "🟢📝 NEW 공지 📝🟢"
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
            
            # DB에 저장 
            Computer_ref = db.reference("Notice_List/Computer_Notice/ID_Title") #db 위치 지정, 기본 가장 상단을 가르킴
            Computer_ref.update({Hansung_Result[i].id : Hansung_Result[i].title}) #해당 변수가 없으면 생성한다.
            Computer_ref = db.reference("Notice_List/Computer_Notice/ID_URL") #db 위치 지정, 기본 가장 상단을 가르킴
            Computer_ref.update({Hansung_Result[i].id : Hansung_Result[i].url}) #해당 변수가 없으면 생성한다.
            print("->이메일 알림  및  DB 저장 완료\n")
        
        Computer_std_F5()
    else:
        print("컴공 New 공지가 없다")
    print("300초 대기를 시작합니다")
    time.sleep(300)
    
    
server.quit()