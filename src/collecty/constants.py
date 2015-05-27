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

DATABASE_DIR = "/var/lib/collecty"

BUS_DOMAIN = "org.ipfire.collecty1"

DEFAULT_IMAGE_FORMAT = "SVG"

GRAPH_DEFAULT_ARGUMENTS = (
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

GRAPH_DEFAULT_WIDTH = 768
GRAPH_DEFAULT_HEIGHT = 480
