from django.shortcuts import render
from urllib.parse import urljoin
from django.http import JsonResponse
import mechanicalsoup
import re
import datetime
# from django.contrib import messages

def main_view(request):
    # browser = mechanicalsoup.StatefulBrowser()
    # browser.open('https://nid.naver.com/nidlogin.login')      # 네이버 로그인 #
    # browser.select_form('form#frmNIDLogin')                   # 네이버 로그인을 해야 게시글 내부의 정보를 크롤링할 수 있음
    # browser.launch_browser()                                  # 일회용 로그인 방법으로 한 번만 로그인하면 됨
    return render(request, 'main.html')
    
def data_list(request):
    browser = mechanicalsoup.StatefulBrowser()
    list_url = 'https://m.cafe.naver.com/ArticleList.nhn'      # 네이버 모바일 카페 url
    
    clubid = request.GET.get('clubid')          # 페이지에서 보내는 데이터들
    menuid = request.GET.get('menuid')
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    input_date = year[2:4] + '.' + month + '.' + day + '.'      # 날짜 정보를 게시글 목록 날짜 형식에 맞게 변환
    today = datetime.datetime.now()
    custom_today = str(today)[2:10].replace('-', '.') + '.'   # 오늘 날짜 필터링하기 위한 문자열
    search_page = 0
    params = {
        'search.clubid': clubid,
        'search.menuid': menuid,
    }
    data_list = []  # json_dict 사전에 담을 배열
    json_dict = {} # JsonResponse로 실어 보낼 사전

    if(input_date == custom_today):     # 오늘 날짜를 검색했을 경우
        while(True):
            search_page += 1        # 1페이지씩 늘려가며 크롤링
            params['search.page'] = search_page     # 검색할 페이지 params 사전에 담기
            soup = browser.open(list_url, params=params).soup   # 요청 받은 카페의 게시판 목록 접속
            for tag in soup.select('.board_box'):   # li 태그의 클래스 네임 board_box로 접근
                write_date = tag.find(class_='time').text   # 게시 날짜 추출
                if len(write_date) == 5:    # 오늘 날짜 데이터 판별
                    data_list.append(crawling_data(tag, list_url, browser, clubid))
                else:   # 검색 끝
                    json_dict['data_list'] = data_list
                    json_dict['msg'] = '검색이 완료됐습니다.'
                    return JsonResponse(json_dict, json_dumps_params={'ensure_ascii': True})

    else:   # 오늘 날짜 검색이 아닐 경우
        correct = False
        while(True):
            search_page += 1
            params['search.page'] = search_page
            soup = browser.open(list_url, params=params).soup
            if not soup.select('.board_box'):   # 검색 결과가 없는 경우 (맨 마지막 페이지까지 검색한 후)
                json_dict['msg'] = '검색이 완료됐습니다.'
                return JsonResponse(json_dict, json_dumps_params={'ensure_ascii': True})
            else:
                for tag in soup.select('.board_box'):
                    write_date = tag.find(class_='time').text
                    if input_date == write_date:    # 검색 값을 찾은 경우
                        correct = True
                        data_list.append(crawling_data(tag, list_url, browser, clubid))
                    elif correct == True:   # 검색 끝
                        json_dict['data_list'] = data_list
                        json_dict['msg'] = '검색이 완료됐습니다.'
                        return JsonResponse(json_dict, json_dumps_params={'ensure_ascii': True})
                    # 년월 필터링 : 해당 년월까지 검색하고, 결과값 없으면 검색 종료
                    elif int(input_date[3:5]) > int(write_date[3:5]) and input_date[:2] == write_date[:2] and len(write_date) == 9:
                        json_dict['msg'] = write_date + '까지 검색한 결과, 검색값이 없습니다..'
                        return JsonResponse(json_dict, json_dumps_params={'ensure_ascii': True})


# 데이터 크롤링 함수
def crawling_data(tag, list_url, browser, clubid):
    data_dict = {}
    title = tag.find("strong", class_='tit').text.strip()
    data_dict['title'] = title
    data_dict['writer'] = tag.find(class_='ellip').text
    try:
        article_url = urljoin(list_url, tag.find('a')['href'])
        data_dict['article_url'] = article_url
        article_soup = browser.open(article_url).soup
        try:
            compile_title = re.compile('^.*[★|\[](.*)[★|\]].*$')
            match_company = compile_title.match(title)
            company_name = match_company.group(1)
        except (AttributeError, IndexError) as err:          # 'NoneType' object has no attribute 'group' // list index out of range 에러 체크
            print('Attri or Index CompanyError: {0}'.format(err))
            company_name = ''
        try:
            select_article = article_soup.select('div.NHN_Writeform_Main > div > div')
            if(clubid=='15754634'): # 스펙업 카페일 경우
                date = select_article[3].text
                job_sort = select_article[4].text
                employ_sort = select_article[5].text
            else:   # 공취사 카페일 경우
                date = select_article[2].text
                job_sort = select_article[3].text
                employ_sort = select_article[4].text

            compile_date = re.compile('^.*[:](.*)[~]\s(.*)$')
            complie_sort = re.compile('^.*[:](.*)$')
            
            match_date = compile_date.match(date)
            match_job_sort = complie_sort.match(job_sort)
            match_employ_sort = complie_sort.match(employ_sort)
            
            start_date = match_date.group(1)
            end_date = match_date.group(2)
            job = match_job_sort.group(1)
            employ = match_employ_sort.group(1)

        except (AttributeError, IndexError) as err:          # 'NoneType' object has no attribute 'group' // list index out of range 에러 체크
            print('Attri or Index Error: {0}'.format(err))
            start_date = ''
            end_date = ''
            job = ''
            employ = ''

        data_dict['company'] = company_name
        data_dict['start_date'] = start_date
        data_dict['end_date'] = end_date
        data_dict['job_sort'] = job
        data_dict['employ_sort'] = employ

    except TypeError as err:       # 해당 날짜에 검색 결과 없을 때
        print('TypeError: {0}'.format(err))

    return data_dict

