

.PHONY: webapp dockerimage

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

# export JSON data for the webapp
export: dockerimage
	docker run --rm -ti \
		-v $(PWD)/webapp/dist/data:/out \
		-v $(PWD)/secrets:/secrets \
		-v $(PWD)/docs/siteicons:/icons \
		spider data_export.py /secrets/datastore-reader.json

# NodeJS modules for the webapp creation
webapp/node_modules:
	cd webapp && npm install

# Build webapp
webapp: webapp/node_modules
	cd webapp && npx webpack --config webpack.config.js
	cp -r webapp/dist/* ./docs/
	cp webapp/node_modules/tooltipster/dist/css/tooltipster.bundle.min.css ./docs/css/
	rm webapp/dist/bundle.js

# Run a dev server for the webapp
serve-webapp:
	cd docs && ../venv/bin/python -m http.server
