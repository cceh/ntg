PRJ_DIR     := prj/ntg/ntg
ROOT        := $(UNI_DIR)/$(PRJ_DIR)

#NTG_HOST    := ntg.cceh.uni-koeln.de
NTG_HOST    := ntg.uni-muenster.de
NTG_USER    := ntg

NTG         := $(NTG_USER)@$(NTG_HOST)
NTG_PRJ     := $(NTG):/home/$(NTG_USER)/prj/ntg/ntg
NTG_SERVER  := $(NTG_PRJ)/server
#NTG_CLIENT  := $(NTG):/var/www/ntg.cceh.uni-koeln.de
NTG_CLIENT  := $(NTG):/var/www/ntg

RSYNC       := /usr/bin/rsync -azv --exclude '*~'
SHELL       := /bin/bash
PYTHON      := /usr/bin/python3
MYSQL       := mysql --defaults-file=~/.my.cnf.ntg
BROWSER     := firefox
JSDOC       := jsdoc -c doc_src/jsdoc.conf.js
RSYNCPY     := $(RSYNC) --exclude "**/__pycache__"  --exclude "*.pyc"

PSQL_PORT   := 5432
PSQL        := psql -p $(PSQL_PORT)
PGDUMP      := pg_dump -p $(PSQL_PORT)

SERVER      := server
CLIENT      := client
SCRIPTS     := scripts
DOCS        := docs

JS_SRC      := $(wildcard $(CLIENT)/src/js/*.js)
VUE_SRC     := $(wildcard $(CLIENT)/src/components/*.vue $(CLIENT)/src/components/widgets/*.vue)

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

server:
	export PYTHONPATH=$(ROOT)/server:$(ROOT); \
	python3 -m server -vvv

common-clean:
	cd ntg_common ; make clean; cd ..

server-clean:
	cd server ; make clean; cd ..

docker-build: server-clean common-clean client-production
	cd docker; make build; cd ..

docker-run:
	cd docker; make run; cd ..

docker-push:
	cd docker; make push; cd ..

users:
	scripts/cceh/mk_users.py -vvv instance/_global.conf

psql_on_remote:
	psql -h $(NTG_HOST) -U $(NTG_USER) -d ntg_user

clean: client-clean
	find . -depth -name "*~" -delete

# sudo -u postgres psql
#
# CREATE USER ntg CREATEDB PASSWORD '<password>';
# CREATE DATABASE ntg_user OWNER ntg;
#
# CREATE DATABASE acts_ph4 OWNER ntg;
#
# \c acts_ph4
# CREATE SCHEMA ntg AUTHORIZATION ntg;
# ALTER DATABASE acts_ph4 SET search_path = ntg, public;
# CREATE EXTENSION mysql_fdw;
# GRANT USAGE ON FOREIGN DATA WRAPPER mysql_fdw TO ntg;
#
# GRANT CONNECT ON DATABASE acts_ph4 TO ntg_readonly;
# GRANT USAGE ON SCHEMA ntg TO ntg_readonly;
# GRANT SELECT ON ALL TABLES IN SCHEMA ntg TO ntg_readonly;
# \q

import_acts:
	-$(MYSQL) -e "DROP DATABASE ECM_ActsPh4"
	$(MYSQL) -e "CREATE DATABASE ECM_ActsPh4"
	cat ../dumps/ECM_ActsPh4_Final_20170712.dump | $(MYSQL) -D ECM_ActsPh4
	-$(MYSQL) -e "DROP DATABASE VarGenAtt_ActPh4"
	$(MYSQL) -e "CREATE DATABASE VarGenAtt_ActPh4"
	cat ../dumps/VarGenAtt_ActPh3_20170712.dump | $(MYSQL) -D VarGenAtt_ActPh4
	python3 -m scripts.cceh.import -vvv instance/acts_ph4.conf

import_cl:
	-$(MYSQL) -e "DROP DATABASE ECM_CL_Ph2"
	$(MYSQL) -e "CREATE DATABASE ECM_CL_Ph2"
	cat ../dumps/CL_export_vollstaendig.dump | $(MYSQL) -D ECM_CL_Ph2
	-$(MYSQL) -e "DROP DATABASE VG_CL_Ph2"
	$(MYSQL) -e "CREATE DATABASE VG_CL_Ph2"
	cat ../dumps/ECM_KB_2.dump | $(MYSQL) -D VG_CL_Ph2
	python3 -m scripts.cceh.import -vvv instance/cl_ph2.conf

import_john_ph1:
	-$(MYSQL) -e "DROP DATABASE DCPJohnWithFam"
	$(MYSQL) -e "CREATE DATABASE DCPJohnWithFam"
	zcat ../dumps/DCPJohnWithFam-9.sql | $(MYSQL) -D DCPJohnWithFam
	python3 -m scripts.cceh.import -vvv instance/john_ph1.conf

import_john_f1_ph1:
	-$(MYSQL) -e "DROP DATABASE DCPJohnFamily1"
	$(MYSQL) -e "CREATE DATABASE DCPJohnFamily1"
	cat ../dumps/DCPJohnFamily1.sql | $(MYSQL) -D DCPJohnFamily1
	python3 -m scripts.cceh.import -vvv instance/john_f1_ph1.conf

import_mark_ph1:
	-$(MYSQL) -e "DROP DATABASE ECM_Mark_Ph12"
	$(MYSQL) -e "CREATE DATABASE ECM_Mark_Ph12"
	cat ../dumps/ECM_Mk_CBGM_Milestone2.dump | $(MYSQL) -D ECM_Mark_Ph12
	python3 -m scripts.cceh.import -vvv instance/mark_ph12.conf

import_mark_ph2:
	-$(MYSQL) -e "DROP DATABASE ECM_Mark_Ph2"
	$(MYSQL) -e "CREATE DATABASE ECM_Mark_Ph2"
	cat ../dumps/ECM_Mk_Apparat_6.dump | $(MYSQL) -D ECM_Mark_Ph2
	python3 -m scripts.cceh.import -vvv instance/mark_ph2.conf

import_mark_ph22:
	-$(MYSQL) -e "DROP DATABASE ECM_Mark_Ph2"
	$(MYSQL) -e "CREATE DATABASE ECM_Mark_Ph2"
	bzcat ../dumps/ECM_Mk_Apparat_6.dump.bz2 | $(MYSQL) -D ECM_Mark_Ph2
	python3 -m scripts.cceh.import -vvv instance/mark_ph22.conf

import_nestle:
	-$(MYSQL) -e "DROP DATABASE Nestle29"
	$(MYSQL) -e "CREATE DATABASE Nestle29"
	bzcat ../dumps/Nestle29-2.dump.bz2 | $(MYSQL) -D Nestle29

import_2sam:
	-$(MYSQL) -e "DROP DATABASE 2Sam_Ph1"
	$(MYSQL) -e "CREATE DATABASE 2Sam_Ph1"
	bzcat ../dumps/2Sam_apparat_20200618.dump.bz2 | $(MYSQL) -D 2Sam_Ph1
	-$(MYSQL) -e "DROP DATABASE LXX_Leitzeile"
	$(MYSQL) -e "CREATE DATABASE LXX_Leitzeile"
	bzcat ../dumps/LXX.dump.bz2 | $(MYSQL) -D LXX_Leitzeile
	python3 -m scripts.cceh.import -vvv instance/2sam_ph1.conf

acts_ph4:
	python3 -m scripts.cceh.prepare -vvv instance/acts_ph4.conf
	python3 -m scripts.cceh.cbgm    -vvv instance/acts_ph4.conf

acts_ph5:
	$(PSQL) -d template1 -c "DROP DATABASE IF EXISTS acts_ph5"
	$(PSQL) -d template1 -c "CREATE DATABASE acts_ph5 WITH TEMPLATE acts_ph4 OWNER ntg"
	python3 -m scripts.cceh.cbgm    -vvv instance/acts_ph5.conf

cl:
	python3 -m scripts.cceh.prepare -vvv instance/cl_ph2.conf
	python3 -m scripts.cceh.cbgm    -vvv instance/cl_ph2.conf

john:
	python3 -m scripts.cceh.prepare -vvv instance/john_ph1.conf
	python3 -m scripts.cceh.cbgm    -vvv instance/john_ph1.conf

john_f1:
	python3 -m scripts.cceh.prepare -vvv instance/john_f1_ph1.conf
	python3 -m scripts.cceh.cbgm    -vvv instance/john_f1_ph1.conf

mark_ph1:
	python3 -m scripts.cceh.prepare -vvv instance/mark_ph12.conf
	python3 -m scripts.cceh.cbgm    -vvv instance/mark_ph12.conf

mark_ph2:
	python3 -m scripts.cceh.prepare -vvv instance/mark_ph2.conf
	python3 -m scripts.cceh.cbgm    -vvv instance/mark_ph2.conf

mark_ph22:
	python3 -m scripts.cceh.prepare -vvv instance/mark_ph22.conf
	python3 -m scripts.cceh.cbgm    -vvv instance/mark_ph22.conf

2sam_ph1:
	python3 -m scripts.cceh.prepare -vvv instance/2sam_ph1.conf
	python3 -m scripts.cceh.cbgm    -vvv instance/2sam_ph1.conf

DBS := acts_ph3 acts_ph4 acts_ph5 john_ph1 john_f1_ph1 mark_ph1 mark_ph12 mark_ph2 mark_ph22 cl_ph2 2sam_ph1


#################
define TEMPLATE =

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

prepare_$(1):
	python3 -m scripts.cceh.prepare -vvv instance/$(1).conf

cbgm_$(1):
	python3 -m scripts.cceh.cbgm -vvv instance/$(1).conf

load_$(1):
	scp $(NTG_PRJ)/backups/saved_edits_$(1)_`date -I`.xml.gz backups/
	zcat backups/saved_edits_$(1)_`date -I`.xml.gz | python3 -m scripts.cceh.load_edits -vvv -i - instance/$(1).conf

backup_custom_$(1):
	mkdir -p backups/db
	$(PGDUMP) -Fc $(1) > backups/db/$(1).`date -I`.custom.dump

backup_sql_$(1):
	mkdir -p backups/db
	$(PGDUMP) $(1) | gzip > backups/db/$(1).`date -I`.sql.gz

backup_custom_all : backup_custom_$(1)

backup_sql_all : backup_sql_$(1)

endef

$(foreach db,$(DBS),$(eval $(call TEMPLATE,$(db))))
################


upload_client: client-production
	$(RSYNC) --exclude "api.conf.js" $(CLIENT)/build/* $(NTG_CLIENT)/

upload_server:
	$(RSYNCPY) ntg_common   $(NTG_PRJ)/
	$(RSYNCPY) server       $(NTG_PRJ)/

upload_scripts:
	$(RSYNCPY) --exclude "active_databases" scripts/cceh $(NTG_PRJ)/scripts/
	$(RSYNC)   Makefile     $(NTG_PRJ)/

get_remote_backups:
	mkdir -p backups/db
	$(RSYNC) $(NTG_PRJ)/backups/db backups/


lint: pylint eslint csslint

pylint:
	-pylint --rcfile=pylintrc server ntg_common

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


doc_src/jsdoc/structure.json: $(JS_SRC) $(VUE_SRC)
	mkdir -p doc_src/jsdoc/
	$(JSDOC) -X $^ > $@

docs: doc_src/jsdoc/structure.json
	cd doc_src && $(MAKE) -e html
	cp doc_src/_config.yml $(DOCS)/

doccs:
	$(RM) -r docs/*
	$(MAKE) docs

jsdoc: doc_src/jsdoc/structure.json

sqlacodegen:
	sqlacodegen mysql:///ECM_ActsPh4?read_default_group=ntg
	sqlacodegen mysql:///VarGenAtt_ActPh4?read_default_group=ntg

%.gzip : %
	gzip < $? > $@

install-prerequisites:
	sudo apt-get install apache2 libapache2-mod-wsgi-py3 \
		postgresql \
		python3 python3-pip \
	    git make graphviz
	sudo pip3 install --upgrade pip
	sudo pip3 install --upgrade -r server/requirements.txt
	sudo pip3 install --upgrade -r scripts/cceh/requirements.txt

install-prerequisites-dev:
	sudo apt-get install mariadb-client mariadb-server libpq-dev postgresql-11-mysql-fdw npm plantuml
	sudo pip3 install --upgrade \
		sphinx sphinx_rtd_theme sphinx_js sphinxcontrib-plantuml

#	yum install python34-pip python34-pylint mysql-devel python34-devel node mysql_fdw_10 postgresql10-server
#	pip3 install -U setuptools
