FROM alpine:3.16.2

RUN echo "http://dl-4.alpinelinux.org/alpine/edge/main/" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/edge/community/" >> /etc/apk/repositories && \
    apk --update --no-cache add ca-certificates chromium chromium-chromedriver py3-cryptography \
          python3-dev py3-grpcio py3-wheel py3-pip py3-lxml py3-yaml \
          build-base git icu-libs libssl1.1 libssl3 libxml2 libxml2-dev libxslt libxslt-dev libffi-dev openssl-dev cargo

WORKDIR /workdir

# Execute time consuming compilations in a separate step
RUN python3 -m pip install libcst==0.4.7 sgmllib3k==1.0.0

ADD requirements.txt /workdir/
RUN pip install -r requirements.txt

RUN python3 -m pip freeze

ADD cli.py /workdir/
ADD manager /workdir/manager
ADD config /workdir/config
ADD checks /workdir/checks
ADD rating /workdir/rating
ADD spider /workdir/spider
ADD export /workdir/export
ADD job.py /workdir/
