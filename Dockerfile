FROM alpine:3.14

WORKDIR /workdir

ADD requirements.txt /workdir/

RUN echo "http://dl-4.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories && \
    apk --update --no-cache add ca-certificates chromium chromium-chromedriver \
          python3-dev py3-grpcio py3-wheel py3-pip py3-lxml \
          build-base git libxml2 libxml2-dev libxslt libxslt-dev libffi-dev openssl-dev cargo && \
    pip install -r requirements.txt && \
    apk del build-base

# As alpine's py3-cryptography did not work as of alpine v3.14, we use this hack from
# https://github.com/pyca/cryptography/issues/3344#issuecomment-650845512
RUN LDFLAGS="-L/opt/openssl/lib -Wl,-rpath,/opt/openssl/lib" CFLAGS="-I/opt/openssl/include" pip3 install -U cryptography

ADD cli.py /workdir/
ADD manager /workdir/manager
ADD config /workdir/config
ADD checks /workdir/checks
ADD rating /workdir/rating
ADD spider /workdir/spider
ADD export /workdir/export
ADD job.py /workdir/
