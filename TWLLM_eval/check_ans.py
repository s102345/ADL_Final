import json
from tqdm import tqdm

with open('result_TWLLM_yn.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

out = []
for line in tqdm(data):
    title, text = line['title'], line['text']
    print('Title: ', title, '\n', 'Text: ', text)
    print('Response: ', line['ans'])
    ans = input('Your answer is ')
    line['manual_ans'] = ans
    out.append(line)

    with open('result_TWLLM_manual.json', 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=4)

