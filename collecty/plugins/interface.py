#!/usr/bin/python
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

from __future__ import division

import os

import base

from ..i18n import _

SYS_CLASS_NET = "/sys/class/net"

class DataSourceInterface(base.DataSource):
	name = "interface"
	description = "Interface Statistics Data Source"

	templates = []

	rrd_schema = [
		"DS:bytes_rx:DERIVE:0:U",
		"DS:bytes_tx:DERIVE:0:U",
		"DS:collisions:DERIVE:0:U",
		"DS:dropped_rx:DERIVE:0:U",
		"DS:dropped_tx:DERIVE:0:U",
		"DS:errors_rx:DERIVE:0:U",
		"DS:errors_tx:DERIVE:0:U",
		"DS:multicast:DERIVE:0:U",
		"DS:packets_rx:DERIVE:0:U",
		"DS:packets_tx:DERIVE:0:U",
	]

	@classmethod
	def autocreate(cls, collecty, **kwargs):
		if not os.path.exists(SYS_CLASS_NET):
			return

		instances = []
		for interface in os.listdir(SYS_CLASS_NET):
			path = os.path.join(SYS_CLASS_NET, interface)
			if not os.path.isdir(path):
				continue

			instance = cls(collecty, interface=interface)
			instances.append(instance)

		return instances

	def init(self, **kwargs):
		self.interface = kwargs.get("interface")

	@property
	def id(self):
		return "-".join((self.name, self.interface))

	def read(self):
		files = (
			"rx_bytes", "tx_bytes",
			"collisions",
			"rx_dropped", "tx_dropped",
			"rx_errors", "tx_errors",
			"multicast",
			"rx_packets", "tx_packets",
		)
		ret = ["%s" % self.now,]

		for file in files:
			path = os.path.join(SYS_CLASS_NET, self.interface, "statistics", file)

			# Open file and read it's content.
			f = open(path)

			line = f.readline()
			line = line.strip()
			ret.append(line)

			f.close()

		self.data.append(":".join(ret))
