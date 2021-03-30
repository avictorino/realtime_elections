FROM python:3.8-slim
RUN mkdir /app
WORKDIR /app
ADD . /app

ENV TZ="America/Sao_Paulo"

RUN \
 apt-get update && \
 pip install --upgrade pip && \
 pip install gunicorn

RUN python3 -m pip install -r requirements.txt