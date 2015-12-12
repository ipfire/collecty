#!/usr/bin/python3
###############################################################################
#                                                                             #
# collecty - A system statistics collection daemon for IPFire                 #
# Copyright (C) 2015 IPFire development team                                  #
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

def __add_colour(colour, amount):
	colour = colour.strip("#")

	colour = (
		int(colour[0:2], 16),
		int(colour[2:4], 16),
		int(colour[4:6], 16),
	)

	# Scale the colour
	colour = (e + amount for e in colour)
	colour = (max(e, 0) for e in colour)
	colour = (min(e, 255) for e in colour)

	return "#%02x%02x%02x" % tuple(colour)

def lighten(colour, scale=0.1):
	"""
		Takes a hexadecimal colour code
		and brightens the colour.
	"""
	return __add_colour(colour, 0xff * scale)

def darken(colour, scale=0.1):
	"""
		Takes a hexadecimal colour code
		and darkens the colour.
	"""
	return __add_colour(colour, 0xff * -scale)
