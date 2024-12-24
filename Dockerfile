FROM python:3.12-slim

ARG APP_VERSION= 1.0.1
MAINTAINER Safonov

LABEL version=$APP_VERSION
EXPOSE 8000

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh
