import feedparser
import os
import sys
import time
import datetime
from decimal import Decimal
from datetime import timedelta
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from module import notice_module
# ┌ ┐└ ┘
urls='https://www.hansung.ac.kr/bbs/hansung/143/rssList.do?row=50'
d=feedparser.parse(urls)
pub_time=[]
title=[]
link=[]
def make_list(pub_time,title,link):
    # ┌ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ리스트 새로고침ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ┐
    for _ in range(10):
        pub_time.append(cvt_datetime(d.entries[_].published))
        title.append(d.entries[_].title)
        link.append(d.entries[_].link)
    # print(f'pub_time {pub_time}\n')
    # print(f'title은 {title}\n')
    # print(f'link은 {link}\n')
    # └ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ리스트 새로고침ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ┘
def cvt_datetime(obj):
    obj_time=datetime.strptime(obj, "%Y-%m-%d %H:%M:%S.%f")
    return obj_time

# 프로그램 시작 메세지 발송
message = '\n\n[🟣🟣 시작 안내 🟣🟣]'
message = message + '\n\n notice_bot 시작! '
message = message + '\n\n- 현재시간:' + str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
# 프로그램 시작 메세지 발송
notice_module.send_telegram_message(message)

# if문에서 시간 비교할때 사용해야함
std_post_time= d.entries[3].published    #코드 다짜면 생각좀 해보자 0으로 할지 1로할지
std_post_time=cvt_datetime(std_post_time)
print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
make_list(pub_time,title,link)      # 리스트 새로고침
print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
now = datetime.now()
while True:
    try:
        d=feedparser.parse(urls)    # 주소 새로고침해서 가져오기
        make_list(pub_time,title,link)      # 리스트 새로고침
        
        # ┌ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ 시 간 ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ┐
        now = datetime.now()
        recent_post_time= d.entries[0].published
        recent_post_time=cvt_datetime(recent_post_time)
        # NEW POST 등록 된 경우
        print(f'if문은 {std_post_time < recent_post_time < now}')
        if std_post_time < recent_post_time < now:
            # for문 안에서 new_post가 몇개인지 분석하기 인덱스번호 추출
            num=pub_time.index(std_post_time)
            print("공지가 등록되었습니다. 메시지 보낼게요!")
            for i in reversed(range(num)):
                print("ㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁ")
                print(title[i])
                print(link[i])
                print(pub_time[i])
                print("ㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁㅁ")
                message = '\n\n[🔴📝 새로운 공지사항 📝🔴]'
                message = message +'\n\n['+title[i]+']'
                message = message + '\n['+link[i]+']'
                message = message + '\n[ 등록시간 : '+str(pub_time[i])+']'
                notice_module.send_telegram_message(message)
            # 텔레그램 전송
            std_post_time=recent_post_time
        else:
            print("새로운 공지가 없음")
        time.sleep(300)   # 코드 완성하면 300으로 바꾸기
        # └ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ 시 간 ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ┘
        
    except KeyboardInterrupt:
        # 프로그램 종료 메세지 조립
        message = '\n\n[🚨❌🚨종료🚨❌🚨]'
        message = message + '\n\n notice_bot 종료!'
        message = message + '\n\n KeyboardInterrupt Exception 발생!'
        message = message + '\n\n- 현재시간:' + str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
        
        # # 프로그램 종료 메세지 발송
        notice_module.send_telegram_message(message)
        # logging.error("KeyboardInterrupt Exception 발생!")
        # logging.error(traceback.format_exc())
        sys.exit(-100)

    except Exception:
        # 프로그램 종료 메세지 조립
        message = '\n\n[🚨❌🚨종료🚨❌🚨]'
        message = message + '\n\n notice_bot 종료!'
        message = message + '\n\n Exception 발생!'
        message = message + '\n\n- 현재시간:' + str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
        
        # # 프로그램 종료 메세지 발송
        notice_module.send_telegram_message(message)
        # logging.error("Exception 발생!")
        # logging.error(traceback.format_exc())
        sys.exit(-200)

# import requests
# import sys
# import os
# from bs4 import BeautifulSoup
# # sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# # from module import notice_module

# keyword="비교과"
# url="https://www.hansung.ac.kr/hansung/8385/subview.do?enc=Zm5jdDF8QEB8JTJGYmJzJTJGaGFuc3VuZyUyRjE0MyUyRmFydGNsTGlzdC5kbyUzRmJic0NsU2VxJTNEMjM5JTI2YmJzT3BlbldyZFNlcSUzRCUyNmlzVmlld01pbmUlM0RmYWxzZSUyNnNyY2hDb2x1bW4lM0RzaiUyNnNyY2hXcmQlM0QlMjY%3D"
# # 기준 숫자
# standard_num=1124
# r=requests.get(url)
# bs=BeautifulSoup(r.content, "html.parser")
# #atags=bs.select("td.td-num,a.strong")
# #atags=bs.select("strong") #제목 부르기는 strong태그의 text부르기
# trs=bs.select("tr")
# print(trs)
# tdn=bs.select("td.td-num") # td-num 리스트
# tds=bs.select("td.td-subject") # td-subject 리스트
# trs.find_all('span').decompose()
# print(trs[0])
# # 새로고침
# print(tdn[0])
# # for td in tdn:
# #     nnum=td.text
# #     print(nnum)
# #     print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ\n")
# # print(nnum)



