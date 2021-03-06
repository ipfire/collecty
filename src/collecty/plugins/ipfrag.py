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

from .. import util
from . import base

from ..colours import *
from ..constants import *
from ..i18n import _

class GraphTemplateIPv6Fragmentation(base.GraphTemplate):
	name = "ipv6-fragmentation"

	@property
	def rrd_graph(self):
		return [
			"CDEF:ip6_reasm_real_fails=ip6_reasm_fails,ip6_reasm_timeout,-",

			# Reassembly
			"AREA:ip6_reasm_real_fails%s:%s" % \
				(transparency(COLOUR_ERROR, AREA_OPACITY),
				LABEL % _("Failed Reassemblies"),
			),
			"GPRINT:ip6_reasm_fails_cur:%s" % INTEGER,
			"GPRINT:ip6_reasm_fails_avg:%s" % INTEGER,
			"GPRINT:ip6_reasm_fails_min:%s" % INTEGER,
			"GPRINT:ip6_reasm_fails_max:%s" % INTEGER,

			"AREA:ip6_reasm_timeout%s:%s:STACK" % \
				(transparency(COLOUR_WARN, AREA_OPACITY),
				LABEL % _("Reassembly Timeouts"),
			),
			"GPRINT:ip6_reasm_timeout_cur:%s" % INTEGER,
			"GPRINT:ip6_reasm_timeout_avg:%s" % INTEGER,
			"GPRINT:ip6_reasm_timeout_max:%s" % INTEGER,
			"GPRINT:ip6_reasm_timeout_min:%s" % INTEGER,

			"LINE2:ip6_reasm_oks%s:%-24s" % (
				BLACK,
				LABEL % _("Successful Reassemblies"),
			),
			"GPRINT:ip6_reasm_oks_cur:%s" % INTEGER,
			"GPRINT:ip6_reasm_oks_avg:%s" % INTEGER,
			"GPRINT:ip6_reasm_oks_max:%s" % INTEGER,
			"GPRINT:ip6_reasm_oks_min:%s" % INTEGER,

			EMPTY_LINE,

			# Fragmentation
			"LINE2:ip6_frags_fails%s:%s" % (
				COLOUR_ERROR,
				LABEL % _("Failed Fragmentations"),
			),
			"GPRINT:ip6_frags_fails_cur:%s" % INTEGER,
			"GPRINT:ip6_frags_fails_avg:%s" % INTEGER,
			"GPRINT:ip6_frags_fails_max:%s" % INTEGER,
			"GPRINT:ip6_frags_fails_min:%s" % INTEGER,

			"LINE2:ip6_frags_oks%s:%-24s" % (
				COLOUR_OK,
				LABEL % _("Fragmented Packets"),
			),
			"GPRINT:ip6_frags_oks_cur:%s" % INTEGER,
			"GPRINT:ip6_frags_oks_avg:%s" % INTEGER,
			"GPRINT:ip6_frags_oks_max:%s" % INTEGER,
			"GPRINT:ip6_frags_oks_min:%s" % INTEGER,

			# Headline
			"COMMENT:%s" % EMPTY_LABEL,
			"COMMENT:%s" % (COLUMN % _("Current")),
			"COMMENT:%s" % (COLUMN % _("Average")),
			"COMMENT:%s" % (COLUMN % _("Minimum")),
			"COMMENT:%s\\j" % (COLUMN % _("Maximum")),
		]

	@property
	def graph_title(self):
		if self.object.interface:
			return _("IPv6 Fragmentation on %s") % self.object.interface

		return _("IPv6 Fragmentation")

	@property
	def graph_vertical_label(self):
		return _("Packets/s")

	@property
	def rrd_graph_args(self):
		return [
			"--base", "1000",
			"--legend-direction=bottomup",
		]


class GraphTemplateIPv4Fragmentation(base.GraphTemplate):
	name = "ipv4-fragmentation"

	@property
	def rrd_graph(self):
		return [
			"CDEF:ip4_reasm_real_fails=ip4_reasm_fails,ip4_reasm_timeout,-",

			# Reassembly
			"AREA:ip4_reasm_real_fails%s:%s" % \
				(transparency(COLOUR_ERROR, AREA_OPACITY),
				LABEL % _("Failed Reassemblies"),
			),
			"GPRINT:ip4_reasm_fails_cur:%s" % INTEGER,
			"GPRINT:ip4_reasm_fails_avg:%s" % INTEGER,
			"GPRINT:ip4_reasm_fails_min:%s" % INTEGER,
			"GPRINT:ip4_reasm_fails_max:%s" % INTEGER,

			"AREA:ip4_reasm_timeout%s:%s:STACK" % \
				(transparency(COLOUR_WARN, AREA_OPACITY),
				LABEL % _("Reassembly Timeouts"),
			),
			"GPRINT:ip4_reasm_timeout_cur:%s" % INTEGER,
			"GPRINT:ip4_reasm_timeout_avg:%s" % INTEGER,
			"GPRINT:ip4_reasm_timeout_max:%s" % INTEGER,
			"GPRINT:ip4_reasm_timeout_min:%s" % INTEGER,

			"LINE2:ip4_reasm_oks%s:%-24s" % (
				BLACK,
				LABEL % _("Successful Reassemblies"),
			),
			"GPRINT:ip4_reasm_oks_cur:%s" % INTEGER,
			"GPRINT:ip4_reasm_oks_avg:%s" % INTEGER,
			"GPRINT:ip4_reasm_oks_max:%s" % INTEGER,
			"GPRINT:ip4_reasm_oks_min:%s" % INTEGER,

			EMPTY_LINE,

			# Fragmentation
			"LINE2:ip4_frags_fails%s:%s" % (
				COLOUR_ERROR,
				LABEL % _("Failed Fragmentations"),
			),
			"GPRINT:ip4_frags_fails_cur:%s" % INTEGER,
			"GPRINT:ip4_frags_fails_avg:%s" % INTEGER,
			"GPRINT:ip4_frags_fails_max:%s" % INTEGER,
			"GPRINT:ip4_frags_fails_min:%s" % INTEGER,

			"LINE2:ip4_frags_oks%s:%-24s" % (
				COLOUR_OK,
				LABEL % _("Fragmented Packets"),
			),
			"GPRINT:ip4_frags_oks_cur:%s" % INTEGER,
			"GPRINT:ip4_frags_oks_avg:%s" % INTEGER,
			"GPRINT:ip4_frags_oks_max:%s" % INTEGER,
			"GPRINT:ip4_frags_oks_min:%s" % INTEGER,

			# Headline
			"COMMENT:%s" % EMPTY_LABEL,
			"COMMENT:%s" % (COLUMN % _("Current")),
			"COMMENT:%s" % (COLUMN % _("Average")),
			"COMMENT:%s" % (COLUMN % _("Minimum")),
			"COMMENT:%s\\j" % (COLUMN % _("Maximum")),
		]

	@property
	def graph_title(self):
		if self.object.interface:
			return _("IPv4 Fragmentation on %s") % self.object.interface

		return _("IPv4 Fragmentation")

	@property
	def graph_vertical_label(self):
		return _("Packets/s")

	@property
	def rrd_graph_args(self):
		return [
			"--base", "1000",
			"--legend-direction=bottomup",
		]


class IPFragmentationObject(base.Object):
	rrd_schema = [
		"DS:ip6_frags_oks:DERIVE:0:U",
		"DS:ip6_frags_fails:DERIVE:0:U",
		"DS:ip6_frags_creates:DERIVE:0:U",
		"DS:ip6_reasm_timeout:DERIVE:0:U",
		"DS:ip6_reasm_reqds:DERIVE:0:U",
		"DS:ip6_reasm_oks:DERIVE:0:U",
		"DS:ip6_reasm_fails:DERIVE:0:U",
		"DS:ip4_frags_oks:DERIVE:0:U",
		"DS:ip4_frags_fails:DERIVE:0:U",
		"DS:ip4_frags_creates:DERIVE:0:U",
		"DS:ip4_reasm_timeout:DERIVE:0:U",
		"DS:ip4_reasm_reqds:DERIVE:0:U",
		"DS:ip4_reasm_oks:DERIVE:0:U",
		"DS:ip4_reasm_fails:DERIVE:0:U",
	]

	def __repr__(self):
		if self.interface:
			return "<%s %s>" % (self.__class__.__name__, self.interface)

		return "<%s>" % self.__class__.__name__

	def init(self, interface=None):
		self.interface = interface

	@property
	def id(self):
		return self.interface or "default"

	def collect(self):
		p = util.ProcNetSnmpParser(self.interface)

		# Description in RFC2465
		results = [
			p.get("Ip6", "FragOKs"),
			p.get("Ip6", "FragFails"),
			p.get("Ip6", "FragCreates"),
			p.get("Ip6", "ReasmTimeout"),
			p.get("Ip6", "ReasmReqds"),
			p.get("Ip6", "ReasmOKs"),
			p.get("Ip6", "ReasmFails"),
			p.get("Ip", "FragOKs"),
			p.get("Ip", "FragFails"),
			p.get("Ip", "FragCreates"),
			p.get("Ip", "ReasmTimeout"),
			p.get("Ip", "ReasmReqds"),
			p.get("Ip", "ReasmOKs"),
			p.get("Ip", "ReasmFails"),
		]

		return results


class IPFragmentationPlugin(base.Plugin):
	name = "ip-fragmentation"
	description = "IP Fragmentation Plugin"

	templates = [
		GraphTemplateIPv6Fragmentation,
		GraphTemplateIPv4Fragmentation,
	]

	@property
	def objects(self):
		# Overall statistics
		yield IPFragmentationObject(self)

		# Stats per interface
		for interface in util.get_network_interfaces():
			yield IPFragmentationObject(self, interface)
