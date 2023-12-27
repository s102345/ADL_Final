from transformers import BitsAndBytesConfig
import torch
import random


def get_prompt(instruction: str) -> str:
    '''Format the instruction as a prompt for LLM.'''
    return f"你是一個訓練有素的人工智慧助理，負責處理分類問題。在這個情境中，你的任務是讀取輸入，並根據內容判斷是否為惡意言論，輸出「中性」或是「惡意」。請確保你的回答是有用的、安全的、詳細的，並保持禮貌。USER:{instruction} ASSISTANT: 在分析用戶的輸入後，"
    
def get_bnb_config() -> BitsAndBytesConfig:
    '''Get the BitsAndBytesConfig.'''
    nf4_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16
    )

    return nf4_config