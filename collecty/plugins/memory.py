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

import base

from ..i18n import _

class GraphTemplateMemory(base.GraphTemplate):
	name = "memory"

	rrd_graph = [
		"DEF:used=%(file)s:used:AVERAGE",
		"DEF:cached=%(file)s:cached:AVERAGE",
		"DEF:buffered=%(file)s:buffered:AVERAGE",
		"DEF:free=%(file)s:free:AVERAGE",
		"DEF:swap=%(file)s:swap:AVERAGE",

		"AREA:used#90EE90:%-15s" % _("Used memory"),
		"VDEF:usedmin=used,MINIMUM",
		"VDEF:usedmax=used,MAXIMUM",
		"VDEF:usedavg=used,AVERAGE",
		"GPRINT:usedmax:%12s\:" % _("Maximum") + " %6.2lf" ,
		"GPRINT:usedmin:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:usedavg:%12s\:" % _("Average") + " %6.2lf\\n",

		"STACK:buffered#4169E1:%-15s" % _("Buffered data"),
		"VDEF:bufferedmin=buffered,MINIMUM",
		"VDEF:bufferedmax=buffered,MAXIMUM",
		"VDEF:bufferedavg=buffered,AVERAGE",
		"GPRINT:bufferedmax:%12s\:" % _("Maximum") + " %6.2lf" ,
		"GPRINT:bufferedmin:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:bufferedavg:%12s\:" % _("Average") + " %6.2lf\\n",

		"STACK:cached#FFD700:%-15s" % _("Cached data"),
		"VDEF:cachedmin=cached,MINIMUM",
		"VDEF:cachedmax=cached,MAXIMUM",
		"VDEF:cachedavg=cached,AVERAGE",
		"GPRINT:cachedmax:%12s\:" % _("Maximum") + " %6.2lf" ,
		"GPRINT:cachedmin:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:cachedavg:%12s\:" % _("Average") + " %6.2lf\\n",

#		"STACK:free#7799ff:%-15s" % _("Free memory"),
#		"VDEF:freemin=free,MINIMUM",
#		"VDEF:freemax=free,MAXIMUM",
#		"VDEF:freeavg=free,AVERAGE",
#		"GPRINT:freemax:%12s\:" % _("Maximum") + " %6.2lf" ,
#		"GPRINT:freemin:%12s\:" % _("Minimum") + " %6.2lf",
#		"GPRINT:freeavg:%12s\:" % _("Average") + " %6.2lf\\n",

		"LINE3:swap#ff0000:%-15s" % _("Used Swap space"),
		"VDEF:swapmin=swap,MINIMUM",
		"VDEF:swapmax=swap,MAXIMUM",
		"VDEF:swapavg=swap,AVERAGE",
		"GPRINT:swapmax:%12s\:" % _("Maximum") + " %6.2lf" ,
		"GPRINT:swapmin:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:swapavg:%12s\:" % _("Average") + " %6.2lf\\n",
	]

	rrd_graph_args = [
		"--title", _("Memory Usage"),
		"--vertical-label", _("Percent"),

		# Limit y axis.
		"--upper-limit", "100",
		"--lower-limit", "0",
		"--rigid",
	]


class DataSourceMemory(base.DataSource):
	name = "memory"
	description = "Memory Usage Data Source"

	templates = [GraphTemplateMemory,]

	rrd_schema = [
		"DS:used:GAUGE:0:100",
		"DS:cached:GAUGE:0:100",
		"DS:buffered:GAUGE:0:100",
		"DS:free:GAUGE:0:100",
		"DS:swap:GAUGE:0:100",
	]

	@classmethod
	def autocreate(cls, collecty, **kwargs):
		# Every system has got memory.
		return cls(collecty, **kwargs)

	def read(self):
		f = None

		try:
			ret = "%s" % self.now

			f = open("/proc/meminfo")
			for line in f.readlines():
				if line.startswith("MemTotal:"):
					total = float(line.split()[1])
				if line.startswith("MemFree:"):
					free = float(line.split()[1])
				elif line.startswith("Buffers:"):
					buffered = float(line.split()[1])
				elif line.startswith("Cached:"):
					cached = float(line.split()[1])
				elif line.startswith("SwapTotal:"):
					swapt = float(line.split()[1])
				elif line.startswith("SwapFree:"):
					swapf = float(line.split()[1])

			ret += ":%s" % ((total - (free + buffered + cached)) * 100 / total)
			ret += ":%s" % (cached * 100 / total)
			ret += ":%s" % (buffered * 100 / total)
			ret += ":%s" % (free * 100 / total)

			if swapt:
				ret += ":%s" % ((swapt - swapf) * 100 / swapt)
			else:
				ret += ":0"

			self.data.append(ret)
		finally:
			if f:
				f.close()
