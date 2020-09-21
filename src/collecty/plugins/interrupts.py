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

import os
import re

from . import base

from ..colours import *

class GraphTemplateSystemInterrupts(base.GraphTemplate):
	name = "system-interrupts"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			"AREA:intr%s:%-15s" % (
				lighten(PRIMARY, AREA_OPACITY), _("System Interrupts"),
			),
			"GPRINT:intr_max:%12s\:" % _("Maximum") + " %6.2lf" ,
			"GPRINT:intr_min:%12s\:" % _("Minimum") + " %6.2lf" ,
			"GPRINT:intr_avg:%12s\:" % _("Average") + " %6.2lf\\n",
			"LINE1:intr%s" % PRIMARY,
		]

	lower_limit = 0

	@property
	def graph_title(self):
		_ = self.locale.translate

		if self.object.irq is None:
			return _("System Interrupts")

		return _("Interrupt %s") % self.object.irq

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate

		return _("Interrupts/s")


class SystemInterruptObject(base.Object):
	rrd_schema = [
		"DS:intr:DERIVE:0:U",
	]

	def init(self, irq=None):
		self.irq = irq

	@property
	def id(self):
		if self.irq is None:
			return "default"

		return "%s" % self.irq

	def collect(self):
		stat = self.read_proc_stat()

		# Get a list of all interrupt events
		interrupts = stat.get("intr").split()

		# The first value is the sum of all interrupts
		total = interrupts.pop(0)

		if self.irq is None:
			return total

		# Otherwise return the value for a specific IRQ
		return interrupts[self.irq]


class SystemInterruptsPlugin(base.Plugin):
	name = "system-interrupts"
	description = "System Interrupts Plugin"

	templates = [GraphTemplateSystemInterrupts]

	@property
	def objects(self):
		yield SystemInterruptObject(self)

		for irq in os.listdir("/sys/kernel/irq"):
			try:
				irq = int(irq)
			except (ValueError, TypeError):
				continue

			yield SystemInterruptObject(self, irq)
