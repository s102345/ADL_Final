import json
import random
import os
from sklearn.model_selection import train_test_split
#Merge admin.json and all.json

data_folder = os.listdir('datasets') 
data_json = []

for folder in data_folder:
    with open(os.path.join('datasets', folder)) as f:
        data_json.append(json.load(f))

dataTmp = []
for dj in data_json:
    dataTmp.extend(dj)

data = []

for datapiece in dataTmp:
    if len(datapiece['label']) == 0: continue

    if 'title' in list(datapiece.keys()):
        text = "標題：" + datapiece['title'] + " 內容：" + '\n' + datapiece['text'] 
    else:
        text = "標題：" + datapiece['Name'] + " 內容：" + '\n' + datapiece['text'] 

    tmp = {'id': len(data), 
           'text': text, 
           'labels': "中性" if datapiece['label'] == "中性" else "惡意" }
    data.append(tmp)

p, n = 0, 0

for datapiece in data:
    if datapiece['labels'] == '中性': p+=1
    else: n+=1

print("中性", p, "惡意", n)
print("比例", p/n)

regularData = []
meanData = []

for datapiece in data:
    if len(datapiece['labels']) == 0: continue

    if datapiece['labels'] == '中性':
        regularData.append(datapiece)
    else:
        meanData.append(datapiece)

newData = []
newData.extend(meanData)

tmp = random.sample(regularData, len(meanData) * 2)
newData.extend(tmp)

p, n = 0, 0
for datapiece in newData:
    if datapiece['labels'] == '中性': p+=1
    else: n+=1

print("中性", p, "惡意", n)
print("比例", p/n)

random.shuffle(newData)
#json.dump(newData, open('data.json', 'w'), ensure_ascii=False, indent=4)

train_dataset, test_dataset = train_test_split(newData, test_size=0.1, random_state=42)

os.makedirs('data', exist_ok=True)

t = []
for i in range(len(train_dataset)):
    t.append({'text': train_dataset[i]['text'], 'labels': 1 if train_dataset[i]['labels'] == "惡意" else 0, "id": train_dataset[i]['id']})

with open('./data/train.json', 'w') as f:
    json.dump(t, f, ensure_ascii=False, indent=4)

t = []
for i in range(len(test_dataset)):
    t.append({'text': test_dataset[i]['text'], 'labels': 1 if test_dataset[i]['labels'] == "惡意" else 0, "id": test_dataset[i]['id']})

with open('./data/test.json', 'w') as f:
    json.dump(t, f, ensure_ascii=False, indent=4)
