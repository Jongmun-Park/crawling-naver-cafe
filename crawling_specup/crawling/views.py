from django.shortcuts import render
from urllib.parse import urljoin
from django.http import JsonResponse
from django.contrib import messages
import mechanicalsoup
import re
import datetime

def main_view(request):
    browser = mechanicalsoup.StatefulBrowser()
    browser.open('https://nid.naver.com/nidlogin.login')      # 네이버 로그인
    browser.select_form('form#frmNIDLogin')
    browser.launch_browser()
    return render(request, 'main.html')
    
def data_list(request):
    browser = mechanicalsoup.StatefulBrowser()
    list_url = 'https://m.cafe.naver.com/ArticleList.nhn'      # 네이버 모바일 카페 url
    
    clubid = request.GET.get('clubid')
    menuid = request.GET.get('menuid')
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    input_date = year[2:4] + '.' + month + '.' + day + '.'
    today = datetime.datetime.now()
    custom_today = str(today)[2:10].replace('-', '.') + '.'   # 오늘 날짜 필터링하기 위한 문자열
    search_page = 0
    params = {
        'search.clubid': clubid,
        'search.menuid': menuid,
    }
    data_list = []

    if(input_date == custom_today):     # 오늘 날짜를 검색했을 경우
        while(True):
            search_page += 1
            print('page:', search_page)
            params['search.page'] = search_page
            soup = browser.open(list_url, params=params).soup
            for tag in soup.select('.board_box'):
                write_date = tag.find(class_='time').text
                if len(write_date) == 5:    # 오늘 날짜 데이터
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
                        except (AttributeError, IndexError) as err:          # 'NoneType' object has no attribute 'group' 에러 체크
                            print('CompanyError: {0}'.format(err))
                            company_name = ''
                        try:
                            date = article_soup.select('div.NHN_Writeform_Main div > span > b > span')[0].text
                            print(title, '--------정규표현식 거치면 : ', company_name, date)
                            compile_date = re.compile('^(.*)[~]\s(.*)$')
                            match_date = compile_date.match(date)
                            start_date = match_date.group(1)
                            end_date = match_date.group(2)
                        except (AttributeError, IndexError) as err:          # 'NoneType' object has no attribute 'group' 에러 체크
                            print('DateError: {0}'.format(err))
                            start_date = ''
                            end_date = ''
                        
                        data_dict['company'] = company_name
                        data_dict['start_date'] = start_date
                        data_dict['end_date'] = end_date

                    except TypeError as err:       # 해당 날짜에 검색 결과 없을 때
                        print('TypeError: {0}'.format(err))

                    data_list.append(data_dict)

                else:   # 검색 끝
                    print('~endwhile~')
                    return JsonResponse(data_list, json_dumps_params={'ensure_ascii': True}, safe=False)
    else:   # 오늘 날짜 검색이 아닐 경우
        correct = 0
        while(True):
            search_page += 1
            print('page:', search_page)
            params['search.page'] = search_page
            soup = browser.open(list_url, params=params).soup
            if not soup.select('.board_box'):   # 검색 결과가 없는 경우
                print('검색 결과가 없습니다.')
                return JsonResponse(data_dict, json_dumps_params={'ensure_ascii': True})
            else:
                for tag in soup.select('.board_box'):
                    write_date = tag.find(class_='time').text
                    if len(write_date) != 5 and (int(input_date[:2]) > int(write_date[:2])):    # 연도 필터링 : 해당 연도까지 검색하고 결과값 없으면 검색 종료
                        print(write_date, '검색 결과가 없습니다.')
                        return JsonResponse(data_dict, json_dumps_params={'ensure_ascii': True})
                    if input_date == write_date:  # 검색 값을 찾은 경우
                        correct = 1
                        title = tag.find("strong", class_='tit').text.strip()



                        print('correct:', title)
                    elif correct == 1: # 검색 끝
                        return JsonResponse(data_dict, json_dumps_params={'ensure_ascii': True}, safe=False)





