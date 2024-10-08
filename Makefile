testing:
	python -m pytest ./test -s --log-cli-level DEBUG

install:
	mamba env update -n coclico -f environment.yml

install-precommit:
	pre-commit install

##############################
# Docker
##############################

PROJECT_NAME=ghcr.io/ignf/coclico
VERSION=`python -m coclico.version`

docker-build:
	docker build -t ${PROJECT_NAME}:${VERSION} -f Dockerfile .

docker-test:
	docker run --rm -it ${PROJECT_NAME}:${VERSION} python -m pytest -s

docker-remove:
	docker rmi -f `docker images | grep ${PROJECT_NAME} | tr -s ' ' | cut -d ' ' -f 3`

docker-deploy:
	docker push ${PROJECT_NAME}:${VERSION}

