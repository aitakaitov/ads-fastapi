from fastapi import FastAPI
from models import *
from processing import classification
from processing import attribution
import config
import transformers
import torch

device = 'cuda' if torch.cuda.is_available() else 'cpu'


app = FastAPI()

model = transformers.AutoModelForSequenceClassification.from_pretrained(config.MODEL_FILE).to(device)
tokenizer = transformers.AutoTokenizer.from_pretrained(config.MODEL_FILE)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/classify")
async def classify(page: Page) -> Classification | Message:
    cls = classification.classify(page.text, model, tokenizer)
    if cls is None:
        return Message(code=501, message='The passed HTML contains no plain text')
    else:
        return Classification(is_advertisement=cls)


@app.post("/rationale")
async def attribute(page: Page) -> Rationales:
    return Rationales(rationales=attribution.rationales(page.text))
