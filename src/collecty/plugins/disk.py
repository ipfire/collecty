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

from collecty import _collecty
import os
import re

from . import base

from ..i18n import _

class GraphTemplateDiskBadSectors(base.GraphTemplate):
	name = "disk-bad-sectors"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			"AREA:bad_sectors#ff0000:%s" % _("Bad Sectors"),
			"GPRINT:bad_sectors_cur:%12s\:" % _("Current") + " %9.2lf",
			"GPRINT:bad_sectors_max:%12s\:" % _("Maximum") + " %9.2lf\\n",
		]

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Bad Sectors of %s") % self.object.device_string

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Pending/Relocated Sectors")


class GraphTemplateDiskBytes(base.GraphTemplate):
	name = "disk-bytes"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		rrd_graph = [
			"CDEF:read_bytes=read_sectors,512,*",
			"CDEF:write_bytes=write_sectors,512,*",

			"LINE1:read_bytes#ff0000:%-15s" % _("Read"),
			"GPRINT:read_bytes_cur:%12s\:" % _("Current") + " %9.2lf",
			"GPRINT:read_bytes_max:%12s\:" % _("Maximum") + " %9.2lf",
			"GPRINT:read_bytes_min:%12s\:" % _("Minimum") + " %9.2lf",
			"GPRINT:read_bytes_avg:%12s\:" % _("Average") + " %9.2lf\\n",

			"LINE1:write_bytes#00ff00:%-15s" % _("Written"),
			"GPRINT:write_bytes_cur:%12s\:" % _("Current") + " %9.2lf",
			"GPRINT:write_bytes_max:%12s\:" % _("Maximum") + " %9.2lf",
			"GPRINT:write_bytes_min:%12s\:" % _("Minimum") + " %9.2lf",
			"GPRINT:write_bytes_avg:%12s\:" % _("Average") + " %9.2lf\\n",
		]

		return rrd_graph

	lower_limit = 0

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Disk Utilisation of %s") % self.object.device_string

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Byte per Second")


class GraphTemplateDiskIoOps(base.GraphTemplate):
	name = "disk-io-ops"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		rrd_graph = [
			"LINE1:read_ios#ff0000:%-15s" % _("Read"),
			"GPRINT:read_ios_cur:%12s\:" % _("Current") + " %6.2lf",
			"GPRINT:read_ios_max:%12s\:" % _("Maximum") + " %6.2lf",
			"GPRINT:read_ios_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:read_ios_avg:%12s\:" % _("Average") + " %6.2lf\\n",

			"LINE1:write_ios#00ff00:%-15s" % _("Written"),
			"GPRINT:write_ios_cur:%12s\:" % _("Current") + " %6.2lf",
			"GPRINT:write_ios_max:%12s\:" % _("Maximum") + " %6.2lf",
			"GPRINT:write_ios_min:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:write_ios_avg:%12s\:" % _("Average") + " %6.2lf\\n",
		]

		return rrd_graph

	lower_limit = 0

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Disk IO Operations of %s") % self.object.device_string

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Operations per Second")


class GraphTemplateDiskTemperature(base.GraphTemplate):
	name = "disk-temperature"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		rrd_graph = [
			"CDEF:celsius=temperature,273.15,-",
			"VDEF:temp_cur=celsius,LAST",
			"VDEF:temp_min=celsius,MINIMUM",
			"VDEF:temp_max=celsius,MAXIMUM",
			"VDEF:temp_avg=celsius,AVERAGE",

			"LINE2:celsius#ff0000:%s" % _("Temperature"),
			"GPRINT:temp_cur:%12s\:" % _("Current") + " %3.2lf",
			"GPRINT:temp_max:%12s\:" % _("Maximum") + " %3.2lf",
			"GPRINT:temp_min:%12s\:" % _("Minimum") + " %3.2lf",
			"GPRINT:temp_avg:%12s\:" % _("Average") + " %3.2lf\\n",
		]

		return rrd_graph

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Disk Temperature of %s") % self.object.device_string

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("° Celsius")

	@property
	def rrd_graph_args(self):
		return [
			# Make the y-axis have a decimal
			"--left-axis-format", "%3.1lf",
		]


class DiskObject(base.Object):
	rrd_schema = [
		"DS:awake:GAUGE:0:1",
		"DS:read_ios:DERIVE:0:U",
		"DS:read_sectors:DERIVE:0:U",
		"DS:write_ios:DERIVE:0:U",
		"DS:write_sectors:DERIVE:0:U",
		"DS:bad_sectors:GAUGE:0:U",
		"DS:temperature:GAUGE:U:U",
	]

	def __repr__(self):
		return "<%s %s (%s)>" % (self.__class__.__name__, self.sys_path, self.id)

	def init(self, device):
		self.dev_path = os.path.join("/dev", device)
		self.sys_path = os.path.join("/sys/block", device)

		self.device = _collecty.BlockDevice(self.dev_path)

	@property
	def id(self):
		return "-".join((self.device.model, self.device.serial))

	@property
	def device_string(self):
		return "%s (%s)" % (self.device.model, self.dev_path)

	def collect(self):
		stats = self.parse_stats()

		return (
			self.is_awake(),
			stats.get("read_ios"),
			stats.get("read_sectors"),
			stats.get("write_ios"),
			stats.get("write_sectors"),
			self.get_bad_sectors(),
			self.get_temperature(),
		)

	def parse_stats(self):
		"""
			https://www.kernel.org/doc/Documentation/block/stat.txt

			Name            units         description
			----            -----         -----------
			read I/Os       requests      number of read I/Os processed
			read merges     requests      number of read I/Os merged with in-queue I/O
			read sectors    sectors       number of sectors read
			read ticks      milliseconds  total wait time for read requests
			write I/Os      requests      number of write I/Os processed
			write merges    requests      number of write I/Os merged with in-queue I/O
			write sectors   sectors       number of sectors written
			write ticks     milliseconds  total wait time for write requests
			in_flight       requests      number of I/Os currently in flight
			io_ticks        milliseconds  total time this block device has been active
			time_in_queue   milliseconds  total wait time for all requests
		"""
		stats_file = os.path.join(self.sys_path, "stat")

		with open(stats_file) as f:
			stats = f.read().split()

			return {
				"read_ios"      : stats[0],
				"read_merges"   : stats[1],
				"read_sectors"  : stats[2],
				"read_ticks"    : stats[3],
				"write_ios"     : stats[4],
				"write_merges"  : stats[5],
				"write_sectors" : stats[6],
				"write_ticks"   : stats[7],
				"in_flight"     : stats[8],
				"io_ticks"      : stats[9],
				"time_in_queue" : stats[10],
			}

	def is_smart_supported(self):
		"""
			We can only query SMART data if SMART is supported by the disk
			and when the disk is awake.
		"""
		return self.device.is_smart_supported() and self.device.is_awake()

	def is_awake(self):
		# If SMART is supported we can get the data from the disk
		if self.device.is_smart_supported():
			if self.device.is_awake():
				return 1
			else:
				return 0

		# Otherwise we just assume that the disk is awake
		return 1

	def get_temperature(self):
		if not self.is_smart_supported():
			return "NaN"

		return self.device.get_temperature()

	def get_bad_sectors(self):
		if not self.is_smart_supported():
			return "NaN"

		return self.device.get_bad_sectors()


class DiskPlugin(base.Plugin):
	name = "disk"
	description = "Disk Plugin"

	templates = [
		GraphTemplateDiskBadSectors,
		GraphTemplateDiskBytes,
		GraphTemplateDiskIoOps,
		GraphTemplateDiskTemperature,
	]

	block_device_patterns = [
		re.compile(r"(x?v|s)d[a-z]+"),
		re.compile(r"mmcblk[0-9]+"),
	]

	@property
	def objects(self):
		for dev in self.find_block_devices():
			try:
				yield DiskObject(self, dev)
			except OSError:
				pass

	def find_block_devices(self):
		for device in os.listdir("/sys/block"):
			# Skip invalid device names
			if not self._valid_block_device_name(device):
				continue

			yield device

	def _valid_block_device_name(self, name):
		# Check if the given name matches any of the valid patterns.
		for pattern in self.block_device_patterns:
			if pattern.match(name):
				return True

		return False
