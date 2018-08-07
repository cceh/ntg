RSYNC       := /usr/bin/rsync -azv --exclude '*~'
SHELL       := /bin/bash
PYTHON      := /usr/bin/python3
MYSQL       := mysql --defaults-file=~/.my.cnf.ntg
BROWSER     := firefox

NTG_VM      := ntg.cceh.uni-koeln.de
NTG_USER    := ntg
NTG         := $(NTG_USER)@$(NTG_VM)
NTG_ROOT    := $(NTG):/home/$(NTG_USER)/prj/ntg/ntg
PSQL_PORT   := 5432
SERVER      := server
STATIC      := $(SERVER)/static

PSQL        := psql -p $(PSQL_PORT)
PGDUMP      := pg_dump -p $(PSQL_PORT)

TRANSLATIONS    := de            # space-separated list of translations we have eg. de fr

NTG_SERVER  := $(NTG_ROOT)/$(SERVER)
NTG_STATIC  := $(NTG_ROOT)/$(STATIC)

LESS        := $(wildcard $(SERVER)/less/*.less)
CSS         := $(patsubst $(SERVER)/less/%.less, $(STATIC)/css/%.css, $(LESS))
CSS_GZ      := $(patsubst %, %.gzip, $(CSS))

JS_SRC      := $(wildcard $(SERVER)/js/*.js)
JS          := $(patsubst $(SERVER)/js/%.js, $(STATIC)/js/%.js, $(JS_SRC))
JS_GZ       := $(patsubst %, %.gzip, $(JS))

PY_SOURCES  := scripts/cceh/*.py ntg_common/*.py server/*.py

.PHONY: upload vpn server client restart psql
.PHONY: js css doc jsdoc sphinx lint pylint eslint csslint

css: $(CSS)

js:	$(JS)

restart: js css server

server:
	python3 -m server.server -vv

client:
	cd client; make build; cd ..

client-production:
	cd client; make build-production; cd ..

dev-server:
	cd client; make dev-server; cd ..

users:
	scripts/cceh/mk_users.py -vvv server/instance/_global.conf

clean:
	find . -depth -name "*~" -delete

psql:
	ssh -f -L 1$(PSQL_PORT):localhost:$(PSQL_PORT) $(NTG_USER)@$(NTG_VM) sleep 120
	sleep 1
	psql -h localhost -p 1$(PSQL_PORT) -U $(NTG_USER) acts_ph4

import_acts:
	$(MYSQL) -e "DROP DATABASE ECM_ActsPh4"
	$(MYSQL) -e "CREATE DATABASE ECM_ActsPh4"
	mysql --defaults-file=~/.my.cnf.ntg -D ECM_ActsPh4      < ../dumps/ECM_ActsPh4.dump
	$(MYSQL) -e "DROP DATABASE VarGenAtt_ActPh4"
	$(MYSQL) -e "CREATE DATABASE VarGenAtt_ActPh4"
	mysql --defaults-file=~/.my.cnf.ntg -D VarGenAtt_ActPh4 < ../dumps/VarGenAtt_ActPh4.dump

import_john:
	$(MYSQL) -e "DROP DATABASE DCPJohnWithFam"
	$(MYSQL) -e "CREATE DATABASE DCPJohnWithFam"
	cat ../dumps/DCPJohnWithFam-8.sql | mysql --defaults-file=~/.my.cnf.ntg -D DCPJohnWithFam

import_mark:
	-$(MYSQL) -e "DROP DATABASE ECM_Mark_Ph1"
	$(MYSQL) -e "CREATE DATABASE ECM_Mark_Ph1"
	for dump in ../dumps/Mk1to16dump/*.dump; do \
		mysql --defaults-file=~/.my.cnf.ntg -D ECM_Mark_Ph1 < $${dump} ; \
	done

acts:
	python3 -m scripts.cceh.prepare4cbgm -vvv server/instance/acts_ph4.conf

john:
	python3 -m scripts.cceh.prepare4cbgm -vvv server/instance/john_ph1.conf

mark:
	python3 -m scripts.cceh.prepare4cbgm -vvv server/instance/mark_ph1.conf


define UPLOAD_TEMPLATE =

BOOK = $(firstword $(subst _, ,$(1)))

upload_dbs_from_work: upload_$$(BOOK)_from_work

upload_dbs_from_home: upload_$$(BOOK)_from_home

# from work (fast connection, pipe to psql on the host)
upload_$$(BOOK)_from_work:
	$(PGDUMP) --clean --if-exists $(1) | psql -h $(NTG_VM) -U $(NTG_USER) $(1)

# from home (slow connection, upload bzipped file and then ssh to host)
upload_$$(BOOK)_from_home:
	-rm /tmp/$(1).pg_dump.sql.bz2
	$(PGDUMP) --clean --if-exists $(1) | bzip2 > /tmp/$(1).pg_dump.sql.bz2
	scp /tmp/$(1).pg_dump.sql.bz2 $(NTG_USER)@$(NTG_VM):~/

endef

DBS := acts_ph4 john_ph1 mark_ph1

$(foreach db,$(DBS),$(eval $(call UPLOAD_TEMPLATE,$(db))))

upload_scripts:
	$(RSYNC) --exclude "**/__pycache__"  --exclude "*.pyc"  ntg_common $(NTG_ROOT)/
	$(RSYNC) --exclude "**/instance/**"                     server     $(NTG_ROOT)/

diff_affinity_acts:
	scripts/cceh/sqldiff.sh acts_ph4 "select ms_id1, ms_id2, affinity, common, equal, older, newer, unclear from affinity where rg_id = 94 order by ms_id1, ms_id2" | less

diff_affinity_john:
	scripts/cceh/sqldiff.sh john_ph1 "select ms_id1, ms_id2, affinity, common, equal, older, newer, unclear from affinity where rg_id = 72 order by ms_id1, ms_id2" | less

lint: pylint eslint csslint

pylint:
	-pylint $(PY_SOURCES)

# eslint:
# 	./node_modules/.bin/eslint -f unix $(JS_SRC)
#
# csslint: css
# 	csslint --ignore="adjoining-classes,box-sizing,ids,order-alphabetical,overqualified-elements,qualified-headings" $(CSS)

csslint:
	cd client ; make csslint ; cd ..

eslint:
	cd client ; make eslint ; cd ..

doc: sphinx

.PRECIOUS: doc_src/%.jsgraph.dot

doc_src/%.jsgraph.dot : $(STATIC)/js/%.js $(JS)
	madge --dot $< | \
	sed -e "s/static\/js\///g" \
		-e "s/static\/node_modules\///g" \
		-e "s/G {/G {\ngraph [rankdir=\"LR\"]/" > $@

doc_src/%.nolibs.jsgraph.dot : doc_src/%.jsgraph.dot
	sed -e "s/.*\/.*//g" $< > $@

%.jsgraph.png : %.jsgraph.dot
	dot -Tpng $? > $@

jsgraphs: doc_src/coherence.jsgraph.dot doc_src/comparison.jsgraph.dot \
			doc_src/coherence.nolibs.jsgraph.dot doc_src/comparison.nolibs.jsgraph.dot

sphinx: jsgraphs
	-rm docs/_images/*
	cd doc_src; make html; cd ..

jsdoc: js
	jsdoc -c jsdoc.json -d jsdoc -a all $(JS_SRC) && $(BROWSER) jsdoc/index.html

sqlacodegen:
	sqlacodegen mysql:///ECM_ActsPh4?read_default_group=ntg
	sqlacodegen mysql:///VarGenAtt_ActPh4?read_default_group=ntg

$(STATIC)/js/%.js : $(SERVER)/js/%.js
	./node_modules/.bin/babel $? --out-file $@ --source-maps

$(STATIC)/css/%.css : $(SERVER)/less/%.less
	lessc --global-var="BS=\"$(STATIC)/node_modules/bootstrap/less\"" --autoprefix="last 2 versions" $? $@

%.gzip : %
	gzip < $? > $@

install-prerequisites:
	sudo apt-get install apache2 libapache2-mod-wsgi-py3 \
		postgresql libpg-dev postgresql-10-mysql-fdw \
		mysql default-libmysqlclient-dev \
		python3 python3-pip graphviz git plantuml
	sudo pip3 install --upgrade pip
	sudo pip3 install --upgrade \
		numpy networkx matplotlib pillow \
		psycopg2 mysqlclient sqlalchemy sqlalchemy-utils intervals \
		flask babel flask-babel flask-sqlalchemy jinja2 flask-user \
		sphinx sphinx_rtd_theme sphinx_js sphinxcontrib-plantuml \
	yarn
