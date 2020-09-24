#!/usr/bin/python3
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

from .i18n import _

from .__version__ import *

DATABASE_DIR = "/var/lib/collecty"

BUS_DOMAIN = "org.ipfire.collecty1"

DEFAULT_IMAGE_FORMAT = "SVG"
DEFAULT_LOCALE = "en_GB.utf8"
DEFAULT_TIMEZONE = "UTC"

SUPPORTED_IMAGE_FORMATS = ("SVG", "PNG", "PDF")

GRAPH_DEFAULT_ARGUMENTS = (
	# Change the background colour
	"--color", "BACK#FFFFFF",

	# Disable the border around the image.
	"--border", "0",

	# Let's width and height define the size of
	# the entire image.
	"--full-size-mode",

	# Gives the curves a more organic look.
	"--slope-mode",

	# Show nicer labels.
	"--dynamic-labels",

	# Brand all generated graphs.
	"--watermark", _("Created by collecty"),
)

INTERVALS = {
	None   : "-3h",
	"hour" : "-1h",
	"day"  : "-25h",
	"month": "-30d",
	"week" : "-360h",
	"year" : "-365d",
}

GRAPH_DEFAULT_WIDTH = 768
GRAPH_DEFAULT_HEIGHT = 480

# Default column widths
LABEL         = "%-24s"
EMPTY_LABEL   = "%26s" % ""

COLUMN        = "%16s"
PERCENTAGE    = "%13.2lf%%"
INTEGER       = "%16.0lf"
LARGE_INTEGER = "%14.0lf %s"
FLOAT         = "%14.2lf"
LARGE_FLOAT   = "%12.2lf %s"

EMPTY_LINE = "COMMENT: \\n"

THUMBNAIL_DEFAULT_WIDTH = 80
THUMBNAIL_DEFAULT_HEIGHT = 20
