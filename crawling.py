import json
import re
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import Response

app = FastAPI()


@app.get('/')
async def get_news_list(query: str = None, news_num: int = 10):
    news_dict = {}
    news_url = 'https://search.naver.com/search.naver?where=news&sm=tab_jum&query={}'
    request = requests.get(news_url.format(query))
    soup = BeautifulSoup(request.text, 'html.parser')
    idx, cur_page = 0, 0
    while idx < news_num:
        table = soup.find('ul', {'class': 'list_news'})
        li_list = table.find_all('li', {'id': re.compile('sp_nws.*')})
        thumb_list = [li.find('img', {'class': 'thumb api_get'}) for li in li_list]
        area_list = [li.find('div', {'class': 'news_area'}) for li in li_list]
        a_list = [area.find('a', {'class': 'news_tit'}) for area in area_list]

        for n, t in zip(a_list[:min(len(a_list), news_num - idx)], thumb_list[:min(len(a_list), news_num - idx)]):
            news_dict[idx] = {'title': n.get('title'),
                              'url': n.get('href'),
                              'thumbnail': t.get('src')}
            idx += 1

        cur_page += 1
        pages = soup.find('div', {'class': 'sc_page_inner'})
        next_page_url = [p for p in pages.find_all('a') if p.text == str(cur_page)][0].get('href')

        req = requests.get('https://search.naver.com/search.naver' + next_page_url)
        soup = BeautifulSoup(req.text, 'html.parser')

    return Response(json.dumps(news_dict, ensure_ascii=False), status_code=200)
