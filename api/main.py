from sqlalchemy.orm import Session

from .schemas import *
from .config import Config

from . import models
from .database import SessionLocal, engine
from . import crud

from processing import classification
from processing import attribution

from fastapi import FastAPI, Depends, HTTPException
import transformers
import torch
import nltk

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

device = 'cuda' if torch.cuda.is_available() else 'cpu'

model = transformers.AutoModelForSequenceClassification.from_pretrained(Config.MODEL_FILE).to(device)
tokenizer = transformers.AutoTokenizer.from_pretrained(Config.MODEL_FILE)

nltk.download('punkt')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "It works!"}


@app.post("/classify", response_model=Classification)
async def classify(page: Page, db: Session = Depends(get_db)):
    page_info = crud.get_page(db, page.url)
    if page_info:
        return Classification(is_advertisement=page_info.is_advertisement)

    cls = classification.classify(page.text, model, tokenizer)
    if cls is None:
        raise HTTPException(status_code=400, detail='Page HTML contains no plain text')
    else:
        crud.add_page(db, is_advertisement=cls, url=page.url)
        return Classification(is_advertisement=cls)


@app.post("/rationale", response_model=Rationales)
async def attribute(page: Page, db: Session = Depends(get_db)):
    rationales = crud.get_rationales(db, page.url)

    if rationales is None:
        raise HTTPException(status_code=400, detail='URL has not been classified yet')

    if len(rationales) > 0:
        return Rationales(rationales=[r.text for r in rationales])
    
    rationales = attribution.rationales(page.text, model, tokenizer)
    if rationales is None:
        raise HTTPException(status_code=400, detail='Page HTML contains no plain text')
    else:
        crud.add_rationales(db, rationales=rationales, url=page.url)
        return Rationales(rationales=[r.text for r in rationales])


#if __name__ == '__main__':
#    import uvicorn
#    uvicorn.run(app, host='127.0.0.1', port=8001)
