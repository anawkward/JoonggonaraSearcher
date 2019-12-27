# 교훈
# 1. ctrl + w : 해당 word 블록지정
# 2. ctrl + shift + j : multiline code 를 한줄로 변경

# 계획
# 0. sql 과 상호작용,
# 파이썬에서 author list 를 최초 로드
# 새로 올라온 글이 author list 에 없으면 올리고, author list 를 업데이트

# 1. 업자거르기 (구현예정, db쌓이는거 보고 생각) 일단 지금은 임시로 filter_count < 5 ? 정도 적용
# i) 글제목 : db에 올라와있는 글과 제목에서 유사성
# ii) 글내용 : db에 올라와있는 글과 본문에서 유사성
# iii) 작성자가올린 글목록 : 작성자가 올린 게시물들에서, 같은날짜로 5개이상 올렸으면 거르기

# 글 전체내용 : soup2, 제목 : title, 작성자 : author, 주소 : address
# soup 과정을 따라가려면, soup2 -> plist 와 divlist -> plist2와 divlist2 순으로 확인할 것.

# 위기
# 네이버에서 검색용 아카이브를 업데이트 하지 않는다. 왜지?
# 3시간 째, 검색에 들어가는 아카이브가 업데이트 되지 않고 있다. 아무 검색방법도 효과가 없다.
# 이렇게 되면 하는 수 없이, 전체글 페이지에서 올라오는 글들을 0.1초간격으로 빠르게 읽어서 s8이 들어가는
# postnum 을 찾아서 접속하는 방식밖에 방법이 없는데..? 일주일정도 경과를 지켜보고, 결정하자
# 검색아카이브는 갱신이 최소 몇분에서 몇시간까지 딜레이가 있는걸로 결론.
# 전체글에서 키워드로 따는 방법으로 변경

# 위기1 극복 후 위기2
# 갱신속도가 느리다. 파이썬이 느린건가 했더니, 실제로 네이버 중고나라 메인페이지를 Page load performance 띄워서 봤더니
# 로드까지 1600ms 가 걸린다.
# 크롬 콘솔창에서 이하의 Jquery 문을 실행하면 게시판 보드 91ms 만 순수하게 iframe 변경됨.
# $("cafe_main").src = '//cafe.naver.com/ArticleList.nhn?search.clubid=10050146&search.boardtype=L'
# 이걸로 크롬웹드라이버에서 반복적으로 갱신해가면서 수프뜨면 될 듯??

# 해결 : iframe 별로 갱신하고, 시간최적화 다 됐음. 남은건 업자 필터링. 이것도 iframe 띄워서 5개 글이 1일 이내에 쓰이면 업자. 그렇지 않으면 텔레그램 보내기를 할까?
# 일주일정도 db쌓아보고, 결정 . filter_count 만으로도 충분히 걸러지는 것 같기도 하고..?

# 추가개발 : 세션을 두개 운영하면서, 하나는 업데이트용, 하나는 파싱용으로 두고, 각각 iframe 을 전환하면서
# 검색세션에서 파싱세션으로 넘어갈 때, 스택식으로 쌓아서 순차적으로 처리되는 알고리즘 개발하면 continuity 놓칠 일 없음.
# 현재로서는, 로딩에 0.5+0.2초, 파싱에 0.3+0.1초가 걸리는데, 비동기식으로 병렬세션 운영하면
# 0.7초는 소모에서 없앨 수 있겠지.

# 리소스모니터링 결과, 파이썬콘솔에서 cpu 10%, 크롬웹드라이버에서 cpu 10% 평균적으로 소모. 네트워크는 초당 1mb정도로 소모.

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from winsound import Beep
import telegram
import os
import re
import pandas as pd
import pymysql
import sys
from bs4 import NavigableString
import dateutil.parser

debug = False
########################################사용자 지정 초기값 ################################################
Search = [] # Regular_Search 혹은 Search 둘중 하나를 채우십쇼.
Regular_Search = '^(?!.*(구매|구합|삽니|사봅|구해|S9)).*럭.+[^a-zA-Z][s|S]8[^0-9](?!.*(구매|구합|삽니|사봅|구해|S9)).*$' # 정규표현식은 편리합니다.
price_Search_range = [100000,500000]
NAVER = {'id': 'id', 'passwd': 'password'}
myID = NAVER["id"]
myPASSWD = NAVER["passwd"]
my_token = '1029388466:AAEAVoLmMbyokQ-YM0WRgwlpxbnpwly6NCY' # 봇이 필요합니다. 텔레그램 봇파더 검색
# 필터요소 : 해당 필터가 일정 갯수 이상 포함될 경우, 업자로 판정하도록.
filter_factor_title = ['☆', '★', '◀', '▶', '■', '□', '●', '○', '◇', '◈', '♪', '♨', '♣', '♧', '⊙', '#', '@', '<', '>','▣', '최저가', '구매',
                       '매입','삽니다', '파손', '부품']
filter_factor_body = ['☆', '★', '◀', '▶', '■', '□', '●', '○', '◇', '◈', '♪', '♨', '♣', '♧', '⊙', '#', '@', '<', '>', '▣', '매입',
                      '파손', '고장', '최고가', '최저가', '할인', '대박', '세일', '한정', '특급', '특가', '전국', '가개통',
                      '전문', '강변', '출장', '급처', '사은품', '최고회원', '정직', '퀵', '상담', '고객', '손님', '100%']
# 중복으로 넣으면 추가가중치.
# 1. 잔상여부 2. 상태 3. 택배여부 4. 멍 여부
important_factor = ["[깨파][^없끗려는워심]{7}|잔상[^없]{7}|번인[^없]{7}|멍[^없]{7}|금이.{4}|반점[^없]{7}|열화.{4}"]
# vender check 및 processing 이 이루어질 메인페이지
webpage = 'https://cafe.naver.com/joonggonara?iframe_url=/ArticleList.nhn%3Fsearch.clubid=10050146%26search.boardtype=L'
loop_interval = 0.1 # 페이지 로드 등에 필요한 최소시간(iframe 하나당 약 0.2초)은 기본값으로 포함돼있고, 거기에 추가할 시간을 입력. slow caution 이 안나오는거에 한해서, 높일수록 자원소모가 적음
# 호스트, 유저명, 비밀번호, 디비 등은 직접 sql 서버를 만들어서 설정해야합니다. 시간 되면 공용 sql 서버 열던지 하겟음..
def sqlquery(query, host = 'localhost', user = 'root', password = 'somepassword', db = 'test'):
    conn = pymysql.connect(host, user, password, db, charset='utf8mb4')
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    res = cur.fetchall()
    conn.close()
    return res
#####################################################################################################################
########################################각종 변수 초기화 ###########################################################
postlist = []
timelist = []
Searched = []
i = 0
sums = 0
t = 0
impolist = []
first = ''
need_refresh = 0
number_of_searched = 0
number_of_added = 0
endtexts = []
pd.set_option('display.max_colwidth', -1)
after_the_insert_it_requires_some_time = False
query = 'select author from test_table where 1'
dbauthor = [str(sqlquery(query)[i])[2:-3] for i in range(0, len(sqlquery(query)))] # sql
sign = ['↑', '↗', '→', '↘', '↓', '↙', '←', '↖']
df = pd.DataFrame(columns=['title', 'feature', 'address', 'price', 'author', 'date', 'filter_count', 'date_diff', 'body'])
bot = telegram.Bot(my_token)
chat_id = 885829636 # bot.getUpdates()[-1].message.chat.id # id 인식하는 명령어. 아이디 모를때는 해당 함수 사용해서 텔레그램 채팅인식
# crhome driver 창에 관한 초기설정. headless 를 안하면 서핑과정을 확인할 수 있다.
options = webdriver.ChromeOptions()
#options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument('disable-gpu')
#####################################################################################################################
#################################### Selenium 웹환경 작동 ##########################################################
driver = webdriver.Chrome(executable_path='C:/chromedriver.exe',options=options)  # 인터넷에서 chromedirver 다운받아서 웹드라이버로 사용
driver.implicitly_wait(1)  # 암묵적으로 웹 자원을 주고받는데 최대 1초 기다리기

# 네이버 Login
driver.get('https://nid.naver.com/nidlogin.login')  # 네이버 로그인 URL로 이동하기
driver.execute_script("document.getElementsByName('id')[0].value=\'" + myID + "\'")  # id입력
driver.execute_script("document.getElementsByName('pw')[0].value=\'" + myPASSWD + "\'")  # pw입력
driver.find_element_by_xpath('//*[@id="frmNIDLogin"]/fieldset/input').click()  # 로그인 버튼클릭하기
time.sleep(2)

# 설정된 webpage(예를 들어, 중고나라 검색결과 아티클)로 접속
driver.get(webpage)

while True : # 이하 전체가 항상 반복문안에 들어가있음. 100라인짜리 공통 들여쓰기. 주석 지우고 이하를 전체 블록지정해서 tab 누르면 실제 사용하는 반복버젼코드가 됩니다.
    ### 게시판 갱신 부분
    # 계속해서 안의 iframe 만 바꿔가면서 게시판 갱신
    if need_refresh > 5 :
        driver.get(webpage)
        need_refresh = 0
    driver.implicitly_wait(10)
    try :
        driver.switch_to.default_content()
        driver.execute_script('$(\"cafe_main\").src = \'//cafe.naver.com/ArticleList.nhn?search.clubid=10050146&search.boardtype=L\'')
        driver.switch_to.frame('cafe_main')
    except : print('error occured at line 138-142. but pass');need_refresh+=1; continue
    # element가 뜰 때까지의 추가해야되는 시간. 15번째 글의 제목이 뜨는 시점까지 기다림
    try : WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@id='main-area']/*[6]/table/tbody/*[15]/td[1]/div[@class = 'board-list']/div[1]/a")))
    except : print('error occured at line 144. but pass'); continue # 읽는 도중에 글이 삭제되면 오류가 뜨는 것 같다. 삭제된 글 만나면 리셋.

    for i in range(0,10) : # 위에서 wait 를 넣어줘도, 간혹 다른 요소들이 안뜨는 케이스가 발생.. 모든 요소들을 지정해서 기다리느니 그냥 반복문에서 오류안뜰때까지 try시키자.
        try :
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # 게시판 리스트에서 Search 키워드 찾기
            board = soup.select('#main-area > div:nth-child(6) > table > tbody')[0]
            titles = [board.find_all('div', {'class' : 'inner_list'})[i].find('a',{'class':'article'}).text.strip() for i in range(0,15)] # 총 15개 글
            links = [board.find_all('div', {'class' : 'inner_list'})[i].find('a',{'class':'article'})['href'] for i in range(0,15)]
            authors = [board.find_all('div',{'class' : 'pers_nick_area'})[i].find('a', {'class' : 'm-tcol-c'}).text for i in range(0,15)]
            break # 오류없으면 반복문 빠져나옴
        except :
            time.sleep(0.1)

    if first not in authors :
        print('Caution! : Board update is too slow that it does not maintain its continuity')
        need_refresh += 1 # 왠진 모르지만, 세션이 점점 느려짐. 5번정도 느려지면 driver.get 으로 새로 세션시작.
    first = authors[0]
    ######################
    # 검색어를 포함하는 게시물 읽기

    if(any(Regular_Search)) :
        pattern = re.compile(Regular_Search)
        i = 0
        for line in titles :
            if pattern.search(line) != None :
                Searched.append(i)
            i += 1

    else :
        i = 0
        for line in titles :
            if any([s in line for s in Search]) :
                Searched.append(i)
            i += 1

    # 검색어 발견 시 작동하는 구문(약 70줄)
    if Searched :
        number_of_searched += 1
        found = Searched[0] # 위에까진 한 화면에서 여러개 동시에 리스트로 쌓지만, 여기서부터 그냥 글 하나만 정해서 스크래핑하겠음
        Searched = []  # Searched 됐을 때, 처리하고 나서 여기로 와서 다시 False 처리해서 새출발
        # 찾아진거 정보
        title = " ".join(titles[found].split()) # 불필요한 공백 제거된 글제목
        author = authors[found]
        address = 'https://cafe.naver.com' + links[found]

        if author not in dbauthor: # 이하 전체가 항상 if문(70라인)안에 들어가있음
            number_of_added += 1

            if debug :
                time1 = time.time() # 디버그

            print("New author detected, this article adds to SQL Server and is telegramed after filtered. added : ",
                  number_of_added, "total Searched :", number_of_searched)
            print(title)
            dbauthor.append(author)
            # 글 읽기
            driver.switch_to.default_content()
            driver.execute_script('$(\"cafe_main\").src = \'//cafe.naver.com'+links[found]+'\'')
            driver.switch_to.frame('cafe_main')
            WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located((By.XPATH, "//div[@class='tbody m-tcol-c']")))  # 최대 3초 기다림, element 가 뜰 때 까지
            if debug :
                time1_2 = time.time()
                print('post body loaded. used time resource : '+str(time1_2-time1))
            innerText = driver.execute_script("return document.querySelector(\"#tbody\").innerText")[643:] #tbody 자체에 innerTetx가 첨부되있는 케이스도 포함
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            if debug :
                time2 = time.time()
                print('parsed post body. used time resource : '+str(time2-time1_2)) # 디버그

            # 글 읽었으면, 바로 작성자 게시글목록 수프뜨러 감. 수프끓이기는 그 와중에 계속 진행.
            writer_id = driver.find_element_by_xpath(
                '//div[@class = "list-blog border-sub"]/div/div[3]/div[1]/table/tbody/tr/td[1]/table/tbody/tr/td[1]/a').get_attribute(
                'href')[81:]
            w_iframe = "/CafeMemberNetworkArticleList.nhn?clubid=10050146&search.clubid=10050146&search.query=" + writer_id + "&search.writerid=" + writer_id + "&search.page=1&search.searchtype=7&search.memberid=" + writer_id
            driver.switch_to.default_content()
            driver.execute_script('$(\"cafe_main\").src = \''+w_iframe+'\'')
            driver.switch_to.frame('cafe_main')
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-area"]/div[1]/table/tbody/tr[1]/td[1]/div[2]/div/a'))) # 첫번째글 로드. 몇개인지 모르니까.
            html_of_writer = driver.page_source
            soup_of_writer = BeautifulSoup(html_of_writer, 'html.parser')
            w_times = [tag.text for tag in soup_of_writer.findAll('td',{'class' : "td_date"})]
            first_w = w_times[0]
            last_w = w_times[-1]
            date_diff =  dateutil.parser.parse(first_w) - dateutil.parser.parse(last_w)
            if len(w_times) == 1 :
                date_diff_min = 1440 # 글을 한개만 썼을 때는 1440분으로 취급.
            else :
                date_diff_min = date_diff.total_seconds()/60
            min_per_post = date_diff_min/len(w_times) # 게시글 당 평균 시간간격.

            if debug :
                time3 = time.time()
                print('parsed writer body used time resource : '+str(time3-time2)) # 디버그
            ########################### 글 내용으로 수프를 끓여보자. ########################################################
            date = soup.find('td', {'class' : 'm-tcol-c date'}).text
            date = date[8:10] + '일 ' + date[12:20]
            soup2 = soup.find('div',{'class':'tbody m-tcol-c'})

            try :
                price = int(soup2.find('div', {'class' : 'prod_price'}).text.strip().replace(',','').replace('원',''))
            except :
                price = 0

            def end_node(tag):
                if tag.name not in ["div", "p", "span"]:
                    return False  # div 혹은 p 이면서 동시에,
                if tag.get('class') is not None and tag.get('class')[0] in ['banner_add', 'notice_manager', 'NHN_Writeform_Main']:
                    return False  # class 속성이 있을 때, 이하의 class가 아니어야함.
                return True  # 그러면 okay. 해당태그는 출력

            endnodes = soup2.findChildren(end_node, recursive=False)  # recursive = False 할 시에, 자손의 자손은 찾지 않는다.
            for item in endnodes:
                endtexts.append(item.text)
            body = ' '.join(endtexts)+innerText
            body = re.sub(r'\n\s*\n', '\n', body) #줄바꿈 정리.
            body = body.replace('\xa0','') # 개행없는 줄바꿈문자 \xa0 제거

            if price < price_Search_range[0] or price > price_Search_range[1] : # 5000원 이상 40만원 이상은 오류로 보고 아래의 body parsing해서 찾아내기
                pattern = re.compile('[\d]{1,}\s?만?\s?원|[\d,]{3,}\s?만?\s?원|[\d]{1,}\s?만\s?원?|[\d,]{3,}\s?만\s?원?')
                #prisear = pattern.search(body)
                try :
                    prisear = list(pattern.findall(body)[0])
                    prisear.remove('')
                except :
                    prisear = None
                if not prisear is None :
                    pri = int(prisear[0].replace('만', '0000').replace(',','').replace(' ',''))
                    price = pri

            # body 로 데이터프레임으로 정리해보자.
            for item in filter_factor_body :
                sums += body.count(item)
            # 요부분은 title로 filter . 제목에서 걸리면 바로 5를 곱해서 하나라도 걸리면 탈락되게끔
            for item in filter_factor_title :
                sums += 5*title.count(item)
            for item in important_factor :
                pattern = re.compile(item)
                if(pattern.search(body+title)==None) :
                    impolist.append(str(pattern.search(body)))
                else :
                    impolist.append(str(pattern.search(body)[0]))
            if len(body) < 5 :
                sums += 10 # 아무내용이 없는 글 = 이미지로 본문을 대체한 글 = 업자 100% , 거른다.!
                if(debug) :
                    print('No body error. check if something is wrong.')
                    break
            important = ','.join(impolist)
            df.loc[len(df)+1] = [title, important, address, price, author, date, sums, min_per_post, body]
            if debug :
                time4 = time.time()
                print('done with soup of post body and writer body. used time resource : '+str(time4-time3)) # 디버그
            # SQL : INSERT
            df1 = str(df.loc[1].tolist())
            df2 = df1.replace("[", "(")
            df3 = df2.replace("]", ")")
            inputrow = df3
            query = 'insert into test_table(`title`, `feature`, `address`, `price`, `author`, `date`, `filter_count`, `min_per_post`, `body`) values' + inputrow
            sqlquery(query)
            if debug :
                time5 = time.time()
                print('sql done. used time resource : '+str(time5-time4)) # 디버그

            # filter_count나 body 검증 후, telegram 보내기.
            if 80000 < price < 160000 and (min_per_post > 60 or sums < 5) and len(important) < 2 :
                message = "제목 : " + df['title'].to_string(index=False) + \
                          "가격 : " + df['price'].to_string(index=False) + \
                          "주소 : https://164.125.33.74"
                bot.sendMessage(chat_id=chat_id, text=message)
            if debug:
                time6 = time.time()
                print('telegram done. used time resource : ' + str(time6 - time5))  # 디버그

            df = pd.DataFrame(columns=['title', 'feature', 'address', 'price', 'author', 'date', 'filter_count', 'min_per_post', 'body'])
            impolist = []
            plist = []
            plist2 = []
            plist3 = []
            divlist = []
            divlist2 = []
            divlist3 = []
            tdlist = ''
            endtexts = []
            sums = 0
            t = 65 # 발견 시 non-replace 로 시간 message 한번 띄우기
            ###############################################################################################################
    # 시간표시. 1회 체크마다 현재시간을 출력
    now=time.gmtime(time.time())
    message = '{:d}시 {:d}분 {:d}초 {:s}'.format(now.tm_hour+9, now.tm_min, now.tm_sec, sign[t%8])
    if t < 64 :
        print(message, end = '\r')
    else :
        print(message)
        t = 0
    t+=1
    time.sleep(loop_interval) # 기본 implicitly wait, 혹은 until(presence) 의 시간간격 외에, 추가로 들어갈 최소 시간간격
    driver.implicitly_wait(5)
