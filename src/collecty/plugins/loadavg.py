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

import os

from . import base

from ..i18n import _

class GraphTemplateLoadAvg(base.GraphTemplate):
	name = "loadavg"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			"AREA:load1#ff0000:%s" % _("Load average  1m"),
			"GPRINT:load1_max:%12s\:" % _("Maximum") + " %6.2lf",
			"GPRINT:load1_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:load1_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"AREA:load5#ff9900:%s" % _("Load average  5m"),
			"GPRINT:load5_max:%12s\:" % _("Maximum") + " %6.2lf",
			"GPRINT:load5_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:load5_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"AREA:load15#ffff00:%s" % _("Load average 15m"),
			"GPRINT:load15_max:%12s\:" % _("Maximum") + " %6.2lf",
			"GPRINT:load15_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:load15_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"LINE:load5#dd8800",
			"LINE:load1#dd0000",
		]

	lower_limit = 0

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Load average")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Load")


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
		return os.getloadavg()


class LoadAvgPlugin(base.Plugin):
	name = "loadavg"
	description = "Load Average Plugin"

	templates = [GraphTemplateLoadAvg]

	@property
	def objects(self):
		return [LoadAvgObject(self)]
