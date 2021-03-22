import json
import re
from collections import deque, defaultdict
from time import time
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import Response
app = FastAPI()


def append_news(idx, cur_page, news_dict: dict, news_num: int, soup: BeautifulSoup):
    table = soup.find('ul', {'class': 'list_news'})
    li_list = table.find_all('li', {'id': re.compile('sp_nws.*')})
    news_list = [(li.find('div', {'class': 'news_area'}),
                  li.find('a', {'class': 'dsc_thumb'})) for li in li_list]
    try:
        a_list = [(news[0].find('a', {'class': 'news_tit'}),
                   news[1].find('img', {'class': 'thumb api_get'})) for news in news_list]
    except AttributeError:
        a_list = [(news[0].find('a', {'class': 'news_tit'}),
                   {'src': ''}) for news in news_list]
    list_len = len(a_list)
    for n, t in a_list[:min(list_len, news_num - idx)]:
        news_dict[idx] = {'title': n.get('title'),
                          'url': n.get('href'),
                          'thumbnail': t.get('src')}
        idx += 1

    cur_page += 1

    return idx, cur_page, news_dict


async def fetch(session, url):
    async with session.get(url, verify_ssl=False) as response:
        return await response.text()


async def task(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        return await asyncio.gather(*tasks)


"""
https://search.naver.com/search.naver?&where=news&query=암호화폐&sm=tab_pge&start=11
"""

@app.get('/')
async def get_news_list(query: str = '암호화폐', news_num: int = 10):
    start = time()
    news_dict = defaultdict()
    news_url = f'https://search.naver.com/search.naver?where=news&sm=tab_jum&query={query}/'
    request = await task([news_url])
    soup = BeautifulSoup(request.__str__(), 'html.parser')
    pages = soup.find('div', {'class': 'sc_page_inner'})
    idx, cur_page = 0, 0
    while idx < news_num:
        (idx, cur_page, news_dict) = append_news(idx, cur_page, news_dict, news_num, soup)
        try:
            req = reqs.popleft()
        except (IndexError, UnboundLocalError):
            next_page_urls = [p.get('href') for p in pages.find_all('a', {'class': 'btn'})]
            reqs = deque(await task([f'https://search.naver.com/search.naver{n_url}'
                                     for n_url in next_page_urls]))
            req = reqs.popleft()

        soup = BeautifulSoup(req.__str__(), 'html.parser')

    print(f"time : {time() - start}")

    return Response(json.dumps(news_dict, ensure_ascii=False), status_code=200)

