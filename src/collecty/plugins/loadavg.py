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

class GraphTemplateLoadAvg(base.GraphTemplate):
	name = "loadavg"

	rrd_graph = [
		"DEF:load1=%(file)s:load1:AVERAGE",
		"DEF:load5=%(file)s:load5:AVERAGE",
		"DEF:load15=%(file)s:load15:AVERAGE",

		"AREA:load1#ff0000:%s" % _("Load average  1m"),
		"VDEF:load1min=load1,MINIMUM",
		"VDEF:load1max=load1,MAXIMUM",
		"VDEF:load1avg=load1,AVERAGE",
		"GPRINT:load1max:%12s\:" % _("Maximum") + " %6.2lf",
		"GPRINT:load1min:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:load1avg:%12s\:" % _("Average") + " %6.2lf\\n",

		"AREA:load5#ff9900:%s" % _("Load average  5m"),
		"VDEF:load5min=load5,MINIMUM",
		"VDEF:load5max=load5,MAXIMUM",
		"VDEF:load5avg=load5,AVERAGE",
		"GPRINT:load5max:%12s\:" % _("Maximum") + " %6.2lf",
		"GPRINT:load5min:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:load5avg:%12s\:" % _("Average") + " %6.2lf\\n",

		"AREA:load15#ffff00:%s" % _("Load average 15m"),
		"VDEF:load15min=load15,MINIMUM",
		"VDEF:load15max=load15,MAXIMUM",
		"VDEF:load15avg=load15,AVERAGE",
		"GPRINT:load15max:%12s\:" % _("Maximum") + " %6.2lf",
		"GPRINT:load15min:%12s\:" % _("Minimum") + " %6.2lf",
		"GPRINT:load15avg:%12s\:" % _("Average") + " %6.2lf\\n",

		"LINE:load5#dd8800",
		"LINE:load1#dd0000",
	]

	rrd_graph_args = [
		"--title", _("Load average"),
		"--vertical-label", _("Load"),

		"--lower-limit", "0", "--rigid",
	]


class LoadAvgObject(base.Object):
	rrd_schema = [
		"DS:load1:GAUGE:0:U",
		"DS:load5:GAUGE:0:U",
		"DS:load15:GAUGE:0:U",
	]

	@property
	def id(self):
		return "default"

	def collect(self):
		return ":".join(["%.10f" % l for l in os.getloadavg()])


class LoadAvgPlugin(base.Plugin):
	name = "loadavg"
	description = "Load Average Plugin"

	templates = [GraphTemplateLoadAvg,]

	interval = 30

	@property
	def objects(self):
		return [LoadAvgObject(self)]
