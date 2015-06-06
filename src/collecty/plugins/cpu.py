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

class GraphTemplateProcessor(base.GraphTemplate):
	name = "processor"

	rrd_graph = [
		"DEF:user=%(file)s:user:AVERAGE",
		"DEF:nice=%(file)s:nice:AVERAGE",
		"DEF:sys=%(file)s:sys:AVERAGE",
		"DEF:idle=%(file)s:idle:AVERAGE",
		"DEF:wait=%(file)s:wait:AVERAGE",
		"DEF:irq=%(file)s:irq:AVERAGE",
		"DEF:sirq=%(file)s:sirq:AVERAGE",

		"AREA:user#90EE90:%-15s" % _("User"),
		"VDEF:usermin=user,MINIMUM",
		"VDEF:usermax=user,MAXIMUM",
		"VDEF:useravg=user,AVERAGE",
		"GPRINT:usermax:%12s\:" % _("Maximum") + " %6.2lf" ,
		"GPRINT:usermin:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:useravg:%12s\:" % _("Average") + " %6.2lf\\n",

		"STACK:nice#4169E1:%-15s" % _("Nice"),
		"VDEF:nicemin=nice,MINIMUM",
		"VDEF:nicemax=nice,MAXIMUM",
		"VDEF:niceavg=nice,AVERAGE",
		"GPRINT:nicemax:%12s\:" % _("Maximum") + " %6.2lf" ,
		"GPRINT:nicemin:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:niceavg:%12s\:" % _("Average") + " %6.2lf\\n",

		"STACK:sys#DC143C:%-15s" % _("System"),
		"VDEF:sysmin=sys,MINIMUM",
		"VDEF:sysmax=sys,MAXIMUM",
		"VDEF:sysavg=sys,AVERAGE",
		"GPRINT:sysmax:%12s\:" % _("Maximum") + " %6.2lf" ,
		"GPRINT:sysmin:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:sysavg:%12s\:" % _("Average") + " %6.2lf\\n",

		"STACK:wait#483D8B:%-15s" % _("Wait"),
		"VDEF:waitmin=wait,MINIMUM",
		"VDEF:waitmax=wait,MAXIMUM",
		"VDEF:waitavg=wait,AVERAGE",
		"GPRINT:waitmax:%12s\:" % _("Maximum") + " %6.2lf" ,
		"GPRINT:waitmin:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:waitavg:%12s\:" % _("Average") + " %6.2lf\\n",

		"STACK:irq#DAA520:%-15s" % _("Interrupt"),
		"VDEF:irqmin=irq,MINIMUM",
		"VDEF:irqmax=irq,MAXIMUM",
		"VDEF:irqavg=irq,AVERAGE",
		"GPRINT:irqmax:%12s\:" % _("Maximum") + " %6.2lf" ,
		"GPRINT:irqmin:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:irqavg:%12s\:" % _("Average") + " %6.2lf\\n",

		"STACK:sirq#FFD700:%-15s" % _("Soft interrupt"),
		"VDEF:sirqmin=sirq,MINIMUM",
		"VDEF:sirqmax=sirq,MAXIMUM",
		"VDEF:sirqavg=sirq,AVERAGE",
		"GPRINT:sirqmax:%12s\:" % _("Maximum") + " %6.2lf" ,
		"GPRINT:sirqmin:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:sirqavg:%12s\:" % _("Average") + " %6.2lf\\n",

		"STACK:idle#EFEFEF:%-15s" % _("Idle"),
		"VDEF:idlemin=idle,MINIMUM",
		"VDEF:idlemax=idle,MAXIMUM",
		"VDEF:idleavg=idle,AVERAGE",
		"GPRINT:idlemax:%12s\:" % _("Maximum") + " %6.2lf" ,
		"GPRINT:idlemin:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:idleavg:%12s\:" % _("Average") + " %6.2lf\\n",
	]

	lower_limit = 0

	@property
	def graph_title(self):
		return _("CPU usage")

	@property
	def graph_vertical_label(self):
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
