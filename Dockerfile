FROM alpine:3.21@sha256:56fa17d2a7e7f168a043a2712e63aed1f8543aeafdcee47c58dcffe38ed51099

# Find an eligible version at https://dl-cdn.alpinelinux.org/alpine/v3.21/community/x86_64/
ARG CHROMIUM_VERSION=136.0.7103.113-r0

RUN echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/community" >> /etc/apk/repositories && \
    apk --update --no-cache add ca-certificates \
          chromium=$CHROMIUM_VERSION \
          chromium-chromedriver=$CHROMIUM_VERSION \
          py3-cryptography python3-dev py3-grpcio py3-wheel py3-pip py3-lxml py3-yaml \
          build-base git icu-libs libssl3 libxml2 libxml2-dev libxslt libxslt-dev \
          libffi-dev openssl-dev cargo

RUN apk info -v | sort

WORKDIR /workdir

# Execute time consuming compilations in a separate step
RUN python3 -m pip install libcst==0.4.10 sgmllib3k==1.0.0 --break-system-packages

ADD https://pki.google.com/roots.pem /google_roots.pem
ENV GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=/google_roots.pem

ADD requirements.txt /workdir/
RUN pip install -r requirements.txt --break-system-packages

RUN python3 -m pip freeze

ADD cli.py /workdir/
ADD manager /workdir/manager
ADD config /workdir/config
ADD checks /workdir/checks
ADD rating /workdir/rating
ADD spider /workdir/spider
ADD export /workdir/export
ADD job.py /workdir/
ADD VERSION /workdir/VERSION

ENV PYTHONPATH="/workdir"
