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

from ..i18n import _

ENTROPY_FILE = "/proc/sys/kernel/random/entropy_avail"

class GraphTemplateEntropy(base.GraphTemplate):
	name = "entropy"

	rrd_graph = [
		"DEF:entropy=%(file)s:entropy:AVERAGE",
		"CDEF:entropytrend=entropy,43200,TREND",

		"LINE3:entropy#ff0000:%-15s" % _("Available entropy"),
		"VDEF:entrmin=entropy,MINIMUM",
		"VDEF:entrmax=entropy,MAXIMUM",
		"VDEF:entravg=entropy,AVERAGE",
		"GPRINT:entrmax:%12s\:" % _("Maximum") + " %5.0lf",
		"GPRINT:entrmin:%12s\:" % _("Minimum") + " %5.0lf",
		"GPRINT:entravg:%12s\:" % _("Average") + " %5.0lf\\n",

		"LINE3:entropytrend#000000",
	]

	rrd_graph_args = [
		"--title", _("Available entropy"),
		"--vertical-label", _("Bits"),

		"--lower-limit", "0", "--rigid",
	]


class DataSourceEntropy(base.DataSource):
	name = "entropy"
	description = "Entropy Data Source"

	templates = [GraphTemplateEntropy,]

	rrd_schema = [
		"DS:entropy:GAUGE:0:U",
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
