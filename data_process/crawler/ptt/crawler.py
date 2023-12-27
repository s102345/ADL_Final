""" 
ptt爬回覆工具，可以指定要爬的頁數與討論板
"""
import re
import rich
import rich.table
from requests_html import HTMLSession
import urllib.parse
import json, os
import codecs

def parse_next_link(controls):
    link = controls[1].attrs['href']
    next_page_url = urllib.parse.urljoin('https://www.ptt.cc/', link)
    return next_page_url

def parse_page(response):
    
    context = (response.html.xpath('//*[@id="main-content"]/text()[1]'))[0]
    attrs = response.html.find('.article-meta-value')
    if len(attrs)<4:
        return None
        
    author = attrs[0].text
    place = attrs[1].text
    title = attrs[2].text
    date = attrs[3].text
    pushs = response.html.find('.push')
    
    users = {}
    result = []
    push_count = 0
    for push in pushs:
        try:
            tag = push.find('.push-tag')[0].text
            user = push.find('.push-userid')[0].text
            content = push.find('.push-content')[0].text
        except Exception:
            continue
        
        if "推" in tag:
            push_count += 1
        if user not in users:
            users[user] = ""
        users[user] += content[2:]
    for key,value in users.items():
        obj = {
            'author':author,
            'place':place,
            'title':title,
            'date':date,
            'context':context,
            'replyer':key,
            'text':value,
            'label':[]
        }
        result.append(obj)
        
    return {"replies":result,"push_count":push_count}

# 解析該頁文章列表中的元素
def parse_article_entries(elements):
    results = []
    for element in elements:
        try:
            push = element.find('.nrec', first=True).text
            mark = element.find('.mark', first=True).text
            title = element.find('.title', first=True).text
            author = element.find('.meta > .author', first=True).text
            date = element.find('.meta > .date', first=True).text
            link = None
            link = element.find('.title > a', first=True).attrs['href']
        except AttributeError:
            # 處理文章被刪除的情況
            if '(本文已被刪除)' in title:
                match_author = re.search('\[(\w*)\]', title)
                if match_author:
                    author = match_author.group(1)
            elif re.search('已被\w*刪除', title):
                match_author = re.search('\<(\w*)\>', title)
                if match_author:
                    author = match_author.group(1)
        # 將解析結果加到回傳的列表中
        results.append({'push': push, 'mark': mark, 'title': title,
                        'author': author, 'date': date, 'link': link})
    return results


# 想要收集的討論版
metas = ["Gossiping", "C_Chat", "Baseball", "Stock", "NBA", "Lifeismoney", "HatePolitics", "car",
         "LoL", "home-sale", "movie", "Japan_Travel", "KoreaStar", "basketballTW", "sex"]

# 想要收集的頁數
num_page = 50
for meta in metas:
    # 起始首頁
    url = f'https://www.ptt.cc/bbs/{meta}/index.html'

    # 建立 HTML 會話
    session = HTMLSession()
    session.cookies.set('over18', '1')  # 向網站回答滿 18 歲了 !
    with open(f"{meta}.json", 'w+', encoding="UTF-8") as json_file:
        for page in range(num_page):
            # 發送 GET 請求並獲取網頁內容
            response = session.get(url)
            # 解析文章列表的元素
            results = parse_article_entries(elements=response.html.find('div.r-ent'))
            
            for article in results:
                if article['link'] is None:
                    continue
                
                link = "https://www.ptt.cc"+article['link']
                article_session = HTMLSession()
                article_session.cookies.set('over18', '1')
                article_response = article_session.get(link)
                article_results = parse_page(article_response)
                if article_results is None:
                    continue
                push_num = article_results['push_count'] # 文章推數
                replies_num = len(article_results['replies'])
                if replies_num == 0:
                    continue
                
                push_ratio = push_num/replies_num #文章推數的比例
                if push_ratio > 0.85 or push_ratio<0.1:
                    continue
                
                for article_reply in article_results['replies']:
                    str = (json.dumps(article_reply,ensure_ascii=False))
                    json_file.write(str)
                    json_file.write('\n')
            # 解析下一個連結
            next_page_url = parse_next_link(controls=response.html.find('.action-bar a.btn.wide'))

            # 建立表格物件
            table = rich.table.Table(show_header=False, width=120)
            for result in results:
                table.add_row(*list(result.values()))
            # 輸出表格
            rich.print(table)

            # 更新下面一位 URL~
            url = next_page_url