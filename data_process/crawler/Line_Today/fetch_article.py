from selenium import webdriver
from fake_useragent import UserAgent as ua   
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import json
import os
import re

SCROLL_DIS = 2000
MAX_WAIT_TIME = 10
LONG_DELAY = 5
SHORT_DELAY = 3

def pageBottom(driver):
    bottom=False
    a=0
    while not bottom:
        new_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script(f"window.scrollTo(0, {a});")
        if a > new_height:
            bottom=True
        a+=5

sources = [
    {'name': '三立', 'url': 'https://today.line.me/tw/v2/publisher/100106'},
    {'name': '民視', 'url': 'https://today.line.me/tw/v2/publisher/100495'},
    {'name': '自由電子報', 'url': 'https://today.line.me/tw/v2/publisher/100309'},
    {'name': '東森', 'url': 'https://today.line.me/tw/v2/publisher/100237'},
    {'name': 'TVBS', 'url': 'https://today.line.me/tw/v2/publisher/100167'},
    {'name': '聯合', 'url': 'https://today.line.me/tw/v2/publisher/100151'},
    {'name': '太報', 'url': 'https://today.line.me/tw/v2/publisher/101366'},
    {'name': '新頭殼', 'url': 'https://today.line.me/tw/v2/publisher/100086'},
    {'name': '風傳媒', 'url': 'https://today.line.me/tw/v2/publisher/100004'},
    {'name': 'CTWANT', 'url': 'https://today.line.me/tw/v2/publisher/101427'},
    {'name': '台視', 'url': 'https://today.line.me/tw/v2/publisher/103053'},
    {'name': '鏡新聞', 'url': 'https://today.line.me/tw/v2/publisher/103088'},
    {'name': 'Nownews今日新聞', 'url': 'https://today.line.me/tw/v2/publisher/100007'},
    {'name': '東森新聞雲', 'url': 'https://today.line.me/tw/v2/publisher/100200'},
    {'name': '中廣新聞網', 'url': 'https://today.line.me/tw/v2/publisher/100006'},
]

def fetch_articles(driver, url, amount, trial=100):
    driver.get(url)
    _ = WebDriverWait(driver, MAX_WAIT_TIME).until(
        EC.presence_of_element_located((By.CLASS_NAME, "entityProfile-head"))
    )

    for i in range(trial):
        driver.execute_script(f"window.scrollBy(0, {SCROLL_DIS});")
        articles = driver.find_elements(By.CLASS_NAME,'articleCard.articleCard--horizontal')
        if len(articles) >= amount:
            break

    
    return articles

def process_comment():
    pageBottom(driver)
    actions = ActionChains(driver)

    comments = driver.find_elements(By.CLASS_NAME,'commentItem-content')
    count = 0
    comment_list = []

    # 遍歷所有留言
    for i, comment in enumerate(comments):
        btn = driver.find_elements(By.CLASS_NAME,'commentItem-btn')[i]

        if btn.text.startswith("回覆 "):
            reply_num = int(btn.text.split(' ')[-1])
        else:
            reply_num = 0

        if reply_num > 5:
            actions.move_to_element(btn).click().perform()
            time.sleep(random.random() * SHORT_DELAY)
           
            reply_list_more = driver.find_elements(By.NAME, '查看更多')
            if reply_list_more:
                actions.move_to_element(reply_list_more[count]).click().perform()
                time.sleep(random.random() * SHORT_DELAY)
                count += 1

        context = comment.find_elements(By.TAG_NAME, 'span')[-1].text
        comment_list.append(context)

    replys = driver.find_elements(By.CLASS_NAME,'replyItem-content')
    for reply in replys:
        context = reply.find_element(By.TAG_NAME, 'span').text
        comment_list.append(context)        
    
    return comment_list

def fetch_comments(driver, url, threshold):
    driver.get(url)
    _ = WebDriverWait(driver, MAX_WAIT_TIME).until(
        EC.presence_of_element_located((By.CLASS_NAME, "titlebar-subtitle.titlebar-subtitle--border"))
    )
    
    time.sleep(1)   
    element = driver.find_elements(By.CLASS_NAME, "titlebar-text.header.header--md.header--primary.header--ellipsis1")
    comment_num = -1

    if element:
        print(element[0].text)
        comment_num = int(re.findall(r'\((.*?)\)', element[0].text)[0])
 
    print("CM:", comment_num)
    if int(comment_num) >= threshold:
        return True, process_comment()
    else:
        return False, []


for source in sources:
    options = Options()

    userAgent = ua().random
    options.add_argument(f'user-agent={userAgent}')

    driver = webdriver.Chrome(options=options)

    articles = fetch_articles(driver, source['url'], 10)

    all_news = []
    
    if os.path.exists('result.json'):
        result = json.load(open('result.json', 'r', encoding='utf-8'))
    else:
        result = {}

    for article in articles:
        href = article.get_attribute('href')
        title = article.find_element(By.TAG_NAME,'h3').text
        all_news.append({'title': title, 'href': href})

    result[source['name']] = []

    for news in all_news:
        id = news['href'].split('/')[-1]
        url = f"https://today.line.me/tw/v2/comment/article/{id}"
        status, comments = fetch_comments(driver, url, 20)
        if status:
            print(news['title'])
            print(news['href'])
            print(len(comments))
            print('=====================')
            result[source['name']].append({'title': news['title'], 'href': news['href'], 'comments': comments})

        json.dump(result, open('result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=4)

        time.sleep(random.random() * LONG_DELAY)
        
    # 關閉瀏覽器
    driver.quit()
