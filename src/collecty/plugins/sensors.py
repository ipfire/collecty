#!/usr/bin/python
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

from collecty import _collecty
import os
import re

import base

from ..i18n import _

class GraphTemplateSensorsTemperature(base.GraphTemplate):
	name = "sensors-temperature"

	rrd_graph = [
		"DEF:value_kelvin=%(file)s:value:AVERAGE",
		"DEF:critical_kelvin=%(file)s:critical:AVERAGE",
		"DEF:high_kelvin=%(file)s:high:AVERAGE",
		"DEF:low_kelvin=%(file)s:low:AVERAGE",

		# Convert everything to celsius
		"CDEF:value=value_kelvin,273.15,-",
		"CDEF:critical=critical_kelvin,273.15,-",
		"CDEF:high=high_kelvin,273.15,-",
		"CDEF:low=low_kelvin,273.15,-",

		# Change colour when the value gets above high
		"CDEF:value_high=value,high,GT,value,UNKN,IF",
		"CDEF:value_normal=value,high,GT,UNKN,value,IF",

		"VDEF:value_cur=value,LAST",
		"VDEF:value_avg=value,AVERAGE",
		"VDEF:value_max=value,MAXIMUM",
		"VDEF:value_min=value,MINIMUM",

		# Get data points for the threshold lines
		"VDEF:critical_line=critical,MINIMUM",
		"VDEF:low_line=low,MAXIMUM",

		# Draw the temperature value
		"LINE3:value_high#ff0000",
		"LINE2:value_normal#00ff00:%-15s" % _("Temperature"),

		# Draw the legend
		"GPRINT:value_cur:%%10.2lf °C\l",
		"GPRINT:value_avg:  %-15s %%6.2lf °C\l" % _("Average"),
		"GPRINT:value_max:  %-15s %%6.2lf °C\l" % _("Maximum"),
		"GPRINT:value_min:  %-15s %%6.2lf °C\l" % _("Minimum"),

		# Empty line
		"COMMENT: \\n",

		# Draw boundary lines
		"COMMENT:%s\:" % _("Temperature Thresholds"),
		"HRULE:critical_line#000000:%-15s" % _("Critical"),
		"GPRINT:critical_line:%%6.2lf °C\\r",
		"HRULE:low_line#0000ff:%-15s" % _("Low"),
		"GPRINT:low_line:%%6.2lf °C\\r",
	]

	@property
	def graph_title(self):
		return _("Temperature (%s)") % self.object.sensor.name

	@property
	def graph_vertical_label(self):
		return _("° Celsius")


class GraphTemplateSensorsProcessorTemperature(base.GraphTemplate):
	name = "processor-temperature"

	core_colours = {
		"core0" : "#ff000033",
		"core1" : "#0000ff33",
		"core2" : "#00ff0033",
		"core3" : "#0000ff33",
	}

	def get_temperature_sensors(self):
		return self.plugin.get_detected_sensor_objects("coretemp-*")

	def get_object_table(self):
		objects_table = {}

		counter = 0
		for object in self.get_temperature_sensors():
			objects_table["core%s" % counter] = object
			counter += 1

		return objects_table

	@property
	def rrd_graph(self):
		rrd_graph = []

		cores = sorted(self.object_table.keys())

		for core in cores:
			i = {
				"core" : core,
			}

			core_graph = [
				"DEF:value_kelvin_%(core)s=%%(%(core)s)s:value:AVERAGE",
				"DEF:critical_kelvin_%(core)s=%%(%(core)s)s:critical:AVERAGE",
				"DEF:high_kelvin_%(core)s=%%(%(core)s)s:high:AVERAGE",

				# Convert everything to celsius
				"CDEF:value_%(core)s=value_kelvin_%(core)s,273.15,-",
				"CDEF:critical_%(core)s=critical_kelvin_%(core)s,273.15,-",
				"CDEF:high_%(core)s=high_kelvin_%(core)s,273.15,-",
			]

			rrd_graph += [line % i for line in core_graph]

		all_core_values = ("value_%s" % c for c in cores)
		all_core_highs  = ("high_%s"  % c for c in cores)

		rrd_graph += [
			# Compute the temperature of the processor
			# by taking the average of all cores
			"CDEF:value=%s,%s,AVG" % (",".join(all_core_values), len(cores)),
			"CDEF:high=%s,MIN" % ",".join(all_core_highs),

			# Change colour when the value gets above high
			"CDEF:value_high=value,high,GT,value,UNKN,IF",
			"CDEF:value_normal=value,high,GT,UNKN,value,IF",

			"VDEF:value_avg=value,AVERAGE",
			"VDEF:value_max=value,MAXIMUM",
			"VDEF:value_min=value,MINIMUM",

			"LINE3:value_high#FF0000",
			"LINE3:value_normal#000000:%-15s\l" % _("Temperature"),

			"GPRINT:value_avg:    %-15s %%6.2lf °C\l" % _("Average"),
			"GPRINT:value_max:    %-15s %%6.2lf °C\l" % _("Maximum"),
			"GPRINT:value_min:    %-15s %%6.2lf °C\l" % _("Minimum"),
		]

		for core in cores:
			object = self.object_table.get(core)

			i = {
				"colour" : self.core_colours.get(core, "#000000"),
				"core"   : core,
				"label"  : object.sensor.label,
			}

			core_graph = [
				# TODO these lines were supposed to be dashed, but that
				# didn't really work here
				"LINE2:value_%(core)s%(colour)s:%(label)-10s",
			]

			rrd_graph += [line % i for line in core_graph]

		# Draw the critical line
		rrd_graph += [
			"VDEF:critical_line=critical_core0,MINIMUM",
			"HRULE:critical_line#000000:%-15s" % _("Critical"),
			"GPRINT:critical_line:%%6.2lf °C\\r",
		]

		return rrd_graph

	@property
	def graph_title(self):
		return _("Processor")

	@property
	def graph_vertical_label(self):
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
	def mimimum(self):
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
