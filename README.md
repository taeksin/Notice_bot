
<img src="https://capsule-render.vercel.app/api?type=waving&color=54aeff&height=150&section=header" />


<body>

<h1>Notice Bot</h1>

<p>Notice Bot은 한성대학교 및 컴퓨터공학부의 공지사항을 실시간으로 디스코드로 전달해주는 봇입니다.</p>

<h2>주요 기능</h2>

<ul>
  <li>한성대학교 및 컴퓨터공학부의 공지사항을 크롤링하여 디스코드로 전송</li>
  <li>새로운 공지가 등록될 때마다 디스코드로 알림</li>
  <li>Firebase를 활용하여 공지사항의 정보를 저장 및 관리</li>
</ul>

<h2>사용된 기술 및 라이브러리</h2>

<ul>
  <li>Python</li>
  <li>BeautifulSoup: 웹 스크래핑을 위한 라이브러리</li>
  <li>Firebase: 데이터베이스로 사용하여 공지사항 정보를 저장</li>
  <li>Discord Webhook: 디스코드로 알림을 보내기 위한 기능</li>
</ul>

<h2>실행 화면</h2>

<img src="https://github.com/taeksin/Notice_bot/assets/90402009/cc3c578c-bc2a-48aa-8447-c221306d91e5" width="800" height="600" alt="Notice Bot">
<img src="https://github.com/taeksin/Notice_bot/assets/90402009/3c8d1a8f-b4c2-4cfc-afdf-40f034dd4724" width="800" height="600" alt="Notice Bot">
<img src="https://github.com/taeksin/Notice_bot/assets/90402009/d164dcd5-15db-4cf7-b140-78bac3516e37" width="800" height="1000" alt="Notice Bot">

<h2>프로젝트 구조</h2>

<ul>
  <li><code>notice.py</code>: Notice 클래스 정의</li>
  <li><code>config.yaml</code>: 설정 파일</li>
  <li><code>server_multi_crawler3.py</code>: 크롤링 및 디스코드 알림 처리</li>
</ul>

<h2>설정 방법</h2>

<ol>
  <li><code>config.yaml</code> 파일을 열어서 <code>DISCORD_WEBHOOK_URL</code>에 디스코드 웹훅 URL을 입력하세요.</li>
  <li><code>notice_bot.json</code> 파일에 Firebase 프로젝트의 인증 정보를 입력하세요.</li>
</ol>

<h2>사용 방법</h2>

<ol>
  <li>Python 3.x를 설치하세요.</li>
  <li>필요한 라이브러리를 설치하기 위해 터미널에서 다음 명령어를 실행하세요:
  <code> pip install requests beautifulsoup4 firebase-admin</code>
  </li>
  <li><code>server_multi_crawler3.py</code> 파일을 실행하세요:
    <code>python server_multi_crawler3.py</code>
  </li>
</ol>


<p>프로그램이 실행되면 주기적으로 한성대학교 및 컴퓨터공학부의 공지사항을 크롤링하여 디스코드로 알림을 보내줍니다.</p>

<h2>주의사항</h2>

<ul>
  <li>이 프로젝트는 개인적인 용도로 제작되었으며, 상업적인 목적으로 사용될 수 없습니다.</li>
  <li>공지사항 크롤링 시 서버에 부하를 줄 수 있으므로 적절한 주기로 실행하세요.</li>
  <li>코드 및 설정 파일에는 개인 정보가 포함되어 있으므로 공개 저장소에 올리기 전에 주의하세요.</li>
</ul>


<p>이 프로젝트는 개인 학습 및 흥미로 제작되었으며 어떠한 상황에서도 악용되어서는 안됩니다.</p>
</body>
</html>

<img src="https://capsule-render.vercel.app/api?type=waving&color=54aeff&height=150&section=footer" />
