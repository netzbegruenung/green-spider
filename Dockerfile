FROM python:3.7-alpine3.8

WORKDIR /workdir

ADD requirements.txt /workdir/

RUN echo "http://dl-4.alpinelinux.org/alpine/v3.8/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.8/community" >> /etc/apk/repositories && \
    apk update && \
    apk --no-cache add chromium chromium-chromedriver python3-dev build-base git py3-lxml libxml2 libxml2-dev libxslt libxslt-dev libffi-dev openssl-dev && \
    pip3 install --upgrade pip && \
    pip3 install -r requirements.txt && \
    apk del python3-dev build-base

ADD cli.py /workdir/
ADD manager /workdir/manager
ADD config /workdir/config
ADD checks /workdir/checks
ADD rating /workdir/rating
ADD spider /workdir/spider
ADD export /workdir/export
ADD job.py /workdir/
