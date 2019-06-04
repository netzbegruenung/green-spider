FROM python:3.6-alpine3.8

# Note: we pin selenium to 3.8.0 because of https://github.com/SeleniumHQ/selenium/issues/5296
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.8/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.8/community" >> /etc/apk/repositories && \
    apk update && \
    apk --no-cache add chromium chromium-chromedriver python3-dev build-base git py3-lxml libxml2 libxml2-dev libxslt libxslt-dev libffi-dev openssl-dev && \
    pip3 install --upgrade pip && \
    pip3 install selenium==3.8.0 GitPython PyYAML beautifulsoup4==4.6.0 html-similarity==0.3.2 httpretty==0.9.4 feedparser==5.2.1 pyopenssl==18.0.0 requests==2.18.4 responses==0.9.0 smmap2==2.0.3 urllib3==1.22 google-cloud-datastore==1.7.0 tenacity==5.0.2 && \
    apk del python3-dev build-base

ADD cli.py /
ADD config /config
ADD jobs /jobs
ADD checks /checks
ADD rating /rating
ADD spider /spider
ADD export /export

ENTRYPOINT ["python3", "/cli.py"]
