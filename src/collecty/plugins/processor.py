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
from ..constants import *

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

			# Headline
			"COMMENT:%s" % EMPTY_LABEL,
			"COMMENT:%s" % (COLUMN % _("Current")),
			"COMMENT:%s" % (COLUMN % _("Average")),
			"COMMENT:%s" % (COLUMN % _("Minimum")),
			"COMMENT:%s\\j" % (COLUMN % _("Maximum")),

			"CDEF:usage_p=100,usage,*,total,/",
			"COMMENT:  %s" % (LABEL % _("Total")),
			"GPRINT:usage_p_cur:%s" % PERCENTAGE,
			"GPRINT:usage_p_avg:%s" % PERCENTAGE,
			"GPRINT:usage_p_min:%s" % PERCENTAGE,
			"GPRINT:usage_p_max:%s\\j" % PERCENTAGE,

			EMPTY_LINE,

			"CDEF:user_p=100,user,*,total,/",
			"AREA:user_p%s:%s" % (
				transparency(CPU_USER, AREA_OPACITY),
				LABEL % _("User"),
			),
			"GPRINT:user_p_cur:%s" % PERCENTAGE,
			"GPRINT:user_p_avg:%s" % PERCENTAGE,
			"GPRINT:user_p_min:%s" % PERCENTAGE,
			"GPRINT:user_p_max:%s\\j" % PERCENTAGE,

			"CDEF:nice_p=100,nice,*,total,/",
			"STACK:nice_p%s:%s" % (
				transparency(CPU_NICE, AREA_OPACITY),
				LABEL % _("Nice"),
			),
			"GPRINT:nice_p_cur:%s" % PERCENTAGE,
			"GPRINT:nice_p_avg:%s" % PERCENTAGE,
			"GPRINT:nice_p_min:%s" % PERCENTAGE,
			"GPRINT:nice_p_max:%s\\j" % PERCENTAGE,

			"CDEF:sys_p=100,sys,*,total,/",
			"STACK:sys_p%s:%s" % (
				transparency(CPU_SYS, AREA_OPACITY),
				LABEL % _("System"),
			),
			"GPRINT:sys_p_cur:%s" % PERCENTAGE,
			"GPRINT:sys_p_avg:%s" % PERCENTAGE,
			"GPRINT:sys_p_min:%s" % PERCENTAGE,
			"GPRINT:sys_p_max:%s\\j" % PERCENTAGE,

			"CDEF:wait_p=100,wait,*,total,/",
			"STACK:wait_p%s:%s" % (
				transparency(CPU_WAIT, AREA_OPACITY),
				LABEL % _("Wait"),
			),
			"GPRINT:wait_p_cur:%s" % PERCENTAGE,
			"GPRINT:wait_p_avg:%s" % PERCENTAGE,
			"GPRINT:wait_p_min:%s" % PERCENTAGE,
			"GPRINT:wait_p_max:%s\\j" % PERCENTAGE,

			"CDEF:irq_p=100,irq,*,total,/",
			"STACK:irq_p%s:%s" % (
				transparency(CPU_IRQ, AREA_OPACITY),
				LABEL % _("Interrupt"),
			),
			"GPRINT:irq_p_cur:%s" % PERCENTAGE,
			"GPRINT:irq_p_avg:%s" % PERCENTAGE,
			"GPRINT:irq_p_min:%s" % PERCENTAGE,
			"GPRINT:irq_p_max:%s\\j" % PERCENTAGE,

			"CDEF:sirq_p=100,sirq,*,total,/",
			"STACK:sirq_p%s:%s" % (
				transparency(CPU_SIRQ, AREA_OPACITY),
				LABEL % _("Soft Interrupt"),
			),
			"GPRINT:sirq_p_cur:%s" % PERCENTAGE,
			"GPRINT:sirq_p_avg:%s" % PERCENTAGE,
			"GPRINT:sirq_p_min:%s" % PERCENTAGE,
			"GPRINT:sirq_p_max:%s\\j" % PERCENTAGE,

			"CDEF:steal_p=100,steal,*,total,/",
			"STACK:steal_p%s:%s" % (
				transparency(CPU_STEAL, AREA_OPACITY),
				LABEL % _("Steal"),
			),
			"GPRINT:steal_p_cur:%s" % PERCENTAGE,
			"GPRINT:steal_p_avg:%s" % PERCENTAGE,
			"GPRINT:steal_p_min:%s" % PERCENTAGE,
			"GPRINT:steal_p_max:%s\\j" % PERCENTAGE,

			"CDEF:guest_p=100,guest,*,total,/",
			"STACK:guest_p%s:%s" % (
				transparency(CPU_GUEST, AREA_OPACITY),
				LABEL % _("Guest"),
			),
			"GPRINT:guest_p_cur:%s" % PERCENTAGE,
			"GPRINT:guest_p_avg:%s" % PERCENTAGE,
			"GPRINT:guest_p_min:%s" % PERCENTAGE,
			"GPRINT:guest_p_max:%s\\j" % PERCENTAGE,

			"CDEF:guest_nice_p=100,guest_nice,*,total,/",
			"STACK:guest_nice_p%s:%s" % (
				transparency(CPU_GUEST_NICE, AREA_OPACITY),
				LABEL % _("Guest Nice"),
			),
			"GPRINT:guest_nice_p_cur:%s" % PERCENTAGE,
			"GPRINT:guest_nice_p_avg:%s" % PERCENTAGE,
			"GPRINT:guest_nice_p_min:%s" % PERCENTAGE,
			"GPRINT:guest_nice_p_max:%s\\j" % PERCENTAGE,

			"CDEF:idle_p=100,idle,*,total,/",
			"STACK:idle_p%s" % CPU_IDLE,

			# Draw contour lines
			"LINE:user_p%s" % CPU_USER,
			"LINE:nice_p%s::STACK" % CPU_NICE,
			"LINE:sys_p%s::STACK" % CPU_SYS,
			"LINE:wait_p%s::STACK" % CPU_WAIT,
			"LINE:irq_p%s::STACK" % CPU_IRQ,
			"LINE:sirq_p%s::STACK" % CPU_SIRQ,
			"LINE:steal_p%s::STACK" % CPU_STEAL,
			"LINE:guest_p%s::STACK" % CPU_GUEST,
			"LINE:guest_nice_p%s::STACK" % CPU_GUEST_NICE,
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
