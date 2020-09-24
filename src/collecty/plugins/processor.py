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

import multiprocessing

from . import base

from ..colours import *

class GraphTemplateProcessor(base.GraphTemplate):
	name = "processor"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			# Add all used CPU cycles
			"CDEF:usage=user,nice,+,sys,+,wait,+,irq,+,sirq,+,steal,+,guest,+,guest_nice,+",

			# Add idle to get the total number of cycles
			"CDEF:total=usage,idle,+",

			"CDEF:user_p=100,user,*,total,/",
			"AREA:user_p%s:%-15s" % (CPU_USER, _("User")),
			"GPRINT:user_p_max:%12s\:" % _("Maximum") + " %6.2lf%%",
			"GPRINT:user_p_min:%12s\:" % _("Minimum") + " %6.2lf%%",
			"GPRINT:user_p_avg:%12s\:" % _("Average") + " %6.2lf%%\\n",

			"CDEF:nice_p=100,nice,*,total,/",
			"STACK:nice_p%s:%-15s" % (CPU_NICE, _("Nice")),
			"GPRINT:nice_p_max:%12s\:" % _("Maximum") + " %6.2lf%%",
			"GPRINT:nice_p_min:%12s\:" % _("Minimum") + " %6.2lf%%",
			"GPRINT:nice_p_avg:%12s\:" % _("Average") + " %6.2lf%%\\n",

			"CDEF:sys_p=100,sys,*,total,/",
			"STACK:sys_p%s:%-15s" % (CPU_SYS, _("System")),
			"GPRINT:sys_p_max:%12s\:" % _("Maximum") + " %6.2lf%%",
			"GPRINT:sys_p_min:%12s\:" % _("Minimum") + " %6.2lf%%",
			"GPRINT:sys_p_avg:%12s\:" % _("Average") + " %6.2lf%%\\n",

			"CDEF:wait_p=100,wait,*,total,/",
			"STACK:wait_p%s:%-15s" % (CPU_WAIT, _("Wait")),
			"GPRINT:wait_p_max:%12s\:" % _("Maximum") + " %6.2lf%%",
			"GPRINT:wait_p_min:%12s\:" % _("Minimum") + " %6.2lf%%",
			"GPRINT:wait_p_avg:%12s\:" % _("Average") + " %6.2lf%%\\n",

			"CDEF:irq_p=100,irq,*,total,/",
			"STACK:irq_p%s:%-15s" % (CPU_IRQ, _("Interrupt")),
			"GPRINT:irq_p_max:%12s\:" % _("Maximum") + " %6.2lf%%",
			"GPRINT:irq_p_min:%12s\:" % _("Minimum") + " %6.2lf%%",
			"GPRINT:irq_p_avg:%12s\:" % _("Average") + " %6.2lf%%\\n",

			"CDEF:sirq_p=100,sirq,*,total,/",
			"STACK:sirq_p%s:%-15s" % (CPU_SIRQ, _("Soft Interrupt")),
			"GPRINT:sirq_p_max:%12s\:" % _("Maximum") + " %6.2lf%%",
			"GPRINT:sirq_p_min:%12s\:" % _("Minimum") + " %6.2lf%%",
			"GPRINT:sirq_p_avg:%12s\:" % _("Average") + " %6.2lf%%\\n",

			"CDEF:steal_p=100,steal,*,total,/",
			"STACK:steal_p%s:%-15s" % (CPU_STEAL, _("Steal")),
			"GPRINT:steal_p_max:%12s\:" % _("Maximum") + " %6.2lf%%",
			"GPRINT:steal_p_min:%12s\:" % _("Minimum") + " %6.2lf%%",
			"GPRINT:steal_p_avg:%12s\:" % _("Average") + " %6.2lf%%\\n",

			"CDEF:guest_p=100,guest,*,total,/",
			"STACK:guest_p%s:%-15s" % (CPU_GUEST, _("Guest")),
			"GPRINT:guest_p_max:%12s\:" % _("Maximum") + " %6.2lf%%",
			"GPRINT:guest_p_min:%12s\:" % _("Minimum") + " %6.2lf%%",
			"GPRINT:guest_p_avg:%12s\:" % _("Average") + " %6.2lf%%\\n",

			"CDEF:guest_nice_p=100,guest_nice,*,total,/",
			"STACK:guest_nice_p%s:%-15s" % (CPU_GUEST_NICE, _("Guest Nice")),
			"GPRINT:guest_nice_p_max:%12s\:" % _("Maximum") + " %6.2lf%%",
			"GPRINT:guest_nice_p_min:%12s\:" % _("Minimum") + " %6.2lf%%",
			"GPRINT:guest_nice_p_avg:%12s\:" % _("Average") + " %6.2lf%%\\n",

			"CDEF:usage_p=100,usage,*,total,/",
			"COMMENT:  %-15s" % _("Usage"),
			"GPRINT:usage_p_max:%12s\:" % _("Maximum") + " %6.2lf%%",
			"GPRINT:usage_p_min:%12s\:" % _("Minimum") + " %6.2lf%%",
			"GPRINT:usage_p_avg:%12s\:" % _("Average") + " %6.2lf%%\\n",

			"CDEF:idle_p=100,idle,*,total,/",
			"STACK:idle_p%s:%-15s" % (CPU_IDLE, _("Idle")),
			"GPRINT:idle_p_max:%12s\:" % _("Maximum") + " %6.2lf%%",
			"GPRINT:idle_p_min:%12s\:" % _("Minimum") + " %6.2lf%%",
			"GPRINT:idle_p_avg:%12s\:" % _("Average") + " %6.2lf%%\\n",
		]

	upper_limit = 100
	lower_limit = 0

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Processor Usage")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Percent")


class ProcessorObject(base.Object):
	rrd_schema = [
		"DS:user:DERIVE:0:U",
		"DS:nice:DERIVE:0:U",
		"DS:sys:DERIVE:0:U",
		"DS:idle:DERIVE:0:U",
		"DS:wait:DERIVE:0:U",
		"DS:irq:DERIVE:0:U",
		"DS:sirq:DERIVE:0:U",
		"DS:steal:DERIVE:0:U",
		"DS:guest:DERIVE:0:U",
		"DS:guest_nice:DERIVE:0:U",
	]

	def init(self, cpu_id=None):
		self.cpu_id = cpu_id

	@property
	def id(self):
		if self.cpu_id is not None:
			return "%s" % self.cpu_id

		return "default"

	def collect(self):
		"""
			Reads the CPU usage.
		"""
		stat = self.read_proc_stat()

		if self.cpu_id is None:
			values = stat.get("cpu")
		else:
			values = stat.get("cpu%s" % self.cpu_id)

		# Convert values into a list
		values = values.split()

		if not len(values) == len(self.rrd_schema):
			raise ValueError("Received unexpected output from /proc/stat: %s" % values)

		return values


class ProcessorPlugin(base.Plugin):
	name = "processor"
	description = "Processor Usage Plugin"

	templates = [GraphTemplateProcessor]

	@property
	def objects(self):
		yield ProcessorObject(self)

		num = multiprocessing.cpu_count()
		for i in range(num):
			yield ProcessorObject(self, cpu_id=i)
