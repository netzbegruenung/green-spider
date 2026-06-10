IMAGE := ghcr.io/netzbegruenung/green-spider:latest

DB_ENTITY := spider-results

VERSION = $(shell git describe --exact-match --tags 2> /dev/null || git rev-parse HEAD)

.PHONY: dockerimage dockerimage-nocache dockerimage-multiarch spider export dryrun test

# Build docker image for the host architecture (loadable into the local Docker daemon).
dockerimage: VERSION
	docker build --progress plain -t $(IMAGE) .

dockerimage-nocache: VERSION
	docker build --progress plain --no-cache -t $(IMAGE) .

# Build and push a multi-arch (amd64 + arm64) image.
# Multi-platform output cannot be loaded into the local Docker daemon, so this
# target pushes directly to the registry. Requires a logged-in registry
# (docker login ghcr.io) and a docker-container buildx builder
# (docker buildx create --use).
dockerimage-multiarch: VERSION
	docker buildx build --progress plain \
		--platform linux/amd64,linux/arm64 \
		--push -t $(IMAGE) .


# Fill the queue with spider jobs, one for each site.
jobs:
	mkdir -p cache
	test -d cache/green-directory || git clone --depth 1 https://git.verdigado.com/NB-Public/green-directory.git cache/green-directory	
	git -C cache/green-directory fetch && git -C cache/green-directory pull
	docker compose rm -f manager
	docker compose up manager
	uv run rq info

# Spider a single URL and inspect the result.
# Example:
#   make dryrun ARGS="https://gruene-roesrath.de/"
dryrun:
	docker run --rm -ti \
	  -v $(PWD)/volumes/dev-shm:/dev/shm \
		-v $(PWD)/secrets:/secrets \
		-v $(PWD)/volumes/chrome-userdir:/opt/chrome-userdir \
		--shm-size=2g \
		$(IMAGE) \
		python3 cli.py \
			--credentials-path /secrets/datastore-writer.json \
			--loglevel debug \
			dryrun ${ARGS}

# Run the spider.
# OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES is a workaround for mac OS.
spider:
	PYTHONPATH=$(PWD) \
	OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES \
	JOB_TIMEOUT=100 \
	VIRTUAL_ENV= \
	uv run rq worker \
	--burst \
	--logging_level debug \
	high default low

export:
	docker run --rm -ti \
		-v $(PWD)/secrets:/secrets \
		-v $(PWD)/volumes/json-export:/json-export \
		$(IMAGE) \
		python3 cli.py \
			--credentials-path /secrets/datastore-reader.json \
			--loglevel debug \
			export --kind $(DB_ENTITY)

# run spider tests
test:
	docker run --rm \
	  -v $(PWD)/volumes/dev-shm:/dev/shm \
      -v $(PWD)/secrets:/secrets \
      -v $(PWD)/screenshots:/screenshots \
	  -v $(PWD)/volumes/chrome-userdir:/opt/chrome-userdir \
		$(IMAGE) \
			python3 -m unittest discover -p '*_test.py' -v

# Create local Python virtual environment (.venv) via uv
venv:
	uv sync

VERSION:
	@echo $(VERSION) > VERSION
