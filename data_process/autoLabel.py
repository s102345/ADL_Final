# coding=utf-8
# Copyright 2023 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from dataclasses import dataclass, field
from typing import Optional

import torch
from accelerate import Accelerator
from datasets import load_dataset
from peft import LoraConfig, prepare_model_for_kbit_training, PeftModel, TaskType
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding, Trainer, TrainingArguments, DefaultDataCollator
from utils import get_bnb_config, get_prompt
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score, recall_score, precision_score
import json
import numpy as np
import evaluate

tqdm.pandas()

quantization_config = get_bnb_config()
torch_dtype = torch.bfloat16

model = AutoModelForSequenceClassification.from_pretrained(
    './Taiwan_LLaMA_7B',
    num_labels=2,
    quantization_config=quantization_config,
    torch_dtype=torch_dtype,
    local_files_only=True
)
model.config.pad_token_id = model.config.eos_token_id


tokenizer = AutoTokenizer.from_pretrained(
    './Taiwan_LLaMA_7B',
    local_files_only=True,
)
tokenizer.pad_token = tokenizer.eos_token

model = PeftModel.from_pretrained(model, './Taiwan_LLaMA_7B_Classifier_LoRA/checkpoint-1800')

datasets = load_dataset('json', data_files={"train": './merged.json', "test": './merged.json'})

test_dataset = datasets['test']
test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=1)

#inputs = input("Test:")
#inputs = tokenizer(inputs, truncation=True, padding='max_length', max_length=512, return_tensors='pt')
id2label = {0: "中性", 1: "惡意"}
label2id = {"中性": 0, "惡意": 1}

result = []
eval_preds = []

model.eval()

for i, batch in enumerate(tqdm(test_dataset)):
    with torch.no_grad():
        if batch['label'] == "":
            inputs = tokenizer("標題" + batch['title'] + " 內容：" + batch['text'], truncation=True, padding='max_length', max_length=512, return_tensors='pt')
            outputs = model.forward(**inputs)
            pred, score = torch.argmax(outputs.logits, 1), torch.softmax(outputs.logits, 1)
            pred = int(pred)
            score = score.tolist()[0] 
            confidence = score[pred]
            eval_preds.append(pred)
            tmp = {'id': batch['id'], 'title': batch['title'], 'context': batch['context'], 'text': batch['text'], 'source': batch['source'], 'label': id2label[pred], 'confidence': float(confidence)}
            result.append(tmp)
        else:
            tmp = {'id': batch['id'], 'title': batch['title'], 'context': batch['context'], 'text': batch['text'], 'source': batch['source'], 'label': batch['label'], 'confidence': 1.0}
            result.append(tmp)

with open('result.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)


