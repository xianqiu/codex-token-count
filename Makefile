UV ?= uv

.PHONY: install uninstall run test lock

install:
	$(UV) tool install .

uninstall:
	$(UV) tool uninstall codex-token

run:
	codex-token

test:
	$(UV) run python -m unittest discover -s tests

lock:
	$(UV) lock
