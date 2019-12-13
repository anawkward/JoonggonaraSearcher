# 중고나라 검색기 2.0
http://164.125.33.74:8008
--> 업자, 상태 안좋은, 비싼 매물을 모두 필터링하여 개인판매자의 정상적인 매물을 표시합니다.

크롤러 상에서 구현된 기능
1. 일반 키워드 검색과 정규표현식에 의한 검색을 지원
2. 정상범위의 가격을 찾아낼 때 까지, 제목과 본문, 가격항목에서 검색
3. 제품에 대한 중요한 항목들을 정규표현식을 사용하여 검색
4. 하루동안 이미 검색된적이 있는 동일 글쓴이의 새로운 글 검색에서 제외
5. 글쓴이의 게시글 목록으로 가서 15개의 글을 쓴 주기를 확인. 너무 짧으면 업자판정
6. 검색db를 요청하는 것이 아닌, 직접 짧은주기의 갱신을 통해 db축적
7. 텔레그램을 통해, 조건에 맞는 게시글 발생 시 알림

크롤러 상에서 구현된 자원 최적화
1. 웹브라우저를 초기화하여, monitor frame 과 parsing frame 으로 분리한 병렬탐색구조
2. 모니터링하는 것을 최우선으로 하고, 웹페이지 해석은 남는 시간동안 처리하도록 하는 비동기적 프로그래밍
3. 각종 예외적인 상황(올리자마자 삭제, 잘못된 수프, 브라우저 꺼짐)에 대응하는 로그 축적. 처리과정을 모두 표시

SQL 상에서 구현된 기능
1. 가격범위에 의한 필터링
2. 검색된 특징들에 따른 필터링
3. 업자로 신고된 글쓴이에 대한 필터링
4. BAD로 신고된 글에 대한 필터링
5. 글 작성 주기가 평균 60분이 안되면 필터링

웹페이지 상에서 구현된 기능
1. 업자, BAD판정을 서버로 전송. 이 때, ip와 시각을 함께 기록
2. 숨김, 업자, BAD 판정을 할 때마다 Cookie에 저장. 사이트를 종료해도 기록은 유지.
3. Cookie가 없는 타 플랫폼(pc->스마트폰)에서도 사용하기 위한 Cookie 저장기능 구현(user_name save,load)
4. 확장모드 : 한 Client 개인이 스스로 업자 혹은 BAD판정을 하여, 검색결과를 전처리.
5. 반영모드 : 확장모드에서 전처리된 결과를 다른 Client들도 공유한다. 전처리된 결과만 볼 수 있음.

개발중인기능
1. 축적된 BAD판정 정보를 가지고 인공신경망을 사용하여 상태판정을 자동화
2. 다수의 검색어에 대응하는 웹페이지 Navigation
3. 중고나라에 준하는 타 플랫폼이 있을 시, 해당 플랫폼의 모니터링도 병렬진행
