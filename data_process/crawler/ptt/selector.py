"""
這個腳本會將crawer爬出的ptt各版的內容依照目標數量進行比例分配，
例如八卦版crawer在前50頁爬出10k資料，而在棒球版爬出1k資料，
則八卦與棒球的混和比例為10:1
"""
import os, json, random


max_label = 20000

all_count = 0
cate_num = {}
for file in os.listdir('origin'):
    with open(os.path.join('origin',file), 'r', encoding="utf-8") as f:
        jsons = f.readlines()
        file_size = len(jsons)-1
        all_count += file_size
        cate_num[file] = file_size

cate_quota = {}
for key,value in cate_num.items():
    cate_quota[key] = int(value/all_count*max_label)

for file in os.listdir('origin'):
    with open(os.path.join('origin',file), 'r', encoding="utf-8") as f:
        jsons = f.readlines()
    datas = []
    for json_data in jsons:
        datas.append(json.loads(json_data))
    
    with open(os.path.join('filtered',file), 'w+', encoding="utf-8") as json_file:
        for val in random.sample(range(cate_num[file]),cate_quota[file]):
            new_obj = {
                "source":datas[val]['place'],
                "title":datas[val]['title'],
                "context":datas[val]['context'],
                "text":datas[val]['text'],
                "label":[]
            }
            str = (json.dumps(new_obj,ensure_ascii=False))
            json_file.write(str)
            json_file.write('\n')