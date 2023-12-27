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

id2label = {0: "中性", 1: "惡意"}
label2id = {"中性": 0, "惡意": 1}

result = []
eval_preds = []
gt_labels = []

model.eval()

text = input("Test:")

with torch.no_grad():
    inputs = tokenizer(get_prompt(text), truncation=True, padding='max_length', max_length=512, return_tensors='pt')
    outputs = model.forward(**inputs)
    output_labels = [{'label': id2label[int(label)], 'score':float(max(score))} for label, score in zip(torch.argmax(outputs.logits, 1),  torch.softmax(outputs.logits, 1))]
    print(output_labels)

