import json
import requests
import spacy
from fastapi import FastAPI, HTTPException, Response
from api.main import app
import uvicorn


# with open('00aeee6ba6b317446df0a895c1034a9dc6c25d1a1ae94364d59894d62175d65d.json', 'r', encoding='utf-8') as f:
#     data = json.loads(f.read())
#
#
# obj = {
#     'text': data['data'],
#     'url': data['url']
# }
#
# response = requests.post('http://127.0.0.1:8002/classify', json=obj)
#
# response2 = requests.post('http://127.0.0.1:8002/rationale', json=obj)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8001)
