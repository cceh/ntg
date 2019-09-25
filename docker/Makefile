.PHONY: backup build clean run

build: Makefile
	rm -rf server ntg_common
	cp -a ../server ../ntg_common .
	cp -a ../client/build/* ./client
	cp -a ../scripts/cceh/* ./scripts
	docker build -f Dockerfile.db --tag=cceh/ntg-db-server  .
	docker build -f Dockerfile    --tag=cceh/ntg-app-server .

backup:
	mkdir -p backup
	pg_dump --format custom acts_ph4 -n ntg -T "ntg.original_*" -T "ntg.tmp_*" > backup/acts_ph4.dump

run: build
	docker-compose up

cbgm: build
	docker-compose run ntg-app-server cbgm

push:
	docker push cceh/ntg-app-server:latest
	docker push cceh/ntg-db-server:latest

clean:
	docker container stop $$(docker container ls -a -q)
	docker container rm   $$(docker container ls -a -q)
	docker network prune -f
	docker rmi -f $$(docker images --filter dangling=true -qa)
	docker volume rm $$(docker volume ls --filter dangling=true -q)
	docker rmi -f $$(docker images -qa)

clean-volume:
	docker-compose down --volumes
