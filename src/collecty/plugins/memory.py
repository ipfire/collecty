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

from . import base

from ..i18n import _
from ..colours import *

class GraphTemplateMemory(base.GraphTemplate):
	name = "memory"

	upper_limit = 100
	lower_limit = 0

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			"AREA:used%s:%-15s" % (lighten(MEMORY_USED, AREA_OPACITY), _("Used memory")),
			"GPRINT:used_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:used_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:used_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"STACK:buffered%s:%-15s" % (lighten(MEMORY_BUFFERED, AREA_OPACITY), _("Buffered data")),
			"GPRINT:buffered_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:buffered_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:buffered_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"STACK:cached%s:%-15s" % (lighten(MEMORY_CACHED, AREA_OPACITY), _("Cached data")),
			"GPRINT:cached_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:cached_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:cached_avg:%12s\:" % _("Average") + " %6.2lf\\n",

#			"STACK:free#7799ff:%-15s" % _("Free memory"),
#			"GPRINT:free_max:%12s\:" % _("Maximum") + " %6.2lf" ,
#			"GPRINT:free_min:%12s\:" % _("Minimum") + " %6.2lf",
#			"GPRINT:free_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"LINE3:swap%s:%-15s" % (MEMORY_SWAP, _("Used Swap space")),
			"GPRINT:swap_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:swap_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:swap_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			# Draw the outlines of the areas
			"LINE1:used%s" % MEMORY_USED,
			"LINE1:buffered%s::STACK" % MEMORY_BUFFERED,
			"LINE1:cached%s::STACK" % MEMORY_CACHED,
		]

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Memory Usage")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Percent")


class MemoryObject(base.Object):
	rrd_schema = [
		"DS:used:GAUGE:0:100",
		"DS:cached:GAUGE:0:100",
		"DS:buffered:GAUGE:0:100",
		"DS:free:GAUGE:0:100",
		"DS:swap:GAUGE:0:100",
	]

	@property
	def id(self):
		return "default"

	def collect(self):
		f = None

		try:
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

			ret = [
				"%s" % ((total - (free + buffered + cached)) * 100 / total),
				"%s" % (cached * 100 / total),
				"%s" % (buffered * 100 / total),
				"%s" % (free * 100 / total),
			]

			if swapt:
				ret.append("%s" % ((swapt - swapf) * 100 / swapt))
			else:
				ret.append("0")

			return ret
		finally:
			if f:
				f.close()


class MemoryPlugin(base.Plugin):
	name = "memory"
	description = "Memory Usage Plugin"

	templates = [GraphTemplateMemory]

	@property
	def objects(self):
		yield MemoryObject(self)
