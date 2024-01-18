import os
import sys
import time
import requests
from notice import Notice
from http.client import HTTPException
from bs4 import BeautifulSoup
from module import notice_module
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

BASE_URL = "https://www.hansung.ac.kr/"
REQUEST_URL = BASE_URL + "hansung/8385/subview.do"

# href를 id로 변환


def extractNumberFrom(string: str):
    return int(''.join(filter(str.isdigit, string)))


def scrapeNotices():
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
    tableRows = soup.select('tbody>tr')
    for tableRow in tableRows:
        # 헤더 공지 혹은 블라인드 처리된 공지는 건너뛴다.
        if any(className in tableRow.attrs['class'] for className in ['notice', 'blind']):
            continue

        subject = tableRow.select_one('.td-subject > a[href]')
        href = subject['href']

        id = str(extractNumberFrom(href))
        title = subject.text.strip()
        url = BASE_URL + href.removeprefix("/")
        result.append(Notice(id, title, url))
        if result.__len__() == 10:
            break

    return result


def find_new_post(std):
    with open("IDS.txt") as f:
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


def std_F5():
    f = open("IDS.txt", 'r')
    std2 = f.readline()
    f.close()
    f = open("std.txt", 'w')
    f.write(std2)
    f.close()


while True:

    f = open("std.txt", 'r')
    std = f.readline()
    f.close()

    testResult = scrapeNotices()
    f = open("IDS.txt", 'w')
    for it in testResult:
        f.write(it.id)
        f.write("\n")
        print("mㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ")
        # print(it.id)
    f.close()
    # print(testResult[0].title)
    # print(testResult[0].id)
    # print(testResult[0].url)
    index = find_new_post(std)
    # std_F5()
    if index > 0:
        for i in reversed(range(int(index))):
            message = '\n\n[🔴📝 NEW 공지 📝🔴]'
            message = message + '\n\n['+testResult[i].title + ']'
            message = message + '\n['+testResult[i].url + ']'
            notice_module.send_telegram_message(message)
            time.sleep(2)
            print(testResult[i].title)
            print(testResult[i].url)
        std_F5()
    else:
        print("새로운 게시물이 없다")
