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

import logging
import os

log = logging.getLogger("collecty.util")

from .constants import *

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

def guess_format(filename):
	"""
		Returns the best format by filename extension
	"""
	parts = filename.split(".")

	if parts:
		# The extension is the last part
		extension = parts[-1]

		# Image formats are all uppercase
		extension = extension.upper()

		if extension in SUPPORTED_IMAGE_FORMATS:
			return extension

	# Otherwise fall back to the default format
	return DEFAULT_IMAGE_FORMAT

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
