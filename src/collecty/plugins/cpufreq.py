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

class GraphTemplateCPUFreq(base.GraphTemplate):
	name = "cpufreq"

	lower_limit = 0

	def get_objects(self, *args, **kwargs):
		return list(self.plugin.objects)

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Processor Frequencies")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return "%s [%s]" % (_("Frequency"), _("Hz"))

	processor_colours = [
		"#ff000066",
		"#00ff0066",
		"#0000ff66",
		"#ffff0066",
	]

	@property
	def rrd_graph(self):
		rrd_graph = []

		for processor, colour in zip(self.objects, self.processor_colours):
			rrd_graph += processor.make_rrd_defs(processor.id) + [
				"LINE2:%s_current%s:%-10s" % (processor.id, colour, processor.name),
				"GPRINT:%s_current_avg:%%6.2lf %%sHz\l" % processor.id,
			]

		return rrd_graph

	rrd_graph_args = [
		"--base", "1000", # Hz
	]


class CPUFreqObject(base.Object):
	rrd_schema = [
		"DS:current:GAUGE:0:U",
		"DS:minimum:GAUGE:0:U",
		"DS:maximum:GAUGE:0:U",
	]

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.cpuid)

	def init(self, cpuid):
		self.cpuid = cpuid

		self.sys_path = os.path.join("/sys/devices/system/cpu", self.cpuid)

	@property
	def name(self):
		return "Core %s" % self.core_id

	@property
	def id(self):
		return self.cpuid

	@property
	def core_id(self):
		return self.read_file(self.sys_path, "topology/core_id")

	def is_cpufreq_supported(self):
		path = os.path.join(self.sys_path, "cpufreq")

		return os.path.exists(path)

	def collect(self):
		return (
			self.read_frequency("cpufreq/cpuinfo_cur_freq"),
			self.read_frequency("cpufreq/cpuinfo_min_freq"),
			self.read_frequency("cpufreq/cpuinfo_max_freq"),
		)

	def read_frequency(self, filename):
		val = self.read_file(self.sys_path, filename)

		# Convert from kHz to Hz
		return int(val) * 1000


class CPUFreqPlugin(base.Plugin):
	name = "cpufreq"
	description = "cpufreq Plugin"

	templates = [GraphTemplateCPUFreq]

	@property
	def objects(self):
		core_ids = []

		for cpuid in os.listdir("/sys/devices/system/cpu"):
			if not re.match(r"cpu[0-9]+", cpuid):
				continue

			o = CPUFreqObject(self, cpuid)

			# If we have already seen a virtual core of the processor,
			# we will skip any others.
			if o.core_id in core_ids:
				continue

			# Check if this processor is supported by cpufreq
			if not o.is_cpufreq_supported():
				continue

			# Save the ID of the added core
			core_ids.append(o.core_id)

			yield o
