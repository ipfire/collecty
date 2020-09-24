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

from . import base

from ..colours import *
from ..constants import *

class GraphTemplateMemory(base.GraphTemplate):
	name = "memory"

	lower_limit = 0

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			# Headline
			"COMMENT:%s" % EMPTY_LABEL,
			"COMMENT:%s" % (COLUMN % _("Current")),
			"COMMENT:%s" % (COLUMN % _("Average")),
			"COMMENT:%s" % (COLUMN % _("Minimum")),
			"COMMENT:%s\\j" % (COLUMN % _("Maximum")),

			# Convert everything into bytes
			"CDEF:mem_total_bytes=mem_total,1024,*",
			"CDEF:mem_cached_bytes=mem_cached,1024,*",
			"CDEF:mem_buffered_bytes=mem_buffered,1024,*",
			"CDEF:mem_free_bytes=mem_free,1024,*",
			"CDEF:swap_total_bytes=swap_total,1024,*",
			"CDEF:swap_free_bytes=swap_free,1024,*",

			# Compute used memory & swap
			"CDEF:mem_used_bytes=mem_total_bytes,mem_free_bytes,-,mem_cached_bytes,-,mem_buffered_bytes,-",
			"CDEF:swap_used_bytes=swap_total_bytes,swap_free_bytes,-",

			"AREA:mem_used_bytes%s:%s" % (
				transparency(MEMORY_USED, AREA_OPACITY),
				LABEL % _("Used Memory"),
			),
			"GPRINT:mem_used_bytes_cur:%s" % LARGE_FLOAT,
			"GPRINT:mem_used_bytes_avg:%s" % LARGE_FLOAT,
			"GPRINT:mem_used_bytes_min:%s" % LARGE_FLOAT,
			"GPRINT:mem_used_bytes_max:%s\\j" % LARGE_FLOAT,

			"AREA:mem_buffered_bytes%s:%s:STACK" % (
				transparency(MEMORY_BUFFERED, AREA_OPACITY),
				LABEL % _("Buffered Data"),
			),
			"GPRINT:mem_buffered_bytes_cur:%s" % LARGE_FLOAT,
			"GPRINT:mem_buffered_bytes_avg:%s" % LARGE_FLOAT,
			"GPRINT:mem_buffered_bytes_min:%s" % LARGE_FLOAT,
			"GPRINT:mem_buffered_bytes_max:%s\\j" % LARGE_FLOAT,

			"AREA:mem_cached_bytes%s:%s:STACK" % (
				transparency(MEMORY_CACHED, AREA_OPACITY),
				LABEL % _("Cached Data")),
			"GPRINT:mem_cached_bytes_cur:%s" % LARGE_FLOAT,
			"GPRINT:mem_cached_bytes_avg:%s" % LARGE_FLOAT,
			"GPRINT:mem_cached_bytes_min:%s" % LARGE_FLOAT,
			"GPRINT:mem_cached_bytes_max:%s\\j" % LARGE_FLOAT,

			"AREA:mem_free_bytes%s:%s:STACK" % (
				transparency(MEMORY_FREE, AREA_OPACITY),
				LABEL % _("Free Memory"),
			),
			"GPRINT:mem_free_bytes_cur:%s" % LARGE_FLOAT,
			"GPRINT:mem_free_bytes_avg:%s" % LARGE_FLOAT,
			"GPRINT:mem_free_bytes_min:%s" % LARGE_FLOAT,
			"GPRINT:mem_free_bytes_max:%s\\j" % LARGE_FLOAT,

			EMPTY_LINE,

			"LINE:swap_used_bytes%s:%-15s" % (MEMORY_SWAP, LABEL % _("Used Swap Space")),
			"GPRINT:swap_used_bytes_cur:%s" % LARGE_FLOAT,
			"GPRINT:swap_used_bytes_avg:%s" % LARGE_FLOAT,
			"GPRINT:swap_used_bytes_min:%s" % LARGE_FLOAT,
			"GPRINT:swap_used_bytes_max:%s\\j" % LARGE_FLOAT,

			# Draw the outlines of the areas
			"LINE1:mem_used_bytes%s" % MEMORY_USED,
			"LINE1:mem_buffered_bytes%s::STACK" % MEMORY_BUFFERED,
			"LINE1:mem_cached_bytes%s::STACK" % MEMORY_CACHED,
		]

	@property
	def graph_title(self):
		_ = self.locale.translate

		return _("Memory Usage")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate

		return _("Bytes")


class MemoryObject(base.Object):
	rrd_schema = [
		"DS:mem_total:GAUGE:0:U",
		"DS:mem_cached:GAUGE:0:U",
		"DS:mem_buffered:GAUGE:0:U",
		"DS:mem_free:GAUGE:0:U",
		"DS:swap_total:GAUGE:0:U",
		"DS:swap_free:GAUGE:0:U",
	]

	@property
	def id(self):
		return "default"

	def collect(self):
		meminfo = self.read_proc_meminfo()

		return (
			meminfo.get("MemTotal"),
			meminfo.get("Cached"),
			meminfo.get("Buffers"),
			meminfo.get("MemFree"),
			meminfo.get("SwapTotal"),
			meminfo.get("SwapFree"),
		)


class MemoryPlugin(base.Plugin):
	name = "memory"
	description = "Memory Usage Plugin"

	templates = [GraphTemplateMemory]

	@property
	def objects(self):
		yield MemoryObject(self)
