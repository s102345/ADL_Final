"""
將巴哈姆特爬蟲結果轉換成我們要的格式
"""
import json
from tqdm import tqdm


def postprocess(data):
    """
    "source"    (required)
    "title"     (optional)
    "context"   (optional)
    "text"      (required)
    "label"     (left blank)
    """
    result = []
    for article in tqdm(data):
        text_list = []
        text_list.extend(article['comment'])
        text_list.extend(article['reply'])

        count = 0
        for text in text_list:
            if count >= 120:
                break
            article_info = {
                'source': article['url'],
                'title': article['title'],
                'context': article['content'],
                'text': text,
                'label': ''
            }
            result.append(article_info)
            count = count + 1

        if len(result) > 15000:
            break

    return result


if __name__ == '__main__':

    with open(f'response.json', 'r', encoding='utf-8') as f:
        rawdata = json.load(f)

    print(f"共有 {len(rawdata)} 篇文章")

    # 轉換成我們要的格式
    result = postprocess(rawdata)

    print(f"共有 {len(result)} 筆資料")

    with open('result_1226.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
