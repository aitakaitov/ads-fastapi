# FastAPI backend for advertisement detection

## Build and run

<code>docker build -t fastapi-backend .</code>

<code>docker run --name fastapi-server -p 8001:8001 fastapi-backend</code>

The server inside the container runs on <code>0.0.0.0:8001</code>.

## Endpoints

<code>GET /</code> : returns Hello World

<code>POST /classify</code> : classifies a webpage

<code>POST /rationale</code> : returns rationales if a page is already classified

<code>POST /domains/{domain}</code> : add cookies URL for a domain

<code>GET /domains/{domain}</code> : get cookies URL of a domain

<code>PUT /domains/{domain}</code> : set new cookies url for a domain


See SwaggerDoc at <code>address:port/docs#</code>
