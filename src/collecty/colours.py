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

def _add(colour, amount):
	"""
		Adds some value to colours
	"""
	# Parse hex array
	bytes = bytearray.fromhex(colour.lstrip("#"))

	if not len(bytes) == 3:
		raise ValueError("Invalid colour: %s" % colour)

	ret = bytearray()

	for byte in bytes:
		byte = round(byte * amount)

		# Ensure the result is within range
		byte = min(byte, 255)
		byte = max(byte, 0)

		# Update the array
		ret.append(byte)

	return "#%s" % ret.hex()

def lighten(colour, scale=0.25):
	"""
		Takes a hexadecimal colour code
		and brightens the colour.
	"""
	return _add(colour, scale)

def darken(colour, scale=0.25):
	"""
		Takes a hexadecimal colour code
		and darkens the colour.
	"""
	return _add(colour, -scale)

def transparency(colour, scale=0.1):
	"""
		Adds transparency to the given colour code
	"""
	return "%s%02X" % (colour, round(0xff * scale))

BLACK        = "#000000"
WHITE        = "#FFFFFF"
GREY         = "#9E9E9E"
LIGHT_GREY   = "#F5F5F5"

RED          = "#F44336"
LIGHT_RED    = "#CC0033"
YELLOW       = "#FFEB3B"
LIGHT_YELLOW = "#FFFF66"
GREEN        = "#4CAF50"
LIGHT_GREEN  = "#8BC34A"
BLUE         = "#2196F3"
LIGHT_BLUE   = "#03A9F4"

AMBER        = "#FFC107"
BROWN        = "#795548"
CYAN         = "#00BCD4"
INDIGO       = "#3F51B5"
LIME         = "#CDDC39"
ORANGE       = "#FF9800"
DEEP_ORANGE  = "#FF5722"
PINK         = "#E91E63"
PURPLE       = "#9C27B0"
DEEP_PURPLE  = "#673AB7"
TEAL         = "#009688"

COLOUR_OK       = LIGHT_GREEN
COLOUR_CRITICAL = LIGHT_RED
COLOUR_ERROR    = COLOUR_CRITICAL
COLOUR_WARN     = LIGHT_YELLOW
COLOUR_TEXT     = lighten(BLACK, 0.87) # 87% grey

PRIMARY      = INDIGO
ACCENT       = PINK

# Lighten the areas by this factor
AREA_OPACITY   = 0.25
STDDEV_OPACITY = 0.33

# Receive and transmit
COLOUR_RX    = RED
COLOUR_TX    = GREEN

# I/O
COLOUR_READ  = GREEN
COLOUR_WRITE = RED

# IPv6 + IPv4
COLOUR_IPV6  = INDIGO
COLOUR_IPV4  = PINK
COLOUR_IPVX  = GREY # other

COLOUR_TCP     = INDIGO
COLOUR_UDP     = YELLOW
COLOUR_ICMP    = PURPLE
COLOUR_IGMP    = TEAL
COLOUR_UDPLITE = DEEP_ORANGE
COLOUR_SCTP    = LIGHT_GREEN
COLOUR_DCCP    = LIGHT_BLUE
COLOUR_OTHER   = COLOUR_IPVX

# Processor
CPU_USER       = LIGHT_GREEN
CPU_NICE       = BLUE
CPU_SYS        = RED
CPU_WAIT       = DEEP_PURPLE
CPU_IRQ        = ORANGE
CPU_SIRQ       = YELLOW
CPU_STEAL      = LIGHT_BLUE
CPU_GUEST      = PINK
CPU_GUEST_NICE = lighten(PINK, 0.8)
CPU_IDLE       = LIGHT_GREY

# Memory
MEMORY_USED     = GREEN
MEMORY_BUFFERED = BLUE
MEMORY_CACHED   = YELLOW
MEMORY_SWAP     = RED

COLOURS_PROTOCOL_STATES = {
	# General states
	"NONE"              : GREY,
	"TIME_WAIT"         : AMBER,

	# TCP
	"CLOSE"             : BLACK,
	"CLOSE_WAIT"        : lighten(BLACK, 0.25),
	"ESTABLISHED"       : LIGHT_GREEN,
	"FIN_WAIT"          : ORANGE,
	"LAST_ACK"          : PURPLE,
	"SYN_RECV"          : CYAN,
	"SYN_SENT"          : TEAL,
	"SYN_SENT2"         : AMBER,

	# DCCP
	"CLOSEREQ"          : lighten(BLACK, 0.5),
	"CLOSING"           : lighten(BLACK, 0.25),
	"IGNORE"            : WHITE,
	"INVALID"           : RED,
	"OPEN"              : LIGHT_GREEN,
	"PARTOPEN"          : YELLOW,
	"REQUEST"           : CYAN,
	"RESPOND"           : TEAL,

	# SCTP
	"CLOSED"            : BLACK,
	"COOKIE_ECHOED"     : AMBER,
	"COOKIE_WAIT"       : CYAN,
	"SHUTDOWN_ACK_SENT" : TEAL,
	"SHUTDOWN_RECD"     : PURPLE,
	"SHUTDOWN_SENT"     : LIGHT_BLUE,
}
