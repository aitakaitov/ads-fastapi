from sqlalchemy.orm import Session

from utils.document_similarity import document_to_minhash, are_documents_same

from .schemas import *
from .config import Config

from . import models
from .database import SessionLocal, engine
from . import crud

from advertisement_processing import classification
from advertisement_processing import attribution

from utils.pickle_utils import from_binary_string
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

# ----------------------------------------- COOKIES -----------------------------------------

@app.post("/cookies/analyze", response_model=CookiesAnalysis)
async def analyze(url: Url, db: Session = Depends(get_db)):
    """
    Given a URL, downloads and analyzes the page. 
    
    If the page is cached, compares the page to the cached version and redoes the analysis if needed.
    
    Returns a list of entities with their associated short texts, and HTML to render (incl. a sidebar and JS code)
    """
    # TODO
    ...


@app.post("/cookies/select", response_model=CookiesAnalysis)
async def analyze(request: SelectEntityRequest, db: Session = Depends(get_db)):
    """
    Given page URL and the name of the selected entity, returns a re-rendered page

    If the page is not cached (it should be), returns 400
    """
    # TODO
    ...    

# ----------------------------------------- ADS CLASSIFICATION, RATIONALES -----------------------------------------

@app.post("/classify", response_model=Classification)
async def classify(page: Page, db: Session = Depends(get_db)):
    """
    Returns the classification of a page

    Caches the classification for future use

    Future requests for a classified page will return the cached classification

    If no text can be extracted from the page, returns 400
    """
    # check if the page is cac1hed
    page_info = crud.get_page(db, page.url)
    if page_info:
        print('classify - cached')
        # if it is, check if the page changed - if it did, update the minhash and is_advertisement stuff
        # then delete all rationales and force new ones on next request
        minhash = document_to_minhash(page.text)
        if not are_documents_same(minhash, page_info.minhash):
            print('documents not same')
            cls, minhash = classification.classify(page.text, model, tokenizer)
            crud.update_page_invalidate_rationales(db, page_info, cls, minhash)
            return Classification(is_advertisement=cls)

        print('documents same')
        return Classification(is_advertisement=page_info.is_advertisement)

    cls, minhash = classification.classify(page.text, model, tokenizer)
    if cls is None:
        raise HTTPException(status_code=400, detail='Page HTML contains no plain text')
    else:
        crud.add_page(db, is_advertisement=cls, url=page.url, minhash=minhash)
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

    if len(rationales) == 0:
        rationales = attribution.rationales(page.text, model, tokenizer)

    if rationales is None:
        raise HTTPException(status_code=400, detail='Page HTML contains no plain text')
    else:
        crud.add_rationales(db, rationales=rationales, url=page.url)
        return Rationales(rationales=rationales)


# ----------------------------------------- DOMAIN-URL CACHE -----------------------------------------


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
