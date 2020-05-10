###############################################################################
#                                                                             #
# collecty - The IPFire statictics collection daemon                          #
# Copyright (C) 2015 collecty development team                                #
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

ACLOCAL_AMFLAGS = -I m4 ${ACLOCAL_FLAGS}
AM_MAKEFLAGS = --no-print-directory
AUTOMAKE_OPTIONS = color-tests

# remove target it the command fails
.DELETE_ON_ERROR:

# keep itermediate files
.SECONDARY:

SUBDIRS = . po

pythondir  = $(pyexecdir)

# Dirs of external packages
dbuspolicydir=@dbuspolicydir@
dbussystemservicedir=@dbussystemservicedir@

CLEANFILES =
DISTCLEANFILES =
EXTRA_DIST =
INSTALL_DIRS =
noinst_DATA =

@INTLTOOL_POLICY_RULE@

.PHONY: update-po
update-po:
	$(MAKE) -C po update-po

DISTCHECK_CONFIGURE_FLAGS = \
	--with-dbuspolicydir=$$dc_install_base/$(dbuspolicydir) \
	--with-dbussystemservicedir=$$dc_install_base/$(dbussystemservicedir) \
	--with-systemdsystemunitdir=$$dc_install_base/$(systemdsystemunitdir)

# ------------------------------------------------------------------------------

AM_V_XSLT   = $(AM_V_XSLT_$(V))
AM_V_XSLT_  = $(AM_V_XSLT_$(AM_DEFAULT_VERBOSITY))
AM_V_XSLT_0 = @echo "  XSLT    " $@;

# ------------------------------------------------------------------------------

dist_doc_DATA = \
	COPYING

# ------------------------------------------------------------------------------

dist_bin_SCRIPTS = \
	src/collectyd \
	src/collecty-client

collecty_PYTHON = \
	src/collecty/__init__.py \
	src/collecty/__version__.py \
	src/collecty/bus.py \
	src/collecty/client.py \
	src/collecty/colours.py \
	src/collecty/constants.py \
	src/collecty/daemon.py \
	src/collecty/errors.py \
	src/collecty/i18n.py \
	src/collecty/locales.py \
	src/collecty/logger.py \
	src/collecty/util.py

collectydir = $(pythondir)/collecty

collectyplugins_PYTHON = \
	src/collecty/plugins/base.py \
	src/collecty/plugins/contextswitches.py \
	src/collecty/plugins/conntrack.py \
	src/collecty/plugins/cpufreq.py \
	src/collecty/plugins/df.py \
	src/collecty/plugins/disk.py \
	src/collecty/plugins/__init__.py \
	src/collecty/plugins/interface.py \
	src/collecty/plugins/interrupts.py \
	src/collecty/plugins/ipfrag.py \
	src/collecty/plugins/latency.py \
	src/collecty/plugins/loadavg.py \
	src/collecty/plugins/memory.py \
	src/collecty/plugins/processor.py \
	src/collecty/plugins/sensors.py

collectypluginsdir = $(collectydir)/plugins

pkgpyexec_LTLIBRARIES = \
	_collecty.la

_collecty_la_SOURCES = \
	src/_collecty/_collectymodule.c \
	src/_collecty/_collectymodule.h \
	src/_collecty/blockdev.c \
	src/_collecty/ping.c \
	src/_collecty/sensors.c \
	src/_collecty/utils.c

_collecty_la_CFLAGS = \
	$(AM_CFLAGS) \
	$(LIBATASMART_CFLAGS) \
	$(OPING_CFLAGS) \
	$(PYTHON_CFLAGS)

_collecty_la_LDFLAGS = \
	$(AM_LDFLAGS) \
	-shared \
	-module \
	-avoid-version

_collecty_la_LIBADD = \
	$(LIBATASMART_LIBS) \
	$(OPING_LIBS) \
	$(PYTHON_LIBS) \
	$(SENSORS_LIBS)

dist_dbuspolicy_DATA = \
	src/dbus/org.ipfire.collecty1.conf

dist_dbussystemservice_DATA = \
	src/dbus/org.ipfire.collecty1.service

systemdsystemunit_DATA = \
	src/systemd/collecty.service

dist_systemdsystemunit_DATA = \
	src/systemd/org.ipfire.collecty1.busname

EXTRA_DIST += \
	src/systemd/collecty.service.in

CLEANFILES += \
	src/systemd/collecty.service

# ------------------------------------------------------------------------------

.PHONY: man
man: $(MANPAGES) $(MANPAGES_HTML)

if ENABLE_MANPAGES
MANPAGES = \
	man/collectyd.1

MANPAGES_XML  = $(patsubst %.1,%.xml,$(patsubst %.5,%.xml,$(MANPAGES)))
MANPAGES_HTML = $(patsubst %.xml,%.html,$(MANPAGES_XML))

man_MANS = \
	$(MANPAGES)

noinst_DATA += \
	$(MANPAGES_HTML)

CLEANFILES += \
	$(man_MANS) \
	$(MANPAGES_HTML)

EXTRA_DIST += \
	$(MANPAGES_XML) \
	man/custom-html.xsl

XSLTPROC_FLAGS = \
	--nonet \
	--stringparam man.output.quietly 1 \
	--stringparam funcsynopsis.style ansi \
	--stringparam man.th.extra1.suppress 1 \
	--stringparam man.authors.section.enabled 1 \
	--stringparam man.copyright.section.enabled 1

XSLTPROC_COMMAND_MAN = \
	$(AM_V_XSLT)$(XSLTPROC) -o $@ $(XSLTPROC_FLAGS) \
		http://docbook.sourceforge.net/release/xsl/current/manpages/docbook.xsl $<

XSLTPROC_COMMAND_HTML = \
	$(AM_V_XSLT)$(XSLTPROC) -o $@ $(XSLTPROC_FLAGS) $(srcdir)/man/custom-html.xsl $<

man/%.1: man/%.xml
	$(XSLTPROC_COMMAND_MAN)

man/%.5: man/%.xml
	$(XSLTPROC_COMMAND_MAN)

man/%.html: man/%.xml man/custom-html.xsl
	$(XSLTPROC_COMMAND_HTML)

endif

# ------------------------------------------------------------------------------

substitutions = \
	'|PACKAGE_NAME=$(PACKAGE_NAME)|' \
	'|PACKAGE_VERSION=$(PACKAGE_VERSION)|' \
	'|configsdir=$(configsdir)|' \
	'|bindir=$(bindir)|'

SED_PROCESS = \
	$(AM_V_GEN)$(MKDIR_P) $(dir $@) && \
	$(SED) $(subst '|,-e 's|@,$(subst =,\@|,$(subst |',|g',$(substitutions)))) \
		< $< > $@

src/systemd/%: src/systemd/%.in Makefile
	$(SED_PROCESS)
