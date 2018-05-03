

.PHONY: webapp

# Build docker image and run spider in Docker container
spider:
	docker pull python:3.6-alpine3.7
	docker build -t spider .
	docker run --rm -ti -v $(PWD)/webapp/dist/data:/out spider

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
