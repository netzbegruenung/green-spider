IMAGE := quay.io/netzbegruenung/green-spider:latest

DB_ENTITY := spider-results

.PHONY: dockerimage spider export

# Build docker image
dockerimage:
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

