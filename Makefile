export SHELL:=$(shell which bash)

.PHONY: all clean test

all:
	python -m pip install -e .

test:
	python -m unittest

clean:
	rm -rf build/ dist/ {src/,}*.egg-info/ $$(find src tests -name __pycache__) .ruff_cache/
