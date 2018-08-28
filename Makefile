

.PHONY: dockerimage

# Build docker image
dockerimage:
	docker pull debian:stretch-slim
	docker build -t spider .

# Create spider job queue
spiderjobs: dockerimage
	docker run --rm -ti \
		-v $(PWD)/secrets:/secrets \
		spider spider.py \
		--credentials-path /secrets/datastore-writer.json \
		--loglevel debug \
		jobs

# Run spider in docker image
spider: dockerimage
	docker run --rm -ti \
		-v $(PWD)/webapp/dist/data:/out \
		-v $(PWD)/secrets:/secrets \
		spider spider.py \
		--credentials-path /secrets/datastore-writer.json \
		--loglevel debug \
		spider

# run spider tests
test: dockerimage
	docker run --rm -ti spider /spider_test.py
