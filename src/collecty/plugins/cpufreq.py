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

from ..i18n import _

class GraphTemplateCPUFreq(base.GraphTemplate):
	name = "cpufreq"

	lower_limit = 0

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Processor Frequencies")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return "%s [%s]" % (_("Frequency"), _("Hz"))

	def get_object_table(self):
		objects_table = {}

		for processor in self.plugin.objects:
			objects_table[processor.id] = processor

		return objects_table

	core_colours = {
		"cpu0" : "#ff000066",
		"cpu1" : "#00ff0066",
		"cpu2" : "#0000ff66",
		"cpu3" : "#ffff0066",
	}

	@property
	def rrd_graph(self):
		rrd_graph = []

		for core, processor in sorted(self.object_table.items()):
			i = {
				"core"   : core,
				"colour" : self.core_colours.get(core, "#000000"),
				"name"   : processor.name,
			}

			core_graph = [
				"DEF:current_%(core)s=%%(%(core)s)s:current:AVERAGE",
				"DEF:minimum_%(core)s=%%(%(core)s)s:minimum:AVERAGE",
				"DEF:maximum_%(core)s=%%(%(core)s)s:maximum:AVERAGE",

				"VDEF:avg_%(core)s=current_%(core)s,AVERAGE",

				"LINE2:current_%(core)s%(colour)s:%(name)-10s",
				"GPRINT:avg_%(core)s:%%6.2lf %%sHz\l",
			]

			rrd_graph += [line % i for line in core_graph]

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
		return self.read_file("topology/core_id")

	def is_cpufreq_supported(self):
		path = os.path.join(self.sys_path, "cpufreq")

		return os.path.exists(path)

	def collect(self):
		return (
			self.read_frequency("cpufreq/cpuinfo_cur_freq"),
			self.read_frequency("cpufreq/cpuinfo_min_freq"),
			self.read_frequency("cpufreq/cpuinfo_max_freq"),
		)

	def read_file(self, filename):
		file = os.path.join(self.sys_path, filename)

		with open(file, "r") as f:
			return f.read().strip()

	def read_frequency(self, filename):
		val = self.read_file(filename)

		# Convert from kHz to Hz
		return int(val) * 1000


class CPUFreqPlugin(base.Plugin):
	name = "cpufreq"
	description = "cpufreq Plugin"

	templates = [GraphTemplateCPUFreq]

	cpuid_pattern = re.compile(r"cpu[0-9]+")

	@property
	def objects(self):
		core_ids = []

		for cpuid in os.listdir("/sys/devices/system/cpu"):
			if not self.cpuid_pattern.match(cpuid):
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
