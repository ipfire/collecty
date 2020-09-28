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

from .__version__ import *

DATABASE_DIR = "/var/lib/collecty"

DEFAULT_IMAGE_FORMAT = "SVG"
SUPPORTED_IMAGE_FORMATS = ("SVG", "PNG", "PDF")

# Default column widths
LABEL         = "%-30s"
EMPTY_LABEL   = "%32s" % ""

COLUMN        = "%16s"
PERCENTAGE    = "%13.2lf%%"
INTEGER       = "%16.0lf"
LARGE_INTEGER = "%14.0lf %s"
FLOAT         = "%14.2lf"
LARGE_FLOAT   = "%12.2lf %s"
BPS           = "%9.2lf %sbps"
PPS           = "%9.2lf %spps"
MS            = "%11.2lf ms"

EMPTY_LINE    = "COMMENT: \\n"
HEADLINE      = "COMMENT:---- %s ----\\c"

