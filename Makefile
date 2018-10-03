IMAGE := quay.io/netzbegruenung/green-spider:latest

DB_ENTITY := spider-results

.PHONY: dockerimage

# Build docker image
dockerimage:
	docker build -t $(IMAGE) .

# Create spider job queue
spiderjobs: dockerimage
	docker run --rm -ti \
		-v $(PWD)/secrets:/secrets \
		$(IMAGE) \
		--credentials-path /secrets/datastore-writer.json \
		--loglevel info \
		jobs

# Run spider in docker image
spider: dockerimage
	docker run --rm -ti \
	  -v $(PWD)/dev-shm:/dev/shm \
		-v $(PWD)/webapp/dist/data:/out \
		-v $(PWD)/secrets:/secrets \
		$(IMAGE) \
		--credentials-path /secrets/datastore-writer.json \
		--loglevel debug \
		spider --kind $(DB_ENTITY)

export: dockerimage
	docker run --rm -ti \
		-v $(PWD)/export-json:/out \
		-v $(PWD)/secrets:/secrets \
		-v $(PWD)/export-siteicons:/icons \
		$(IMAGE) \
		--credentials-path /secrets/datastore-reader.json \
		--loglevel debug \
		export --kind $(DB_ENTITY)

# run spider tests
# FIXME
test: dockerimage
	docker run --rm -ti \
		--entrypoint "python3" \
		$(IMAGE) \
		-m unittest discover -p '*_test.py'

