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

ENTROPY_FILE = "/proc/sys/kernel/random/entropy_avail"

class GraphTemplateEntropy(base.GraphTemplate):
	name = "entropy"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			"DEF:entropy=%(file)s:entropy:AVERAGE",

			"LINE3:entropy#ff0000:%-15s" % _("Available entropy"),
			"VDEF:entrmin=entropy,MINIMUM",
			"VDEF:entrmax=entropy,MAXIMUM",
			"VDEF:entravg=entropy,AVERAGE",
			"GPRINT:entrmax:%12s\:" % _("Maximum") + " %5.0lf",
			"GPRINT:entrmin:%12s\:" % _("Minimum") + " %5.0lf",
			"GPRINT:entravg:%12s\:" % _("Average") + " %5.0lf\\n",
		]

	lower_limit = 0

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Available entropy")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Bit")


class EntropyObject(base.Object):
	rrd_schema = [
		"DS:entropy:GAUGE:0:U",
	]

	@property
	def id(self):
		return "default"

	def collect(self):
		with open(ENTROPY_FILE) as f:
			return f.readline().strip()


class EntropyPlugin(base.Plugin):
	name = "entropy"
	description = "Entropy Plugin"

	templates = [GraphTemplateEntropy]

	@property
	def objects(self):
		if not os.path.exists(ENTROPY_FILE):
			self.log.debug(_("Entropy kernel interface does not exist"))
			return []

		return [EntropyObject(self)]
