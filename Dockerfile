FROM python:3.6-alpine3.9

ADD requirements.txt /

# Note: we pin selenium to 3.8.0 because of https://github.com/SeleniumHQ/selenium/issues/5296
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.9/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.9/community" >> /etc/apk/repositories && \
    apk update && \
    apk --no-cache add chromium chromium-chromedriver python3-dev build-base git py3-lxml libxml2 libxml2-dev libxslt libxslt-dev libffi-dev openssl-dev && \
    pip3 install --upgrade pip && \
    pip3 install -r requirements.txt && \
    apk del python3-dev build-base

ADD cli.py /
ADD config /config
ADD jobs /jobs
ADD checks /checks
ADD rating /rating
ADD spider /spider
ADD export /export

ENTRYPOINT ["python3", "/cli.py"]
