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

import base

from ..i18n import _

class PluginCPU(base.Plugin):
	name = "cpu"
	description = "CPU Usage Plugin"

	rrd_schema = [
		"DS:user:GAUGE:120:0:U",
		"DS:nice:GAUGE:120:0:U",
		"DS:sys:GAUGE:120:0:U",
		"DS:idle:GAUGE:120:0:U",
		"DS:wait:GAUGE:120:0:U",
		"DS:irq:GAUGE:120:0:U",
		"DS:sirq:GAUGE:120:0:U",
		"RRA:AVERAGE:0.5:1:2160",
		"RRA:AVERAGE:0.5:5:2016",
		"RRA:AVERAGE:0.5:15:2880",
		"RRA:AVERAGE:0.5:60:8760",
	]

	_graph = [ "DEF:user=%(file)s:user:AVERAGE",
			   "DEF:nice=%(file)s:nice:AVERAGE",
			   "DEF:sys=%(file)s:sys:AVERAGE",
			   "DEF:idle=%(file)s:idle:AVERAGE",
			   "DEF:wait=%(file)s:wait:AVERAGE",
			   "DEF:interrupt=%(file)s:interrupt:AVERAGE",
			   "AREA:user#ff0000:%-15s" % _("User"),
			     "VDEF:usermin=user,MINIMUM",
			     "VDEF:usermax=user,MAXIMUM",
			     "VDEF:useravg=user,AVERAGE",
			     "GPRINT:usermax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:usermin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:useravg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:nice#ff3300:%-15s" % _("Nice"),
			   	 "VDEF:nicemin=nice,MINIMUM",
			     "VDEF:nicemax=nice,MAXIMUM",
			     "VDEF:niceavg=nice,AVERAGE",
			     "GPRINT:nicemax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:nicemin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:niceavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:sys#ff6600:%-15s" % _("System"),
			     "VDEF:sysmin=sys,MINIMUM",
			     "VDEF:sysmax=sys,MAXIMUM",
			     "VDEF:sysavg=sys,AVERAGE",
			     "GPRINT:sysmax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:sysmin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:sysavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:wait#ff9900:%-15s" % _("Wait"),
			     "VDEF:waitmin=wait,MINIMUM",
			     "VDEF:waitmax=wait,MAXIMUM",
			     "VDEF:waitavg=wait,AVERAGE",
			     "GPRINT:waitmax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:waitmin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:waitavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:interrupt#ffcc00:%-15s" % _("Interrupt"),
			     "VDEF:interruptmin=interrupt,MINIMUM",
			     "VDEF:interruptmax=interrupt,MAXIMUM",
			     "VDEF:interruptavg=interrupt,AVERAGE",
			     "GPRINT:interruptmax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:interruptmin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:interruptavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:idle#ffff00:%-15s" % _("Idle"),
			     "VDEF:idlemin=idle,MINIMUM",
			     "VDEF:idlemax=idle,MAXIMUM",
			     "VDEF:idleavg=idle,AVERAGE",
			   "GPRINT:idlemax:%12s\:" % _("Maximum") + " %6.2lf" ,
			   "GPRINT:idlemin:%12s\:" % _("Minimum") + " %6.2lf",
			   "GPRINT:idleavg:%12s\:" % _("Average") + " %6.2lf\\n", ]

	def read(self):
		"""
			Reads the CPU usage in jiffies.
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

				entry = [
					columns[1], # user
					columns[2], # nice
					columns[3], # sys
					columns[4], # idle
					columns[5], # wait
					columns[6], # irq
					columns[7], # sirq
				]

				full = sum([int(e) for e in entry])

				for i in range(len(entry)):
					entry[i] = float(entry[i]) * 100
					entry[i] = "%s" % (entry[i] / full)

				entry.insert(0, "%s" % self.now)

				self.data.append(":".join(entry))
				break

		finally:
			if f:
				f.close()