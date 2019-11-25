IMAGE := quay.io/netzbegruenung/green-spider:latest

DB_ENTITY := spider-results

.PHONY: dockerimage spider export

# Build docker image
dockerimage:
	docker build -t $(IMAGE) .

# Create spider job queue
jobs:
	docker run --rm -ti \
		-v $(PWD)/secrets:/secrets \
		$(IMAGE) \
		--credentials-path /secrets/datastore-writer.json \
		--loglevel debug \
		jobs

# Run spider in docker image
spider:
	docker run --rm -ti \
	  -v $(PWD)/volumes/dev-shm:/dev/shm \
		-v $(PWD)/secrets:/secrets \
		-v $(PWD)/volumes/chrome-userdir:/opt/chrome-userdir \
		--shm-size=2g \
		$(IMAGE) \
		--credentials-path /secrets/datastore-writer.json \
		--loglevel debug \
		spider --kind $(DB_ENTITY) ${ARGS}

export:
	docker run --rm -ti \
		-v $(PWD)/secrets:/secrets \
		-v $(PWD)/volumes/json-export:/json-export \
		$(IMAGE) \
		--credentials-path /secrets/datastore-reader.json \
		--loglevel debug \
		export --kind $(DB_ENTITY)

# run spider tests
test:
	docker run --rm -ti \
	  -v $(PWD)/volumes/chrome-userdir:/opt/chrome-userdir \
		--entrypoint "python3" \
		$(IMAGE) \
		-m unittest discover -p '*_test.py' -v

