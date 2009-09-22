
NAME = collecty
VERSION = 0.0.1

DESTDIR =
PYTHON_VER := $(shell python --version 2>&1 | awk '{ print $$NF }')
PYTHON_DIR = $(DESTDIR)/usr/lib/python$(PYTHON_VER)/site-packages/$(NAME)/

all:

dist:
	git archive --format=tar --prefix=$(NAME)-$(VERSION)/ HEAD | gzip -9 \
		> $(NAME)-$(VERSION).tar.gz

install:
	-mkdir -pv $(PYTHON_DIR)
	cp -rvf collecty $(PYTHON_DIR)
	install -v -m 755 colletyd $(DESTDIR)/usr/sbin

	-mkdir -pv $(DESTDIR)/var/rrd

	# Install configuration
	-mkdir -pv $(DESTDIR)/etc/$(NAME)/
	cp -vf example.conf $(DESTDIR)/etc/$(NAME)/$(NAME).conf
