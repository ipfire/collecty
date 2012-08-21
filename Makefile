###############################################################################
#                                                                             #
# collecty - A system statistics collection daemon for IPFire                 #
# Copyright (C) 2012 IPFire development team                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

PACKAGE_NAME    = collecty
PACKAGE_VERSION = 0.0.1

DESTDIR    =
PREFIX     = /usr
BINDIR     = $(PREFIX)/bin
LOCALEDIR  = $(PREFIX)/share/locale
UNITDIR    = $(PREFIX)/lib/systemd/system

PYTHON_VER := $(shell python -c "import platform; print '.'.join(platform.python_version_tuple()[:2])")
PYTHON_DIR = $(DESTDIR)/usr/lib/python$(PYTHON_VER)/site-packages/

###
# Translation stuff
###
# A list of all files that need translation
TRANSLATION_FILES = $(shell find collecty -type f -name "*.py") collectyd

POT_FILE = po/$(PACKAGE_NAME).pot
PO_FILES = $(wildcard po/*.po)
MO_FILES = $(patsubst %.po,%.mo,$(PO_FILES))

.PHONY: all
all: $(MO_FILES)

.PHONY: pot
pot: $(POT_FILE)

.PHONY: dist
dist:
	git archive --format=tar --prefix=$(NAME)-$(VERSION)/ HEAD | gzip -9 \
		> $(NAME)-$(VERSION).tar.gz

.PHONY: install
install: $(MO_FILES)
	-mkdir -pv $(PYTHON_DIR)
	cp -rvf collecty $(PYTHON_DIR)
	install -v -m 755 collectyd $(DESTDIR)$(BINDIR)

	# Install configuration
	-mkdir -pv $(DESTDIR)/etc/$(PACKAGE_NAME)
	cp -vf example.conf $(DESTDIR)/etc/$(PACKAGE_NAME)/$(PACKAGE_NAME).conf

	# Install translation files.
	-mkdir -pv $(DESTDIR)$(LOCALEDIR)
	for file in $(MO_FILES); do \
		lang=$$(basename $${file/.mo/}); \
		mkdir -pv $(DESTDIR)$(LOCALEDIR)/$${lang}/LC_MESSAGES; \
		install -v -m 644 $${file} \
			$(DESTDIR)$(LOCALEDIR)/$${lang}/LC_MESSAGES/$(PACKAGE_NAME).mo; \
	done

	# Install systemd unit files.
	mkdir -pv $(DESTDIR)$(UNITDIR)
	install -m 644 -v collecty.service $(DESTDIR)$(UNITDIR)

# Cleanup temporary files.
.PHONY: clean
clean:
	rm -f $(MO_FILES)

# Translation stuff.
$(POT_FILE): $(TRANSLATION_FILES) Makefile
	xgettext --language python -d $(PACKAGE_NAME) -k_ -kN_ \
		-o $@ --add-comments --from-code=UTF-8 $(sort $^)

# Compile gettext dictionaries from translation files.
%.mo: %.po
	msgfmt -o $@ $<
