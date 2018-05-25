

.PHONY: webapp dockerimage

# Build docker image
dockerimage:
	docker pull debian:stretch-slim
	docker build -t spider .

# Run spider in docker image
spider: dockerimage
	docker run --rm -ti \
		-v $(PWD)/webapp/dist/data:/out \
		-v $(PWD)/docs/siteicons:/icons \
		spider

test: dockerimage
	docker run --rm -ti spider /spider_test.py

screenshots: venv
	docker pull netzbegruenung/green-spider-screenshotter:latest
	venv/bin/python ./screenshots.py

webapp/node_modules:
	cd webapp && npm install

# Build webapp
webapp: webapp/node_modules
	cd webapp && npx webpack --config webpack.config.js
	rm -rf ./docs/*
	cp -r webapp/dist/* ./docs/

serve-webapp:
	cd docs && ../venv/bin/python -m http.server
