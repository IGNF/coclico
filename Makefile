testing:
	python -m pytest ./test -s --log-cli-level DEBUG

install:
	mamba env update -n coclico -f environment.yml

install-precommit:
	pre-commit install
