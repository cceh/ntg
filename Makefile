NTG_HOST    := ntg.cceh.uni-koeln.de
NTG_USER    := ntg

NTG         := $(NTG_USER)@$(NTG_HOST)
NTG_PRJ     := $(NTG):/home/$(NTG_USER)/prj/ntg/ntg
NTG_SERVER  := $(NTG_PRJ)/server
NTG_CLIENT  := $(NTG):/var/www/ntg.cceh.uni-koeln.de

RSYNC       := /usr/bin/rsync -azv --exclude '*~'
SHELL       := /bin/bash
PYTHON      := /usr/bin/python3
MYSQL       := mysql --defaults-file=~/.my.cnf.ntg
BROWSER     := firefox
JSDOC       := node client/node_modules/jsdoc/jsdoc.js -c jsdoc.conf.js
RSYNCPY     := $(RSYNC) --exclude "**/__pycache__"  --exclude "*.pyc"

PSQL_PORT   := 5432
PSQL        := psql -p $(PSQL_PORT)
PGDUMP      := pg_dump -p $(PSQL_PORT)

SERVER      := server
CLIENT      := client
SCRIPTS     := scripts
DOCS        := docs

JS_SRC      := `find $(CLIENT)/src -name '*.js'`
VUE_SRC     := $(wildcard $(CLIENT)/src/components/*.vue)

PY_SOURCES  := scripts/cceh/*.py ntg_common/*.py


.PHONY: client server upload vpn psql
.PHONY: lint pylint eslint csslint
.PHONY: docs jsdoc sphinxdoc

client:
	cd client; make build; cd ..

client-production:
	cd client; make build-production; cd ..

client-clean:
	cd client; make clean; cd ..

dev-server:
	cd client; make dev-server; cd ..
	cd server; make server; cd ..

dev-server-production:
	cd client; make dev-server-production; cd ..
	cd server; make server; cd ..

# cd server; make server; cd ..
server:
	python3 -m server.server -vvv

users:
	scripts/cceh/mk_users.py -vvv server/instance/_global.conf

clean: client-clean
	find . -depth -name "*~" -delete

psql:
	ssh -f -L 1$(PSQL_PORT):localhost:$(PSQL_PORT) $(NTG) sleep 120
	sleep 1
	psql -h localhost -p 1$(PSQL_PORT) -U $(NTG_USER) acts_ph4

# sudo -u postgres psql
#
# CREATE USER ntg CREATEDB PASSWORD '<password>';
# CREATE DATABASE ntg_user OWNER ntg;
# CREATE DATABASE acts_ph4 OWNER ntg;
# \c acts_ph4
# CREATE EXTENSION mysql_fdw;
# GRANT USAGE ON FOREIGN DATA WRAPPER mysql_fdw TO ntg;
# \q

import_acts:
	-$(MYSQL) -e "DROP DATABASE ECM_ActsPh4"
	$(MYSQL) -e "CREATE DATABASE ECM_ActsPh4"
	cat ../dumps/ECM_ActsPh4_Final_20170712.dump | $(MYSQL) -D ECM_ActsPh4
	-$(MYSQL) -e "DROP DATABASE VarGenAtt_ActPh4"
	$(MYSQL) -e "CREATE DATABASE VarGenAtt_ActPh4"
	cat ../dumps/VarGenAtt_ActPh3_20170712.dump | $(MYSQL) -D VarGenAtt_ActPh4
	python3 -m scripts.cceh.import -vvv server/instance/acts_ph4.conf

import_john:
	-$(MYSQL) -e "DROP DATABASE DCPJohnWithFam"
	$(MYSQL) -e "CREATE DATABASE DCPJohnWithFam"
	gunzip -c ../dumps/DCPJohnWithFam-8.sql | $(MYSQL) -D DCPJohnWithFam
	python3 -m scripts.cceh.import -vvv server/instance/john_ph1.conf

import_john_f1:
	-$(MYSQL) -e "DROP DATABASE DCPJohnFamily1"
	$(MYSQL) -e "CREATE DATABASE DCPJohnFamily1"
	cat ../dumps/DCPJohnFamily1.sql | $(MYSQL) -D DCPJohnFamily1
	python3 -m scripts.cceh.import -vvv server/instance/john_f1_ph1.conf

import_mark:
	-$(MYSQL) -e "DROP DATABASE ECM_Mark_Ph1"
	$(MYSQL) -e "CREATE DATABASE ECM_Mark_Ph1"
	cat ../dumps/ECM_Mk_CBGM.dump | $(MYSQL) -D ECM_Mark_Ph1
	python3 -m scripts.cceh.import -vvv server/instance/mark_ph1.conf

import_nestle:
	-$(MYSQL) -e "DROP DATABASE Nestle29"
	$(MYSQL) -e "CREATE DATABASE Nestle29"
	cat ../dumps/Nestle29.dump | $(MYSQL) -D Nestle29

acts:
	python3 -m scripts.cceh.prepare -vvv server/instance/acts_ph4.conf
	python3 -m scripts.cceh.cbgm    -vvv server/instance/acts_ph4.conf

john:
	python3 -m scripts.cceh.prepare -vvv server/instance/john_ph1.conf
	python3 -m scripts.cceh.cbgm    -vvv server/instance/john_ph1.conf

john_f1:
	python3 -m scripts.cceh.prepare -vvv server/instance/john_f1_ph1.conf
	python3 -m scripts.cceh.cbgm    -vvv server/instance/john_f1_ph1.conf

mark:
	python3 -m scripts.cceh.prepare -vvv server/instance/mark_ph1.conf
	python3 -m scripts.cceh.cbgm    -vvv server/instance/mark_ph1.conf

load_mark:
	scp $(NTG_PRJ)/backups/* backups/
	python3 -m scripts.cceh.load_edits -i backups/saved_edits_mark_ph1_`date -I`.xml -vvv server/instance/mark_ph1.conf

define UPLOAD_TEMPLATE =

upload_dbs_from_work: upload_$(1)_from_work

upload_dbs_from_home: upload_$(1)_from_home

# from work (fast connection, pipe to psql on the host)
upload_$(1)_from_work:
	$(PGDUMP) --clean --if-exists $(1) | psql -h $(NTG_HOST) -U $(NTG_USER) $(1)

# from home (slow connection, upload bzipped file and then ssh to host)
#   bunzip2 -c acts_ph4.pg_dump.sql.bz2 | psql -d acts_ph4
upload_$(1)_from_home:
	-rm /tmp/$(1).pg_dump.sql.bz2
	$(PGDUMP) --clean --if-exists $(1) | bzip2 > /tmp/$(1).pg_dump.sql.bz2
	scp /tmp/$(1).pg_dump.sql.bz2 $(NTG_USER)@$(NTG_HOST):~/

endef

DBS := acts_ph4 john_ph1 john_f1_ph1 mark_ph1

$(foreach db,$(DBS),$(eval $(call UPLOAD_TEMPLATE,$(db))))

upload_client:
	$(RSYNC) --exclude "api.conf.js" $(CLIENT)/build/* $(NTG_CLIENT)/

upload_server:
	$(RSYNCPY)                            ntg_common $(NTG_PRJ)/
	$(RSYNCPY) --exclude "**/instance/**" server     $(NTG_PRJ)/

upload_scripts:
	$(RSYNC) --exclude "**/__pycache__"  --exclude "*.pyc"  scripts/cceh $(NTG_PRJ)/scripts/

diff_affinity_acts:
	scripts/cceh/sqldiff.sh acts_ph4 "select ms_id1, ms_id2, affinity, common, equal, older, newer, unclear from affinity where rg_id = 94 order by ms_id1, ms_id2" | less

diff_affinity_john:
	scripts/cceh/sqldiff.sh john_ph1 "select ms_id1, ms_id2, affinity, common, equal, older, newer, unclear from affinity where rg_id = 72 order by ms_id1, ms_id2" | less

lint: pylint eslint csslint

pylint:
	cd server; make pylint; cd ..
	-pylint $(PY_SOURCES)

csslint:
	cd client ; make csslint ; cd ..

eslint:
	cd client ; make eslint ; cd ..

.PRECIOUS: doc_src/%.jsgraph.dot

doc_src/%.jsgraph.dot : $(CLIENT)/src/js/%.js
	madge --dot $< | \
	sed -e "s/src\/js\///g" \
		-e "s/src\/node_modules\///g" \
		-e "s/G {/G {\ngraph [rankdir=\"LR\"]/" > $@

doc_src/%.nolibs.jsgraph.dot : doc_src/%.jsgraph.dot
	sed -e "s/.*\/.*//g" $< > $@

%.jsgraph.png : %.jsgraph.dot
	dot -Tpng $? > $@

jsgraphs: doc_src/coherence.jsgraph.dot doc_src/comparison.jsgraph.dot \
			doc_src/coherence.nolibs.jsgraph.dot doc_src/comparison.nolibs.jsgraph.dot

docs: sphinxdoc

sphinxdoc:
	-rm $(DOCS)/_images/*
	python3 -msphinx -c . -T -a -E -b html -d $(DOCS)/doctrees doc_src $(DOCS)
	cp doc_src/_config.yml $(DOCS)/
	@echo
	@echo "Build finished. The HTML pages are in $(DOCS)."

jsdoc:
	$(JSDOC) -d jsdoc -a all $(JS_SRC) $(VUE_SRC) && $(BROWSER) jsdoc/index.html

sqlacodegen:
	sqlacodegen mysql:///ECM_ActsPh4?read_default_group=ntg
	sqlacodegen mysql:///VarGenAtt_ActPh4?read_default_group=ntg

%.gzip : %
	gzip < $? > $@

install-prerequisites:
	sudo apt-get install apache2 libapache2-mod-wsgi-py3 \
		postgresql libpg-dev postgresql-10-mysql-fdw \
		mysql default-libmysqlclient-dev \
		python3 python3-pip \
	    git make npm graphviz plantuml
	sudo pip3 install --upgrade pip
	sudo pip3 install --upgrade \
		numpy networkx matplotlib pillow \
		psycopg2 mysqlclient sqlalchemy sqlalchemy-utils intervals \
		flask babel flask-babel flask-sqlalchemy jinja2 flask-user \
		sphinx sphinx_rtd_theme sphinx_js sphinxcontrib-plantuml \
