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

NAME = collecty
VERSION = 0.0.1

DESTDIR =
PYTHON_VER := $(shell python -c "import platform; print '.'.join(platform.python_version_tuple()[:2])")
PYTHON_DIR = $(DESTDIR)/usr/lib/python$(PYTHON_VER)/site-packages/

all:

dist:
	git archive --format=tar --prefix=$(NAME)-$(VERSION)/ HEAD | gzip -9 \
		> $(NAME)-$(VERSION).tar.gz

install:
	-mkdir -pv $(PYTHON_DIR)
	cp -rvf collecty $(PYTHON_DIR)
	install -v -m 755 collectyd $(DESTDIR)/usr/sbin

	-mkdir -pv $(DESTDIR)/var/rrd

	# Install configuration
	-mkdir -pv $(DESTDIR)/etc/$(NAME)/
	cp -vf example.conf $(DESTDIR)/etc/$(NAME)/$(NAME).conf
