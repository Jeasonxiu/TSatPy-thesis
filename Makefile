
DIR := $(shell pwd)
VERSION := $(shell grep version $(DIR)/TSatPy/__init__.py | cut -d "'" -f 2)
PIDFILE := /tmp/tsatpy.pid

test:
	nosetests --nocapture --with-coverage --cover-erase --cover-package=TSatPy --cover-html --cover-html-dir=coverage_report

controller:
	twistd --nodaemon --pidfile $PIDFILE --python $(DIR)/bin/tsat_controller.py

lint:
	pep8 TSatPy
	pylint TSatPy --disable=C0103

doc:
	sphinx-apidoc -A "Daniel Robert Couture" -V $(VERSION) -F -o docs/ TSatPy/
	make -C "$(DIR)/docs" html

ipython:
	make -C "$(DIR)/notebooks" ipython

clean:
	rm -r $(DIR)/docs/*
	rm -r $(DIR)/coverage_report/*

thesis:
	make -C "$(DIR)/tex" thesis
	make -C "$(DIR)/tex" view
