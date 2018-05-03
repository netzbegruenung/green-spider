FROM python:3.6-alpine3.7

ADD requirements.txt /
RUN pip install -r requirements.txt

RUN apk add --no-cache git

ADD spider.py /

ENTRYPOINT ["python", "spider.py"]
