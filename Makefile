IMAGE := ghcr.io/netzbegruenung/green-spider:latest

DB_ENTITY := spider-results

VERSION = $(shell git describe --exact-match --tags 2> /dev/null || git rev-parse HEAD)

.PHONY: dockerimage spider export

# Build docker image
dockerimage: VERSION
	docker build --progress plain -t $(IMAGE) .

# Fill the queue with spider jobs, one for each site.
jobs:
	docker run --rm -ti \
		-v $(PWD)/secrets:/secrets \
		$(IMAGE) \
		python cli.py \
			--credentials-path /secrets/datastore-writer.json \
			--loglevel debug \
			manager

# Run spider in docker image
spider:
	docker run --rm -ti \
	  -v $(PWD)/volumes/dev-shm:/dev/shm \
		-v $(PWD)/secrets:/secrets \
		-v $(PWD)/volumes/chrome-userdir:/opt/chrome-userdir \
		--shm-size=2g \
		$(IMAGE) \
		python3 cli.py \
			--credentials-path /secrets/datastore-writer.json \
			--loglevel debug \
			spider --kind $(DB_ENTITY) ${ARGS}

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

# Create Python virtual environment
venv:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt

VERSION:
	@echo $(VERSION) > VERSION
