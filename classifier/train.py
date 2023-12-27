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
from peft import LoraConfig, prepare_model_for_kbit_training, get_peft_model, TaskType
from tqdm import tqdm
from sklearn.utils.class_weight import compute_class_weight
from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig, Trainer, TrainingArguments, TrainerCallback
from transformers.integrations import WandbCallback
from transformers.trainer_callback import TrainerControl, TrainerState
from utils import get_bnb_config, get_prompt
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score, recall_score, precision_score


import numpy as np
import evaluate
import os

tqdm.pandas()

# Step 1: Load the model
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

# Step 2: Load the dataset
def tokenize_function(examples):
    # max_length=None => use the model max length (it's actually the default)
    outputs = tokenizer(examples["text"], padding=True, truncation=True, max_length=512)
    return outputs

datasets = load_dataset('json', data_files={"train": './data/train.json', "test": './data/test.json'})

class_weight = compute_class_weight(class_weight='balanced', classes=np.unique(datasets['train']['labels']), y=datasets['train']['labels']).astype(np.float32)

tokenized_datasets = datasets.map(
    tokenize_function,
    batched=True,
    remove_columns=["text", "id"],
)

# Step 3: Define the training arguments
training_args = TrainingArguments(
    output_dir="./Taiwan_LLaMA_7B_Classifier_LoRA_Final",
    learning_rate=3e-4,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=5,
    save_strategy="steps",
    save_steps=150,
    logging_strategy="steps",
    logging_steps=150,
    remove_unused_columns=False,
)

# Step 4: Define the LoraConfig
model = prepare_model_for_kbit_training(model)
peft_config = LoraConfig(
    TaskType.SEQ_CLS,
    r=64,
    lora_alpha=64,
    lora_dropout=0.1,
    bias="none",
    modules_to_save=["score"]
)
model = get_peft_model(model, peft_config)
model.print_trainable_parameters()

# Step 5: Define the Trainer

# Not working for some reason
def compute_metrics(eval_pred):
    metric = evaluate.combine(["accuracy", "recall", "precision", "f1"]),
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)

class CustomCallback(WandbCallback):
    def __init__(self, trainer, tokenizer, eval_dataset) -> None:
        super().__init__()
        self._trainer = trainer
        self._tokenizer = tokenizer
        self.eval_dataset = eval_dataset

    def on_log(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, **kwargs):
        self._trainer.model.eval()
        eval_dataloader = self._trainer.get_eval_dataloader(self.eval_dataset)
        eval_dataloader = self._trainer.accelerator.prepare(eval_dataloader)
        eval_preds = None
        for step, inputs in enumerate(tqdm(eval_dataloader)):
            with torch.no_grad():
                inputs = self._trainer._prepare_inputs(inputs)
                if step == 0:
                    eval_preds = model(**inputs).logits.detach().cpu().numpy()
                else:
                    eval_preds = np.append(eval_preds, model(**inputs).logits.detach().cpu().numpy(), axis=0)
                
        eval_preds = np.argmax(eval_preds, axis=-1)

        acc = accuracy_score(self.eval_dataset['labels'], eval_preds)
        recall = recall_score(self.eval_dataset['labels'], eval_preds)
        f1 = f1_score(self.eval_dataset['labels'], eval_preds)
        precision = precision_score(self.eval_dataset['labels'], eval_preds)

        print("Accuracy:", acc, "Recall:", recall, "F1:", f1, "Precision:", precision)
        self._wandb.log({"Accuracy": acc, "Recall": recall, "F1": f1, "Precision": precision})
    

class CustomTrainer(Trainer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.pop('labels', None)
        if labels is None:
            raise ValueError("Labels not found in inputs")
        # forward pass
        output = model(**inputs)
        logits = output.logits
        # compute custom loss
        loss_fct = nn.CrossEntropyLoss(weight=torch.tensor(class_weight).cuda())
        loss = loss_fct(logits, labels)

        return (loss, (loss, logits)) if return_outputs else loss

trainer = CustomTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
    compute_metrics=compute_metrics,
)
trainer.add_callback(CustomCallback(trainer, tokenizer, tokenized_datasets["test"]))

trainer.train()

# Step 6: Save the model
model.save_pretrained("./Taiwan_LLaMA_7B_Classifier_LoRA_Final")
tokenizer.save_pretrained("./Taiwan_LLaMA_7B_Classifier_LoRA_Final")

