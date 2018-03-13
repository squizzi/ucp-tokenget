FROM jfloff/alpine-python:2.7-slim

MAINTAINER Kyle Squizzato: 'kyle.squizzato@docker.com'

WORKDIR /

RUN pip install --upgrade \
    pip \
    requests \
    validators

COPY ./tokenget.py /

ENTRYPOINT ["python", "./tokenget.py"]
