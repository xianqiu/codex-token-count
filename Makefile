PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install test smoke smoke-trend smoke-projects

install:
	$(PIP) install -e .

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

smoke:
	codex-token summary

smoke-trend:
	codex-token trend

smoke-projects:
	codex-token project
