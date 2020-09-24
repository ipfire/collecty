#!/usr/bin/python3
###############################################################################
#                                                                             #
# collecty - A system statistics collection daemon for IPFire                 #
# Copyright (C) 2015 IPFire development team                                  #
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

import re

from . import base

from ..colours import *
from ..constants import *

class GraphTemplateContextSwitches(base.GraphTemplate):
	name = "context-switches"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			"COMMENT:%s" % (LEGEND % ""),
			"COMMENT:%s" % (LEGEND % _("Current")),
			"COMMENT:%s" % (LEGEND % _("Average")),
			"COMMENT:%s" % (LEGEND % _("Minimum")),
			"COMMENT:%s\\j" % (LEGEND % _("Maximum")),

			"AREA:ctxt%s:%s" % (
				lighten(PRIMARY, AREA_OPACITY),
				LABEL % _("Context Switches"),
			),
			"GPRINT:ctxt_cur:%s" % INTEGER,
			"GPRINT:ctxt_avg:%s" % INTEGER,
			"GPRINT:ctxt_min:%s" % INTEGER,
			"GPRINT:ctxt_max:%s" % INTEGER,
			"LINE2:ctxt%s" % PRIMARY,
		]

	lower_limit = 0

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Context Switches")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Context Switches/s")


class ContextSwitchesObject(base.Object):
	rrd_schema = [
		"DS:ctxt:DERIVE:0:U",
	]

	@property
	def id(self):
		return "default"

	def collect(self):
		expr = r"^ctxt (\d+)$"

		with open("/proc/stat") as f:
			for line in f.readlines():
				m = re.match(expr, line)
				if m:
					return m.group(1)


class ContextSwitchesPlugin(base.Plugin):
	name = "context-switches"
	description = "Context Switches Plugin"

	templates = [GraphTemplateContextSwitches]

	@property
	def objects(self):
		yield ContextSwitchesObject(self)
