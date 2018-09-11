FROM python:3.6-alpine3.7

# Note: we pin selenium to 3.8.0 because of https://github.com/SeleniumHQ/selenium/issues/5296
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.7/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.7/community" >> /etc/apk/repositories && \
    apk update && \
    apk --no-cache add chromium chromium-chromedriver python3-dev build-base git && \
    pip3 install --upgrade pip && \
    pip3 install selenium==3.8.0 GitPython PyYAML beautifulsoup4==4.6.0 requests==2.18.4 responses==0.9.0 smmap2==2.0.3 urllib3==1.22 google-cloud-datastore==1.7.0 tenacity==5.0.2 && \
    apk del python3-dev build-base

ADD spider.py /
ADD spider_test.py /
ADD data_export.py /

ENTRYPOINT ["python3"]
CMD ["/spider.py"]
