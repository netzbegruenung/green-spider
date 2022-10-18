FROM alpine:3.15.0

WORKDIR /workdir

ADD requirements.txt /workdir/

RUN echo "http://dl-4.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories && \
    apk --update --no-cache add ca-certificates chromium chromium-chromedriver py3-cryptography \
          python3-dev py3-grpcio py3-wheel py3-pip py3-lxml \
          build-base git libxml2 libxml2-dev libxslt libxslt-dev libffi-dev openssl-dev cargo && \
    pip install -r requirements.txt && \
    apk del build-base

ADD cli.py /workdir/
ADD manager /workdir/manager
ADD config /workdir/config
ADD checks /workdir/checks
ADD rating /workdir/rating
ADD spider /workdir/spider
ADD export /workdir/export
ADD job.py /workdir/
