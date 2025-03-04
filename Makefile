# Inspired by: https://blog.mathieu-leplatre.info/tips-for-your-makefile-with-python.html

PYMODULE := project_name
TESTS := tests
INSTALL_STAMP := .install.stamp
UV := $(shell command -v uv 2> /dev/null)
MYPY := $(shell command -v mypy 2> /dev/null)

.DEFAULT_GOAL := help

.PHONY: all
all: install lint test

.PHONY: help
help:
	@echo "Please use 'make <target>', where <target> is one of"
	@echo ""
	@echo "  install     install packages and prepare environment"
	@echo "  lint        run the code linters"
	@echo "  test        run all the tests"
	@echo "  all         install, lint, and test the project"
	@echo "  clean       remove all temporary files listed in .gitignore"
	@echo ""
	@echo "Check the Makefile to know exactly what each target is doing."
	@echo "Most actions are configured in 'pyproject.toml'."

install: $(INSTALL_STAMP)
$(INSTALL_STAMP): pyproject.toml
	@if [ -z $(UV) ]; then echo "uv could not be found. See https://docs.astral.sh/uv/"; exit 2; fi
	$(UV) run pip install --upgrade pip setuptools
	$(UV) sync
	touch $(INSTALL_STAMP)

.PHONY: lint
lint: $(INSTALL_STAMP)
    # Configured in pyproject.toml
    # Skips mypy if not installed
    # 
    # $(UV) run black --check $(TESTS) $(PYMODULE) --diff
	@if [ -z $(MYPY) ]; then echo "Mypy not found, skipping..."; else echo "Running Mypy..."; $(UV) run mypy $(PYMODULE) $(TESTS); fi
	@echo "Running Ruff..."; $(UV) run ruff . --fix

.PHONY: test
test: $(INSTALL_STAMP)
    # Configured in pyproject.toml
	$(UV) run pytest

.PHONY: clean
clean:
    # Delete all files in .gitignore
	git clean -Xdf
