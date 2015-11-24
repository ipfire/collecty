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

from ..i18n import _

class GraphTemplateSystemInterrupts(base.GraphTemplate):
	name = "system-interrupts"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			"DEF:intr=%(file)s:intr:AVERAGE",

			"AREA:intr#90EE90:%-15s" % _("System Interrupts"),
			"VDEF:intrmax=intr,MAXIMUM",
			"VDEF:intrmin=intr,MINIMUM",
			"VDEF:intravg=intr,AVERAGE",
			"GPRINT:intrmax:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:intrmin:%12s\:" % _("Minimum") + " %6.2lf" ,
			"GPRINT:intravg:%12s\:" % _("Average") + " %6.2lf\\n",
		]

	lower_limit = 0

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("System Interrupts")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("System Interrupts/s")


class SystemInterruptsObject(base.Object):
	rrd_schema = [
		"DS:intr:DERIVE:0:U",
	]

	@property
	def id(self):
		return "default"

	def collect(self):
		expr = re.compile(r"^intr (\d+)")

		with open("/proc/stat") as f:
			for line in f.readlines():
				m = re.match(expr, line)
				if m:
					return m.group(1)


class SystemInterruptsPlugin(base.Plugin):
	name = "system-interrupts"
	description = "System Interrupts Plugin"

	templates = [GraphTemplateSystemInterrupts]

	@property
	def objects(self):
		yield SystemInterruptsObject(self)
