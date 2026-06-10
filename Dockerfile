FROM alpine:3.23@sha256:5b10f432ef3da1b8d4c7eb6c487f2f5a8f096bc91145e68878dd4a5019afde11

# Find an eligible version at (must exist for every target architecture):
# https://dl-cdn.alpinelinux.org/alpine/v3.23/community/x86_64/
# https://dl-cdn.alpinelinux.org/alpine/v3.23/community/aarch64/
ARG CHROMIUM_VERSION=149.0.7827.53-r0

RUN echo "http://dl-cdn.alpinelinux.org/alpine/v3.23/community" >> /etc/apk/repositories && \
    apk --update --no-cache add ca-certificates \
          chromium=$CHROMIUM_VERSION \
          chromium-chromedriver=$CHROMIUM_VERSION \
          python3 python3-dev \
          build-base git icu-libs libssl3 libxml2 libxml2-dev libxslt libxslt-dev \
          libffi-dev openssl-dev cargo

RUN apk info -v | sort

# Copy the uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /usr/local/bin/

WORKDIR /workdir

ADD https://pki.google.com/roots.pem /google_roots.pem
ENV GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=/google_roots.pem

# Configure uv for container-friendly behavior
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/workdir/.venv

# Install dependencies in a separate, cacheable layer
COPY pyproject.toml uv.lock /workdir/
RUN uv sync --frozen --no-install-project

# Make the venv's binaries available on PATH
ENV PATH="/workdir/.venv/bin:$PATH" \
    VIRTUAL_ENV="/workdir/.venv"

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
