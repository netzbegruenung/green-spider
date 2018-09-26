

.PHONY: dockerimage

# Build docker image
dockerimage:
	docker build -t quay.io/netzbegruenung/green-spider:latest .

# Create spider job queue
spiderjobs: dockerimage
	docker run --rm -ti \
		-v $(PWD)/secrets:/secrets \
		quay.io/netzbegruenung/green-spider:latest spider.py \
		--credentials-path /secrets/datastore-writer.json \
		--loglevel info \
		jobs

# Run spider in docker image
spider: dockerimage
	docker run --rm -ti \
	  -v $(PWD)/dev-shm:/dev/shm \
		-v $(PWD)/webapp/dist/data:/out \
		-v $(PWD)/secrets:/secrets \
		quay.io/netzbegruenung/green-spider:latest spider.py \
		--credentials-path /secrets/datastore-writer.json \
		--loglevel debug \
		spider

export: dockerimage
	docker run --rm -ti \
		-v $(PWD)/export-json:/out \
		-v $(PWD)/secrets:/secrets \
		-v $(PWD)/export-siteicons:/icons \
		quay.io/netzbegruenung/green-spider:latest \
		data_export.py /secrets/datastore-reader.json

# run spider tests
test: dockerimage
	docker run --rm -ti quay.io/netzbegruenung/green-spider:latest /spider_test.py
