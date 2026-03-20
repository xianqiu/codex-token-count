PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install uninstall

install:
	$(PIP) install -e .

uninstall:
	$(PIP) uninstall -y codex-token
