

.PHONY: webapp

# Python venv for running the spider locally
venv:
	virtualenv -p python3 venv
	venv/bin/pip3 install -r requirements.txt

spider: venv
	venv/bin/python ./spider.py

webapp/node_modules:
	cd webapp && npm install

# Build webapp
webapp: webapp/node_modules
	cd webapp && npx webpack --config webpack.config.js
	rm -rf ./docs
	cp -r webapp/dist ./docs
