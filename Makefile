
NAME = collecty

DESTDIR =
PYTHON_VER := $(shell python --version 2>&1 | awk '{ print $$NF }')
PYTHON_DIR = $(DESTDIR)/usr/lib/python$(PYTHON_VER)/site-packages/$(NAME)/

all:

install:
	-mkdir -pv $(PYTHON_DIR)
	cp -rvf collecty $(PYTHON_DIR)
	install -v -m 755 colletyd $(DESTDIR)/usr/sbin

	-mkdir -pv $(DESTDIR)/var/rrd

	# Install configuration
	-mkdir -pv $(DESTDIR)/etc/$(NAME)/
	cp -vf example.conf $(DESTDIR)/etc/$(NAME)/$(NAME).conf
