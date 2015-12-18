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
from ..i18n import _

class GraphTemplateProcessor(base.GraphTemplate):
	name = "processor"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			"AREA:user%s:%-15s" % (CPU_USER, _("User")),
			"GPRINT:user_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:user_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:user_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"STACK:nice%s:%-15s" % (CPU_NICE, _("Nice")),
			"GPRINT:nice_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:nice_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:nice_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"STACK:sys%s:%-15s" % (CPU_SYS, _("System")),
			"GPRINT:sys_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:sys_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:sys_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"STACK:wait%s:%-15s" % (CPU_WAIT, _("Wait")),
			"GPRINT:wait_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:wait_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:wait_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"STACK:irq%s:%-15s" % (CPU_IRQ, _("Interrupt")),
			"GPRINT:irq_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:irq_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:irq_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"STACK:sirq%s:%-15s" % (CPU_SIRQ, _("Soft Interrupt")),
			"GPRINT:sirq_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:sirq_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:sirq_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"STACK:idle%s:%-15s" % (CPU_IDLE, _("Idle")),
			"GPRINT:idle_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:idle_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:idle_avg:%12s\:" % _("Average") + " %6.2lf\\n",
		]

	lower_limit = 0

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Processor Usage")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Jiffies")


class ProcessorObject(base.Object):
	rrd_schema = [
		"DS:user:DERIVE:0:U",
		"DS:nice:DERIVE:0:U",
		"DS:sys:DERIVE:0:U",
		"DS:idle:DERIVE:0:U",
		"DS:wait:DERIVE:0:U",
		"DS:irq:DERIVE:0:U",
		"DS:sirq:DERIVE:0:U",
	]

	@property
	def id(self):
		return "default"

	def collect(self):
		"""
			Reads the CPU usage.
		"""
		f = None

		try:
			f = open("/proc/stat")

			for line in f.readlines():
				if not line.startswith("cpu"):
					continue

				columns = line.split()
				if len(columns) < 8:
					continue

				return (
					columns[1], # user
					columns[2], # nice
					columns[3], # sys
					columns[4], # idle
					columns[5], # wait
					columns[6], # irq
					columns[7], # sirq
				)
		finally:
			if f:
				f.close()


class ProcessorPlugin(base.Plugin):
	name = "processor"
	description = "Processor Usage Plugin"

	templates = [GraphTemplateProcessor]

	@property
	def objects(self):
		yield ProcessorObject(self)
