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

import os

import logging
log = logging.getLogger("collecty.util")
log.propagate = 1

from .constants import *

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

def get_network_interfaces():
	"""
		Returns all real network interfaces
	"""
	for interface in os.listdir("/sys/class/net"):
		# Skip some unwanted interfaces.
		if interface == "lo" or interface.startswith("mon."):
			continue

		path = os.path.join("/sys/class/net", interface)
		if not os.path.isdir(path):
			continue

		yield interface

def make_interval(interval):
	try:
		return INTERVALS[interval]
	except KeyError:
		return "end-%s" % interval

class ProcNetSnmpParser(object):
	"""
		This class parses /proc/net/snmp{,6} and allows
		easy access to the values.
	"""
	def __init__(self, intf=None):
		self.intf = intf
		self._data = {}

		if not self.intf:
			self._data.update(self._parse())

		self._data.update(self._parse6())

	def _parse(self):
		res = {}

		with open("/proc/net/snmp") as f:
			keys = {}

			for line in f.readlines():
				line = line.strip()

				# Stop after an empty line
				if not line:
					break

				type, values = line.split(": ", 1)

				# Check if the keys are already known
				if type in keys:
					values = (int(v) for v in values.split())
					res[type] = dict(zip(keys[type], values))

				# Otherwise remember the keys
				else:
					keys[type] = values.split()

		return res

	def _parse6(self):
		res = {}

		fn = "/proc/net/snmp6"
		if self.intf:
			fn = os.path.join("/proc/net/dev_snmp6", self.intf)

		with open(fn) as f:
			for line in f.readlines():
				key, val = line.split()

				try:
					type, key = key.split("6", 1)
				except ValueError:
					continue

				type += "6"
				val = int(val)

				try:
					res[type][key] = val
				except KeyError:
					res[type] = { key : val }

		return res

	def get(self, proto, key):
		"""
			Retrieves a value from the internally
			parse dictionary read from /proc/net/snmp.
		"""
		try:
			return self._data[proto][key]
		except KeyError:
			pass
