from bs4 import BeautifulSoup
import requests

BASE_URL = "http://cse.hansung.ac.kr/"
REQUEST_URL = BASE_URL + "news?searchCondition"


response = requests.get(REQUEST_URL)
html = response.text
soup = BeautifulSoup(html, 'html.parser')

# tbody 태그 아래의 a 태그에 접근
a_tags = soup.select('tbody a')  # tbody 태그 아래의 모든 a 태그 선택
for a_tag in a_tags[-10:]:
    print(a_tag['href'])  # 예시: a 태그의 href 속성 값 출력
    print(a_tag.text)
