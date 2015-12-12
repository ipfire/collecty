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

AC_PREREQ([2.64])

AC_INIT([collecty],
	[004],
	[info@ipfire.org],
	[collecty],
	[http://git.ipfire.org/?p=oddments/collecty.git;a=summary])

AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_AUX_DIR([build-aux])

AC_PREFIX_DEFAULT([/usr])

AM_INIT_AUTOMAKE([
	foreign
	1.11
	-Wall
	-Wno-portability
	silent-rules
	tar-pax
	subdir-objects
])
AM_SILENT_RULES([yes])
LT_PREREQ(2.2)
LT_INIT([disable-static])

IT_PROG_INTLTOOL([0.40.0])

GETTEXT_PACKAGE=collecty
AC_SUBST(GETTEXT_PACKAGE)

AC_PROG_LN_S
AC_PROG_MKDIR_P
AC_PROG_SED

# C Compiler
AC_PROG_CC
AC_PROG_CC_C99
AC_PROG_CC_C_O
AC_PROG_GCC_TRADITIONAL

AC_CHECK_HEADERS_ONCE([
	errno.h
	fcntl.h
	linux/hdreg.h
	mntent.h
	stdbool.h
	string.h
	sys/ioctl.h
	time.h
])

AC_PATH_PROG([XSLTPROC], [xsltproc])

PKG_CHECK_MODULES([OPING], [liboping])

# Python
AM_PATH_PYTHON([3.2])
PKG_CHECK_MODULES([PYTHON], [python-${PYTHON_VERSION}])

# libatasmart
PKG_CHECK_MODULES([LIBATASMART], [libatasmart >= 0.19])

save_LIBS="$LIBS"

# lm-sensors
AC_CHECK_HEADERS([sensors/sensors.h sensors/errors.h])

LIBS=
AC_CHECK_LIB(sensors, sensors_init, [], [AC_MSG_ERROR([*** sensors library not found])])
SENSORS_LIBS="$LIBS"
AC_SUBST(SENSORS_LIBS)

LIBS="$save_LIBS"

# pkg-config
PKG_PROG_PKG_CONFIG
# This makes sure pkg.m4 is available.
m4_pattern_forbid([^_?PKG_[A-Z_]+$],[*** pkg.m4 missing, please install pkg-config])

# ------------------------------------------------------------------------------
have_manpages=no
AC_ARG_ENABLE(manpages, AS_HELP_STRING([--disable-man-pages],
	[do not install man pages]))
AS_IF([test "x$enable_manpages" != xno], [have_manpages=yes])
AM_CONDITIONAL(ENABLE_MANPAGES, [test "x$have_manpages" = "xyes"])

# ------------------------------------------------------------------------------

AC_ARG_WITH([systemd],
	AS_HELP_STRING([--with-systemd], [Enable systemd support.])
)

AC_ARG_WITH([dbuspolicydir],
	AS_HELP_STRING([--with-dbuspolicydir=DIR], [D-Bus policy directory]),
	[],
	[with_dbuspolicydir=${sysconfdir}/dbus-1/system.d]
)

AC_ARG_WITH([dbussystemservicedir],
	AS_HELP_STRING([--with-dbussystemservicedir=DIR], [D-Bus system service directory]),
	[],
	[with_dbussystemservicedir=${datadir}/dbus-1/system-services]
)

AS_IF([test "x$with_systemd" != "xno"],
      [PKG_CHECK_MODULES(systemd, [libsystemd],
      [have_systemd=yes], [have_systemd=no])],
      [have_systemd=no]
)

AS_IF([test "x$have_systemd" = "xyes"],
      [AC_MSG_CHECKING([for systemd system unit directory])
	AC_ARG_WITH([systemdsystemunitdir],
		AS_HELP_STRING([--with-systemdsystemunitdir=DIR], [Directory for systemd service files]),
		[], [with_systemdsystemunitdir=$($PKG_CONFIG --variable=systemdsystemunitdir systemd)]
	)

	AC_SUBST([systemdsystemunitdir], [$with_systemdsystemunitdir])

	if test -n "$systemdsystemunitdir" -a "x$systemdsystemunitdir" != xno; then
		AC_MSG_RESULT([$systemdsystemunitdir])
	else
		AC_MSG_ERROR([not found (try --with-systemdsystemunitdir)])
	fi
      ],
      [AS_IF([test "x$with_systemd" = "xyes"],
             [AC_MSG_ERROR([Systemd support is enabled but no systemd has been found.])
      ])
])

AM_CONDITIONAL(HAVE_SYSTEMD, [test "x$have_systemd" = "xyes"])

AC_SUBST([dbuspolicydir], [$with_dbuspolicydir])
AC_SUBST([dbussystemservicedir], [$with_dbussystemservicedir])

# ------------------------------------------------------------------------------

AC_CONFIG_FILES([
	Makefile
	po/Makefile.in
	src/collecty/__version__.py
])

AC_OUTPUT
AC_MSG_RESULT([
	${PACKAGE_NAME} ${VERSION}

	prefix:			${prefix}
	D-Bus policy dir:	${with_dbuspolicydir}
	D-Bus system dir:	${with_dbussystemservicedir}

	Systemd support		${have_systemd}
	Generate man-pages:	${have_manpages}
])
