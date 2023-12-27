from transformers import AutoModelForCausalLM, AutoTokenizer
from utils import get_bnb_config, get_prompt
import torch
import json
from tqdm import tqdm

def generate_response(prompt, model, tokenizer, max_length=512):
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to('cuda:0')
    output = model.generate(input_ids, max_length = max_length)
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    return response

def main():
    model_name = 'Taiwan_LLaMA_7B'
    with open('data/vertify.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    quantization_config = get_bnb_config()
    torch_dtype = torch.bfloat16

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        torch_dtype=torch_dtype,
        local_files_only=True
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    out_json = []
    for line in tqdm(data):
        title, text = line['title'], line['text']
        instruction = f'標題：{title} 內文：{text}'
        prompt = get_prompt(instruction)
        response = generate_response(prompt, model, tokenizer, 820)
        # print("Generated Response:", response)
        ans = response.split('ASSISTANT:')[-1]
        out_json.append({'title':title, 'text':text, 'labels':line['labels'], 'ans':ans})
    with open('result_TWLLM.json', 'w') as f:
        json.dump(out_json, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
