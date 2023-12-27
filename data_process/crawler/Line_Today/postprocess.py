import json 
import time
import random
import copy
from selenium import webdriver
from fake_useragent import UserAgent as ua   
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


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

def fetch_contexts(driver, url):
    driver.get(url)
    _ = WebDriverWait(driver, MAX_WAIT_TIME).until(
        EC.presence_of_element_located((By.TAG_NAME,'p'))
    )
   
    contexts = driver.find_elements(By.TAG_NAME,'p')
    tmp = []

    for context in contexts:
        tmp.append(context.text)

    return '\n'.join(tmp)

with open('result.json', encoding='utf-8') as json_file:
    result = json.load(json_file)

total = 0
data = []#copy.deepcopy(result)
"""
options = Options()
userAgent = ua().random
options.add_argument(f'user-agent={userAgent}')

driver = webdriver.Chrome(options=options)

for key, value in result.items():
    for i, v in enumerate(value):
        context = fetch_contexts(driver, v['href'])
        data[key][i]['context'] = context
        time.sleep(random.random() * LONG_DELAY)
"""

for key, value in result.items():
    for v in value:    
        for c in v['comments']:
            data.append({
                'title': v['title'],
                'context': v['context'],
                'text': c,
                'label': 0,
                'source': v['href'],
            })

with open('data.json', 'w', encoding='utf-8') as outfile:
    json.dump(data, outfile, ensure_ascii=False, indent=4)

"""
for key, value in result.items():
    total += len(value)

for key, value in result.items():
    for v in value:
        print(v['href'])
        
        for c in v['comments']:
            print()
            data.append({
                'text': c,
                'label': 0 
            })
"""

