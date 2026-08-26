import os
from dotenv import load_dotenv

from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from settings import SENTIMENT_ANALYSIS

model_name = SENTIMENT_ANALYSIS
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
sentiment_analysis = pipeline("text-classification", model=model_name, tokenizer=tokenizer)

def analyze_emotion(text_to_analyze):
    print(sentiment_analysis(text_to_analyze))
    return sentiment_analysis(text_to_analyze)[0]["label"]