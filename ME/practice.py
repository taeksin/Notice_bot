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

def make_list(pub_time1,title1,link1,d1):
    d1=feedparser.parse(urls)
    # ┌ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ리스트 새로고침ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ┐
    for _ in range(10):
        pub_time1.append(cvt_datetime(d1.entries[_].published))
        title1.append(d1.entries[_].title)
        link1.append(d1.entries[_].link)
    # └ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ리스트 새로고침ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ┘
    return pub_time1, title1, link1
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
print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
while True:
    try:
        d=feedparser.parse(urls)    # 주소 새로고침해서 가져오기
        pub_time,title,link=make_list(pub_time,title,link,d)      # 리스트 새로고침
        # ┌ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ 시 간 ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ┐
        now = datetime.now()
        recent_post_time=pub_time[0]
        # NEW POST 등록 된 게 있는지 없는지 판단
        if std_post_time.timestamp() < recent_post_time.timestamp() < now.timestamp():
            # for문 안에서 new_post가 몇개인지 분석하기 인덱스번호 추출
            num=pub_time.index(std_post_time)
            for i in reversed(range(int(num))):
                message = '\n\n[🔴📝 NEW 공지 📝🔴]'
                message = message +'\n\n['+title[i]+']'
                message = message + '\n['+link[i]+']'
                message = message + '\n[ 등록시간 : '+str(pub_time[i])+']'
                notice_module.send_telegram_message(message)
            std_post_time=recent_post_time
        else:
            print("새로운 공지가 없음 - "+str(now.strftime('%Y-%m-%d %H:%M:%S')))
        time.sleep(5)   # 코드 완성하면 300으로 바꾸기
        # └ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ 시 간 ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ┘
        
    except KeyboardInterrupt:
        # 프로그램 종료 메세지 조립
        message = '\n\n[🚨❌🚨notice_bot 종료🚨❌🚨]'
        message = message + '\n\n KeyboardInterrupt Exception 발생!'
        message = message + '\n\n- 현재시간:' + str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
        
        # # 프로그램 종료 메세지 발송
        notice_module.send_telegram_message(message)
        sys.exit(-100)

    except Exception:
        # 프로그램 종료 메세지 조립
        message = '\n\n[🚨❌🚨notice_bot 종료🚨❌🚨]'
        message = message + '\n\n Exception !'
        message = message + '\n\n- 현재시간:' + str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
        
        # # 프로그램 종료 메세지 발송
        notice_module.send_telegram_message(message)
        sys.exit(-200)
