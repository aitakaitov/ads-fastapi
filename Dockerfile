FROM debian:latest

# copy scripts to image
RUN mkdir fastapi-server
ADD api fastapi-server/api
ADD processing fastapi-server/processing
ADD small-e-czech-ads fastapi-server/small-e-czech-ads
COPY requirements.txt fastapi-server/requirements.txt 

# install python
RUN apt update
RUN apt install python3 -y
RUN python3 --version
RUN apt install python3-pip -y
#RUN apt install python3.11-venv -y

# install packages
WORKDIR /fastapi-server

# someone really wants me to use venv, but I can't be bothered 
RUN rm -rf /usr/lib/python3.11/EXTERNALLY-MANAGED
RUN python3 -m pip install -r requirements.txt

# entrypoint
ENTRYPOINT [ "uvicorn", "api.main:app", "--port", "8001", "--host", "0.0.0.0" ]