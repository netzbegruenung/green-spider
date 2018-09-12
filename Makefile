

.PHONY: dockerimage

# Build docker image
dockerimage:
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
	  -v $(PWD)/dev-shm:/dev/shm \
		-v $(PWD)/webapp/dist/data:/out \
		-v $(PWD)/secrets:/secrets \
		spider spider.py \
		--credentials-path /secrets/datastore-writer.json \
		--loglevel info \
		spider

# run spider tests
test: dockerimage
	docker run --rm -ti spider /spider_test.py
