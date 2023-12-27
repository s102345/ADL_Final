"""
此程式會使用 selenium 去爬取巴哈姆特場外區新聞看板的文章
並將文章內容、留言、回覆存成 json 檔案
須注意此城市需要登入巴哈姆特帳號後將 BAHARUNE cookie 提供給 driver 才能爬取
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
import time
import random
from tqdm import tqdm
import json


# 設定標頭
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
}

COOKIE = {
    'name': 'BAHARUNE',
    'value': "{input your cookie here}",
}

MAX_PAGE_PER_ARTICLE = 10
POPULARITY_THRESHOLD = 5
NUM_OF_ARTICLE_PAGES = 2

TARGET_URL = 'https://forum.gamer.com.tw/B.php?bsn=60076&subbsn=16'

EXCLUDE_A_JS = """
var span = arguments[0];
var text = span.textContent;
var child = span.querySelector('a');
if (child) {
    text = text.replace(child.textContent, '');
}
return text;
"""


def get_article_url_list(driver):
    # 爬取新聞討論列表
    item_blocks = driver.find_elements(By.CLASS_NAME, 'b-list__row.b-list-item')

    # 爬取高於人氣閥值的文章網址
    article_url_list = []
    for item_block in item_blocks:
        popularity = item_block.find_element(By.CLASS_NAME, 'b-list__count__number').text.split('/')[0]

        if int(popularity) < POPULARITY_THRESHOLD:
            continue

        article_url = item_block.find_element(By.CLASS_NAME, 'b-list__main__title').get_attribute('href')
        article_url = article_url.split("&tnum")[0]
        article_url = f'https://forum.gamer.com.tw/{article_url}'
        article_url_list.append(article_url)

    return article_url_list


def get_comments(driver):
    # 拿取樓主元素
    main_post = driver.find_element(By.CLASS_NAME, 'c-section__main.c-post')

    # 計算原本留言數
    initial_comments = main_post.find_elements(By.CLASS_NAME, 'comment_content')
    initial_count = len(initial_comments)

    def comments_loaded(driver):
        current_comments = main_post.find_elements(By.CLASS_NAME, "comment_content")
        return len(current_comments) > initial_count

    # 點擊更多留言
    try:
        button = main_post.find_element(By.CLASS_NAME, 'more-reply')
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(button))
        button.click()
        WebDriverWait(driver, 10).until(comments_loaded)
    except NoSuchElementException:
        pass
    except Exception as e:
        print(e)
        pass

    # 爬取留言
    comments = []
    comment_blocks = main_post.find_elements(By.CLASS_NAME, 'comment_content')
    for comment_block in comment_blocks:
        comment_text = driver.execute_script(EXCLUDE_A_JS, comment_block)
        if comment_text == '':
            continue
        comments.append(comment_text)

    return comments


def get_replies(driver, article_url):
    # 取得回覆頁數
    article_pages = driver.find_element(By.CLASS_NAME, "BH-pagebtnA")
    article_pages = article_pages.find_elements(By.TAG_NAME, "a")
    last_page = int(article_pages[-1].text)

    # 爬取回覆
    replies = []
    for page in range(1, last_page + 1):
        driver.get(f"{article_url}&page={page}")
        time.sleep(0.5)
        reply_blocks = driver.find_elements(By.CSS_SELECTOR, 'section[id^="post_"]')

        # 對每一則回覆解析資料
        for reply_block in reply_blocks:
            reply_info = {}

            reply_info['floor'] = int(reply_block.find_element(By.CLASS_NAME, 'floor.tippy-gpbp').get_attribute('data-floor'))
            reply_info['content'] = reply_block.find_element(By.CLASS_NAME, 'c-article__content').text
            if reply_info['content'] == '':
                continue
            replies.append(reply_info)

        time.sleep(random.uniform(1, 3))

    return replies


def get_article_info(driver, article_url):
    # 爬取每一篇文章的內容
    driver.get(article_url)
    time.sleep(0.5)

    # 展示文章資訊
    article_title = driver.find_element(By.CLASS_NAME, 'c-post__header__title').text

    print(article_title)
    print(article_url)

    comments = get_comments(driver)
    print('留言數:', len(comments))

    replies = get_replies(driver, article_url)
    print('回覆數:', len(replies))

    # 一樓是文章內文
    article_info = {
        'title': article_title,
        'url': article_url,
        'content': replies[0]['content'],
        'comment': comments,
        'reply': [reply['content'] for reply in replies[1:]]
    }

    return article_info


if '__main__' == __name__:
    # 設定不載入圖片
    chrome_options = Options()
    chrome_options.add_argument('blink-settings=imagesEnabled=false')

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(TARGET_URL)
    driver.add_cookie(COOKIE)

    article_url_list = []
    for page in range(1, NUM_OF_ARTICLE_PAGES):
        driver.get(f"{TARGET_URL}&page={page}")
        time.sleep(0.5)
        url_list = get_article_url_list(driver)
        article_url_list.extend(url_list)
        time.sleep(0.5)

    result = []
    for article_url in tqdm(article_url_list):
        article_info = get_article_info(driver, article_url)
        result.append(article_info)

        # 每爬完 10 篇就存檔，避免中斷
        if len(result) % 10 == 0:
            with open(f'response.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)

    driver.close()

    with open('response.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
