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
    """
    Hello World
    """
    return {"message": "It works!"}


@app.post("/classify", response_model=Classification)
async def classify(page: Page, db: Session = Depends(get_db)):
    """
    Returns the classification of a page

    Caches the classification for future use
    
    Future requests for a classified page will return the cached classification

    If no text can be extracted from the page, returns 400
    """
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
    """
    Returns the rationales for ad-positive classification of a page:

    a list of sentences supporting the classification (5-10 sentences)

    Caches the rationales for the page and returns the cached rationales if available

    If the URL is not in the classification cache, returns 400

    If no text can be extracted from the page, returns 400
    """
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
    

@app.post("/domains/{domain}")
async def add_domain_cookies(request: DomainCacheRequest, domain: str, db: Session = Depends(get_db)):
    """
    Adds a URL for a domain to the cache

    If a URL is already cached for the domain, returns 400
    """
    # check if present
    cookie_url = crud.get_cookie_url_from_cache(db, domain)
    if cookie_url:
        raise HTTPException(status_code=400, detail='Cookies URL already in cache for domain')

    crud.add_domain_to_cache(db, domain, request.url)


@app.put("/domains/{domain}")
async def update_domain_cookies(request: DomainCacheRequest, domain: str, db: Session = Depends(get_db)):   
    """
    Updates a cached URL for a domain

    If the domain is not cached, returns 400
    """
    if not crud.update_domain_cache(db, domain, request.url):
        raise HTTPException(status_code=400, detail='Domain not in cache')



@app.get("/domains/{domain}", response_model=DomainCacheResponse)
async def get_domain_cookies(domain: str, db: Session = Depends(get_db)):
    """
    Retrieves a cached URL for the domain

    If the domain is not in cache, returns 400
    """     # check if present
    domain_data = crud.get_cookie_url_from_cache(db, domain)
    if not domain_data:
        raise HTTPException(status_code=400, detail='Cookies URL not in cache for domain')

    return DomainCacheResponse(url=domain_data.cookie_url)



#if __name__ == '__main__':
#    import uvicorn
#    uvicorn.run(app, host='127.0.0.1', port=8001)
