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

from ..colours import *
from ..constants import *

class GraphTemplateMemory(base.GraphTemplate):
	name = "memory"

	upper_limit = 100
	lower_limit = 0

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			# Headline
			"COMMENT:%s" % EMPTY_LABEL,
			"COMMENT:%s" % (COLUMN % _("Current")),
			"COMMENT:%s" % (COLUMN % _("Average")),
			"COMMENT:%s" % (COLUMN % _("Minimum")),
			"COMMENT:%s\\j" % (COLUMN % _("Maximum")),

			"AREA:used%s:%s" % (
				transparency(MEMORY_USED, AREA_OPACITY),
				LABEL % _("Used Memory"),
			),
			"GPRINT:used_cur:%s" % PERCENTAGE,
			"GPRINT:used_avg:%s" % PERCENTAGE,
			"GPRINT:used_min:%s" % PERCENTAGE,
			"GPRINT:used_max:%s\\j" % PERCENTAGE,

			"STACK:buffered%s:%s" % (
				transparency(MEMORY_BUFFERED, AREA_OPACITY),
				LABEL % _("Buffered Data"),
			),
			"GPRINT:buffered_cur:%s" % PERCENTAGE,
			"GPRINT:buffered_avg:%s" % PERCENTAGE,
			"GPRINT:buffered_min:%s" % PERCENTAGE,
			"GPRINT:buffered_max:%s\\j" % PERCENTAGE,

			"STACK:cached%s:%s" % (
				lighten(MEMORY_CACHED, AREA_OPACITY),
				LABEL % _("Cached data")),
			"GPRINT:cached_cur:%s" % PERCENTAGE,
			"GPRINT:cached_avg:%s" % PERCENTAGE,
			"GPRINT:cached_min:%s" % PERCENTAGE,
			"GPRINT:cached_max:%s\\j" % PERCENTAGE,

#			"STACK:free#7799ff:%-15s" % _("Free memory"),
#			"GPRINT:free_max:%12s\:" % _("Maximum") + " %6.2lf" ,
#			"GPRINT:free_min:%12s\:" % _("Minimum") + " %6.2lf",
#			"GPRINT:free_avg:%12s\:" % _("Average") + " %6.2lf",

			"LINE3:swap%s:%-15s" % (MEMORY_SWAP, LABEL % _("Used Swap Space")),
			"GPRINT:swap_cur:%s" % PERCENTAGE,
			"GPRINT:swap_avg:%s" % PERCENTAGE,
			"GPRINT:swap_min:%s" % PERCENTAGE,
			"GPRINT:swap_max:%s\\j" % PERCENTAGE,

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
		with open("/proc/meminfo") as f:
			for line in f:
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


class MemoryPlugin(base.Plugin):
	name = "memory"
	description = "Memory Usage Plugin"

	templates = [GraphTemplateMemory]

	@property
	def objects(self):
		yield MemoryObject(self)
