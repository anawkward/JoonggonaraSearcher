링크 : http://164.125.33.74:8008

# 중고나라 검색기 
실시간업데이트, 제목과 글 내용에 대한 필터링, 업자거르기, 서버에 db축적, 텔레그램으로 조건에 따른 알림 구현.

##
소스코드 등의 배포는 하지 않습니다. 참고자료로만 사용해주세요.
문의사항 : food1121@naver.com

## 중요 수정사항
1. 중고나라 검색기 v2.0 개발중이므로, v1.0 작동X.
2. 164.125.33.74:8008포트로 변경. ftp서버도 함께 운영중.


![JG_Demo](JG_Demo.gif)

# 작동원리
### 1. User Define
네이버 아이디 및 비밀번호, 텔레그램 봇 token(봇의 고유한 주소), 제목에 대한 검색어, 제목에 들어갈 필터, 본문에 들어갈 필터, 본문에서 찾아낼 주요항목, sql 서버 root 계정정보, 반복간격 지정

### 2. Process with 유사코드
각종 고정변수들 초기화, 서버DB에서 축적된 작성자리스트 불러오기 -> 셀레니움 가상드라이버 작동 -> 네이버 로그인

webpage = 중고나라카페, 전체게시글
0.5초간격으로무한반복{
게시판 보드부분의 iframe갱신 -> 글찾기(글제목 & not기존작성자) -> 해당 글의 본문페이지 iframe로드 -> 본문soup에서 가격, 업자용어 등을 읽음
-> [ "글제목", "제품특징", "게시글주소", "가격", "작성자", "작성날짜", "필터링된갯수", "글본문" ] 으로 정리
-> SQL DB 서버에 등록
-> 조건 만족 시 텔레그램으로 알림 보내기 ex) 필터링된갯수 5개 이하
}

### 3. guest용 서버
개발자의 컴퓨터가 켜져있을 때만 ip주소를 통해 공유된 DB페이지를 열람할 수 있습니다.
164.125.33.74 를 주소창에 입력하면, display-data.php 에서 현재 축적중인 db의 일부를 확인할 수 있습니다. 연결이 안되면 서버가 구동중이 아니라는 뜻입니다. 해당 페이지에는 "최근의 10개 글"이 수록돼있으며, 다음의 조건으로 필터링된 결과입니다.
a)글 제목이 지정된 검색조건을 만족
b)업자가 아닐 것
c)같은 작성자일 경우, 하나의 글로 간주

# 기타
리소스소모 : CPU_LOAD(20%) ~ 파이썬콘솔(10%) + 크롬웹드라이버(10%) , Network ~ SQL연결에서 초당 약 1mb


# 개발자노트

### 개발이유
중고나라의 인기있는 항목(스마트폰 등)에는 업자들의 홍보로 인해, 98%이상의 게시글이 업자글이어서, 개인판매자를 만나기가 힘들다. 또한, 중고나라는 구체적인 검색조건을 지원하지 않기 때문에, 일일이 클릭해서 보기 전에는 가격을 알기도 어렵고, 정렬할 수도 없어서 검색모듈을 만들게 되었다.

### 1차로 검색된 페이지를 크롤링하지 않고, 굳이 전체게시글 페이지를 1초간격으로 확인하는 이유
검색을 해보면, 실시간으로 되는 것이 아닌, 짧으면 10분에서 4시간까지도 검색db가 갱신이 안되어서, 새로 올라온 글을 알 수가 없다. 네이버에서 검색아카이브를 업데이트하는 주기가 불안정하므로, 조금이라도 실시간의 정보를 알려면 바로바로 업데이트가 되는 전체게시글 페이지에서 크롤링을 해야한다.

### 글 본문에 들어가야 하는 이유
본문에 들어가기 전에, 제목에서는 가격을 알 수 없다. 따라서 글을 열람해서, 가격부분을 읽어야 한다. 가격부분도 아무숫자나 써놓고, 본문에서 가격을 언급하는 경우가 종종 있기 때문에, 가격부분이 이상하면 본문에서 가격을 정규표현식으로 떠서 대체하도록 했다. 또한, 많은 부분을 글 본문에서 정규표현식으로 체크해서 업자여부 판별, 중요스펙들(잔상여부, 택배가 가능한지)을 찾는데 활용. 정규표현식은 공부기록 참고.

### driver.get 으로 업데이트 하지 않고, driver.execute_script(jquery 코드) 로 iframe 만 따로 갱신하는 이유
갱신속도가 느리다. 전체 글보기에서 약 1초면 다음페이지로 넘어가버리는데, 크롬 개발자툴에서 reload 퍼포먼스 확인해보면, 중고나라 페이지가 모두 로드되려면 약 1600ms가 걸린다. 세션시작하고, 이것저것 하는 시간이 대부분이고, 순수한 iframe에 걸리는 시간은 약 200ms 정도로, iframe 단독갱신이 필수적. 그러나, iframe으로 로드하게되면, driver.implicitly_wait 를 통해서 로딩을 기다리는 기능을 쓸 수가 없고, explicit 하게 '무엇을' 기다릴지 지정해주어야한다. selenium.webdriver.support 등의 추가 모듈을 불러서, 
WebDriverWait(driver, 10).until(EC.presence_of_element_located( (By.XPATH, XPATH 문법) )) 등으로,
구체적으로 필요한 iframe 내부 element들이 로딩되는걸 지정해주어야한다. XPATH 문법은 공부기록 참고.

### SQL DB를 사용하는 이유
Local 하게 데이터를 축적해도 되겠지만, 다른 장소, 혹은 익명의 접근으로 db를 확인하고 싶은 경우 서버구축이 필요하다.
따라서 유사서버를 구축하기 위해, 간단한 XAMPP 를 사용하여 Localhost(내컴퓨터) 의 mariaDB(SQL서버종류)를 빌드하고, 각종 보안설정(phpmyadmin 의 local전용 설정을 all granted 로 수정, SQL의 root 계정에 비밀번호 추가하기, SQL의 guest 계정 비밀번호 없이 추가, htdocs 싹 지우고 guest계정으로  DB를 select권한(보기전용)으로 불러오는 index.php, dispaly-data.php 등 페이지 추가.
