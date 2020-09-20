#!/usr/bin/python3
# encoding: utf-8
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

from .. import _collecty
from . import base

class GraphTemplateSensorsTemperature(base.GraphTemplate):
	name = "sensors-temperature"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			# Convert everything to Celsius
			"CDEF:value_c=value,273.15,-",
			"CDEF:critical_c=critical,273.15,-",
			"CDEF:high_c=high,273.15,-",
			"CDEF:low_c=low,273.15,-",

			# Change colour when the value gets above high
			"CDEF:value_c_high=value_c,high_c,GT,value_c,UNKN,IF",
			"CDEF:value_c_normal=value_c,high_c,GT,UNKN,value_c,IF",

			# Get data points for the threshold lines
			"VDEF:critical_c_line=critical_c,MINIMUM",
			"VDEF:low_c_line=low_c,MAXIMUM",

			# Draw the temperature value
			"LINE3:value_c_high#ff0000",
			"LINE2:value_c_normal#00ff00:%-15s" % _("Temperature"),

			# Draw the legend
			"GPRINT:value_c_cur:%10.2lf °C\l",
			"GPRINT:value_c_avg:  %-15s %%6.2lf °C\l" % _("Average"),
			"GPRINT:value_c_max:  %-15s %%6.2lf °C\l" % _("Maximum"),
			"GPRINT:value_c_min:  %-15s %%6.2lf °C\l" % _("Minimum"),

			# Empty line
			"COMMENT: \\n",

			# Draw boundary lines
			"COMMENT:%s\:" % _("Temperature Thresholds"),
			"HRULE:critical_c_line#000000:%-15s" % _("Critical"),
			"GPRINT:critical_c_line:%6.2lf °C\\r",
			"HRULE:low_c_line#0000ff:%-15s" % _("Low"),
			"GPRINT:low_c_line:%6.2lf °C\\r",
		]

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Temperature (%s)") % self.object.sensor.name

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("° Celsius")


class GraphTemplateSensorsProcessorTemperature(base.GraphTemplate):
	name = "processor-temperature"

	core_colours = [
		"#ff000033",
		"#0000ff33",
		"#00ff0033",
		"#0000ff33",
	]

	def get_temperature_sensors(self):
		# Use the coretemp module if available
		sensors = self.plugin.get_detected_sensor_objects("coretemp-*")

		# Fall back to the ACPI sensor
		if not sensors:
			sensors = self.plugin.get_detected_sensor_objects("acpitz-virtual-*")

		return sensors

	def get_objects(self, *args, **kwargs):
		sensors = self.get_temperature_sensors()

		return list(sensors)

	@property
	def rrd_graph(self):
		_ = self.locale.translate
		rrd_graph = []

		counter = 0
		ids = []

		for core in self.objects:
			id = "core%s" % counter
			ids.append(id)
			counter += 1

			rrd_graph += core.make_rrd_defs(id) + [
				# Convert everything to celsius
				"CDEF:%s_value_c=%s_value,273.15,-" % (id, id),
				"CDEF:%s_critical_c=%s_critical,273.15,-" % (id, id),
				"CDEF:%s_high_c=%s_high,273.15,-" % (id, id),
			]

		# Compute the temperature of the processor
		# by taking the average of all cores
		all_core_values = ("%s_value_c" % id for id in ids)
		rrd_graph += [
			"CDEF:all_value_c=%s,%s,AVG" % (",".join(all_core_values), len(ids)),
		]

		# Get the high threshold of the first core
		# (assuming that all cores have the same threshold)
		for id in ids:
			rrd_graph.append("CDEF:all_high_c=%s_high_c" % id)
			break

		rrd_graph += [
			# Change colour when the value gets above high
			"CDEF:all_value_c_high=all_value_c,all_high_c,GT,all_value_c,UNKN,IF",
			"CDEF:all_value_c_normal=all_value_c,all_high_c,GT,UNKN,all_value_c,IF",

			"LINE2:all_value_c_high#FF0000",
			"LINE2:all_value_c_normal#000000:%-15s\l" % _("Temperature"),

			"GPRINT:all_value_c_avg:    %-15s %%6.2lf °C\l" % _("Average"),
			"GPRINT:all_value_c_max:    %-15s %%6.2lf °C\l" % _("Maximum"),
			"GPRINT:all_value_c_min:    %-15s %%6.2lf °C\l" % _("Minimum"),
		]

		for id, core, colour in zip(ids, self.objects, self.core_colours):
			rrd_graph += [
				# TODO these lines were supposed to be dashed, but that
				# didn't really work here
				"LINE1:%s_value_c%s:%-10s" % (id, colour, core.sensor.label),
			]

		# Draw the critical line
		for id in ids:
			rrd_graph += [
				"HRULE:%s_critical_c_min#000000:%-15s" % (id, _("Critical")),
				"GPRINT:%s_critical_c_min:%%6.2lf °C\\r" % id,
			]
			break

		return rrd_graph

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Processor")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Temperature")


class SensorBaseObject(base.Object):
	def init(self, sensor):
		self.sensor = sensor

	def __repr__(self):
		return "<%s %s (%s)>" % (self.__class__.__name__, self.sensor.name, self.sensor.label)

	@property
	def id(self):
		return "-".join((self.sensor.name, self.sensor.label))

	@property
	def type(self):
		return self.sensor.type


class SensorTemperatureObject(SensorBaseObject):
	rrd_schema = [
		"DS:value:GAUGE:0:U",
		"DS:critical:GAUGE:0:U",
		"DS:low:GAUGE:0:U",
		"DS:high:GAUGE:0:U",
	]

	def collect(self):
		assert self.type == "temperature"

		return (
			self.sensor.value,
			self.critical,
			self.low,
			self.high,
		)

	@property
	def critical(self):
		try:
			return self.sensor.critical
		except AttributeError:
			return "NaN"

	@property
	def low(self):
		try:
			return self.sensor.minimum
		except AttributeError:
			return "NaN"

	@property
	def high(self):
		try:
			return self.sensor.high
		except AttributeError:
			return "NaN"


class SensorVoltageObject(SensorBaseObject):
	rrd_schema = [
		"DS:value:GAUGE:0:U",
		"DS:minimum:GAUGE:0:U",
		"DS:maximum:GAUGE:0:U",
	]

	def collect(self):
		assert self.type == "voltage"

		return (
			self.sensor.value,
			self.minimum,
			self.maximum,
		)

	@property
	def minimum(self):
		try:
			return self.sensor.minimum
		except AttributeError:
			return "NaN"

	@property
	def maximum(self):
		try:
			return self.sensor.maximum
		except AttributeError:
			return "NaN"


class SensorFanObject(SensorBaseObject):
	rrd_schema = [
		"DS:value:GAUGE:0:U",
		"DS:minimum:GAUGE:0:U",
		"DS:maximum:GAUGE:0:U",
	]

	def collect(self):
		assert self.type == "fan"

		return (
			self.sensor.value,
			self.minimum,
			self.maximum,
		)

	@property
	def minimum(self):
		try:
			return self.sensor.minimum
		except AttributeError:
			return "NaN"

	@property
	def maximum(self):
		try:
			return self.sensor.maximum
		except AttributeError:
			return "NaN"


class SensorsPlugin(base.Plugin):
	name = "sensors"
	description = "Sensors Plugin"

	templates = [
		GraphTemplateSensorsProcessorTemperature,
		GraphTemplateSensorsTemperature,
	]

	def init(self):
		# Initialise the sensors library.
		_collecty.sensors_init()

	def __del__(self):
		_collecty.sensors_cleanup()

	@property
	def objects(self):
		return self.get_detected_sensor_objects()

	def get_detected_sensor_objects(self, what=None):
		for sensor in _collecty.get_detected_sensors(what):
			if sensor.type == "temperature":
				yield SensorTemperatureObject(self, sensor)

			elif sensor.type == "voltage":
				yield SensorVoltageObject(self, sensor)

			elif sensor.type == "fan":
				yield SensorFanObject(self, sensor)
