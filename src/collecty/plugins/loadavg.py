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

from ..colours import *

class GraphTemplateLoadAvg(base.GraphTemplate):
	name = "loadavg"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		rrd_graph = []

		for id, colour, when in zip(self.object.rrd_schema_names,
				LOAD_AVG_COLOURS, ("1m", "5m", "15m")):
			rrd_graph = [
				"LINE2:%s%s:%-24s" % (id, colour, _("Load Average %s") % when),
				"GPRINT:%s_max:%12s\: %%6.2lf" % (id, _("Maximum")),
				"GPRINT:%s_min:%12s\: %%6.2lf" % (id, _("Minimum")),
				"GPRINT:%s_avg:%12s\: %%6.2lf\l" % (id, _("Average")),
			] + rrd_graph

		return rrd_graph

	lower_limit = 0

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Load Average")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Load")

	@property
	def rrd_graph_args(self):
		return [
			"--legend-direction=bottomup",
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
		return os.getloadavg()


class LoadAvgPlugin(base.Plugin):
	name = "loadavg"
	description = "Load Average Plugin"

	templates = [GraphTemplateLoadAvg]

	@property
	def objects(self):
		return [LoadAvgObject(self)]
