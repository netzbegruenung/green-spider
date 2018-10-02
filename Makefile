

.PHONY: dockerimage

# Build docker image
dockerimage:
	docker build -t quay.io/netzbegruenung/green-spider:dev .

# Create spider job queue
spiderjobs: dockerimage
	docker run --rm -ti \
		-v $(PWD)/secrets:/secrets \
		quay.io/netzbegruenung/green-spider:dev \
		--credentials-path /secrets/datastore-writer.json \
		--loglevel info \
		jobs

# Run spider in docker image
spider: dockerimage
	docker run --rm -ti \
	  -v $(PWD)/dev-shm:/dev/shm \
		-v $(PWD)/webapp/dist/data:/out \
		-v $(PWD)/secrets:/secrets \
		quay.io/netzbegruenung/green-spider:dev \
		--credentials-path /secrets/datastore-writer.json \
		--loglevel debug \
		spider --kind spider-results-dev

export: dockerimage
	docker run --rm -ti \
		-v $(PWD)/export-json:/out \
		-v $(PWD)/secrets:/secrets \
		-v $(PWD)/export-siteicons:/icons \
		quay.io/netzbegruenung/green-spider:dev \
		--credentials-path /secrets/datastore-reader.json \
		--loglevel debug \
		export --kind spider-results-dev

# run spider tests
# FIXME
test: dockerimage
	docker run --rm -ti quay.io/netzbegruenung/green-spider:latest /spider_test.py
