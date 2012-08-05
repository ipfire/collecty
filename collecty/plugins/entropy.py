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

import os

import base

ENTROPY_FILE = "/proc/sys/kernel/random/entropy_avail"

class PluginEntropy(base.Plugin):
	name = "entropy"
	description = "Entropy Plugin"

	rrd_schema = [
		"DS:entropy:GAUGE:120:0:U",
		"RRA:AVERAGE:0.5:1:2160",
		"RRA:AVERAGE:0.5:5:2016",
		"RRA:AVERAGE:0.5:15:2880",
		"RRA:AVERAGE:0.5:60:8760",
	]

	@classmethod
	def autocreate(cls, collecty, **kwargs):
		if not os.path.exists(ENTROPY_FILE):
			self.log.debug(_("Entropy kernel interface does not exist."))
			return

		return cls(collecty, **kwargs)

	def read(self):
		data = "%s" % self.now

		f = open(ENTROPY_FILE)
		entropy = f.readline()
		f.close()

		data += ":%s" % entropy.strip()
		self.data.append(data)
