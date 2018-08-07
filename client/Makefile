WEBPACK := node_modules/.bin/webpack --no-color
WEBPACK_DEV_SERVER := node_modules/.bin/webpack-dev-server --no-color
ESLINT := node_modules/.bin/eslint -f unix
STYLELINT := node_modules/.bin/stylelint --custom-formatter ./stylelint-unix-formatter.js

.PHONY: build build-production

AUX := build/index.html build/api.conf.js

build: $(AUX)
	$(WEBPACK) --config webpack.dev.js

build-production: $(AUX)
	$(WEBPACK) --config webpack.prod.js

dev-server: $(AUX)
	$(WEBPACK_DEV_SERVER) --config webpack.dev.js

dev-server-production: $(AUX)
	$(WEBPACK_DEV_SERVER) --config webpack.prod.js

eslint:
	$(ESLINT) src/components/*.vue src/js/*.js src/*.js *.js *.json

csslint:
	$(STYLELINT) src/components/*.vue src/less/*.less


build/index.html: src/index.html
	-mkdir -p build
	cp $< $@

build/api.conf.js: src/api.conf.js
	cp $< $@
