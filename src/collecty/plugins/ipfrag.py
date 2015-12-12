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

from ..constants import *
from ..i18n import _

class GraphTemplateIPv6Fragmentation(base.GraphTemplate):
	name = "ipv6-fragmentation"

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			"DEF:frags_oks=%(file)s:ip6_frags_oks:AVERAGE",
			"DEF:frags_fails=%(file)s:ip6_frags_fails:AVERAGE",
			"DEF:reasm_timeout=%(file)s:ip6_reasm_timeout:AVERAGE",
			"DEF:reasm_oks=%(file)s:ip6_reasm_oks:AVERAGE",
			"DEF:reasm_fails=%(file)s:ip6_reasm_fails:AVERAGE",

			"CDEF:reasm_real_fails=reasm_fails,reasm_timeout,-",

			"VDEF:frags_oks_cur=frags_oks,LAST",
			"VDEF:frags_oks_avg=frags_oks,AVERAGE",
			"VDEF:frags_oks_max=frags_oks,MAXIMUM",
			"VDEF:frags_oks_min=frags_oks,MINIMUM",

			"VDEF:frags_fails_cur=frags_fails,LAST",
			"VDEF:frags_fails_avg=frags_fails,AVERAGE",
			"VDEF:frags_fails_max=frags_fails,MAXIMUM",
			"VDEF:frags_fails_min=frags_fails,MINIMUM",

			"VDEF:reasm_oks_cur=reasm_oks,LAST",
			"VDEF:reasm_oks_avg=reasm_oks,AVERAGE",
			"VDEF:reasm_oks_max=reasm_oks,MAXIMUM",
			"VDEF:reasm_oks_min=reasm_oks,MINIMUM",

			"VDEF:reasm_fails_cur=reasm_real_fails,LAST",
			"VDEF:reasm_fails_avg=reasm_real_fails,AVERAGE",
			"VDEF:reasm_fails_max=reasm_real_fails,MAXIMUM",
			"VDEF:reasm_fails_min=reasm_real_fails,MINIMUM",

			"VDEF:reasm_timeout_cur=reasm_timeout,LAST",
			"VDEF:reasm_timeout_avg=reasm_timeout,AVERAGE",
			"VDEF:reasm_timeout_max=reasm_timeout,MAXIMUM",
			"VDEF:reasm_timeout_min=reasm_timeout,MINIMUM",

			# Reassembly
			"AREA:reasm_real_fails%s:%-24s" % \
				(util.lighten(COLOUR_ERROR), _("Failed Reassemblies")),
			"GPRINT:reasm_fails_cur:%s %%5.0lf%%s" % _("Now"),
			"GPRINT:reasm_fails_avg:%s %%5.0lf%%s" % _("Avg"),
			"GPRINT:reasm_fails_max:%s %%5.0lf%%s" % _("Max"),
			"GPRINT:reasm_fails_min:%s %%5.0lf%%s\\j" % _("Min"),

			"AREA:reasm_timeout%s:%-24s:STACK" % \
				(util.lighten(COLOUR_WARN), _("Reassembly Timeouts")),
			"GPRINT:reasm_timeout_cur:%s %%5.0lf%%s" % _("Now"),
			"GPRINT:reasm_timeout_avg:%s %%5.0lf%%s" % _("Avg"),
			"GPRINT:reasm_timeout_max:%s %%5.0lf%%s" % _("Max"),
			"GPRINT:reasm_timeout_min:%s %%5.0lf%%s\\j" % _("Min"),

			"LINE2:reasm_oks%s:%-24s" % (BLACK, _("Successful Reassemblies")),
			"GPRINT:reasm_oks_cur:%s %%5.0lf%%s" % _("Now"),
			"GPRINT:reasm_oks_avg:%s %%5.0lf%%s" % _("Avg"),
			"GPRINT:reasm_oks_max:%s %%5.0lf%%s" % _("Max"),
			"GPRINT:reasm_oks_min:%s %%5.0lf%%s\\j" % _("Min"),

			"COMMENT: \\n", # empty line

			# Fragmentation
			"LINE2:frags_fails%s:%-24s" % (COLOUR_ERROR, _("Failed Fragmentations")),
			"GPRINT:frags_fails_cur:%s %%5.0lf%%s" % _("Now"),
			"GPRINT:frags_fails_avg:%s %%5.0lf%%s" % _("Avg"),
			"GPRINT:frags_fails_max:%s %%5.0lf%%s" % _("Max"),
			"GPRINT:frags_fails_min:%s %%5.0lf%%s\\j" % _("Min"),

			"LINE2:frags_oks%s:%-24s" % (COLOUR_OK, _("Fragmented Packets")),
			"GPRINT:frags_oks_cur:%s %%5.0lf%%s" % _("Now"),
			"GPRINT:frags_oks_avg:%s %%5.0lf%%s" % _("Avg"),
			"GPRINT:frags_oks_max:%s %%5.0lf%%s" % _("Max"),
			"GPRINT:frags_oks_min:%s %%5.0lf%%s\\j" % _("Min"),
		]

	@property
	def graph_title(self):
		_ = self.locale.translate

		if self.object.interface:
			return _("IPv6 Fragmentation on %s") % self.object.interface

		return _("IPv6 Fragmentation")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
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
		_ = self.locale.translate

		return [
			"DEF:frags_oks=%(file)s:ip4_frags_oks:AVERAGE",
			"DEF:frags_fails=%(file)s:ip4_frags_fails:AVERAGE",
			"DEF:reasm_timeout=%(file)s:ip4_reasm_timeout:AVERAGE",
			"DEF:reasm_oks=%(file)s:ip4_reasm_oks:AVERAGE",
			"DEF:reasm_fails=%(file)s:ip4_reasm_fails:AVERAGE",

			"CDEF:reasm_real_fails=reasm_fails,reasm_timeout,-",

			"VDEF:frags_oks_cur=frags_oks,LAST",
			"VDEF:frags_oks_avg=frags_oks,AVERAGE",
			"VDEF:frags_oks_max=frags_oks,MAXIMUM",
			"VDEF:frags_oks_min=frags_oks,MINIMUM",

			"VDEF:frags_fails_cur=frags_fails,LAST",
			"VDEF:frags_fails_avg=frags_fails,AVERAGE",
			"VDEF:frags_fails_max=frags_fails,MAXIMUM",
			"VDEF:frags_fails_min=frags_fails,MINIMUM",

			"VDEF:reasm_oks_cur=reasm_oks,LAST",
			"VDEF:reasm_oks_avg=reasm_oks,AVERAGE",
			"VDEF:reasm_oks_max=reasm_oks,MAXIMUM",
			"VDEF:reasm_oks_min=reasm_oks,MINIMUM",

			"VDEF:reasm_fails_cur=reasm_real_fails,LAST",
			"VDEF:reasm_fails_avg=reasm_real_fails,AVERAGE",
			"VDEF:reasm_fails_max=reasm_real_fails,MAXIMUM",
			"VDEF:reasm_fails_min=reasm_real_fails,MINIMUM",

			"VDEF:reasm_timeout_cur=reasm_timeout,LAST",
			"VDEF:reasm_timeout_avg=reasm_timeout,AVERAGE",
			"VDEF:reasm_timeout_max=reasm_timeout,MAXIMUM",
			"VDEF:reasm_timeout_min=reasm_timeout,MINIMUM",

			# Reassembly
			"AREA:reasm_real_fails%s:%-24s" % \
				(util.lighten(COLOUR_ERROR), _("Failed Reassemblies")),
			"GPRINT:reasm_fails_cur:%s %%5.0lf%%s" % _("Now"),
			"GPRINT:reasm_fails_avg:%s %%5.0lf%%s" % _("Avg"),
			"GPRINT:reasm_fails_max:%s %%5.0lf%%s" % _("Max"),
			"GPRINT:reasm_fails_min:%s %%5.0lf%%s\\j" % _("Min"),

			"AREA:reasm_timeout%s:%-24s:STACK" % \
				(util.lighten(COLOUR_WARN), _("Reassembly Timeouts")),
			"GPRINT:reasm_timeout_cur:%s %%5.0lf%%s" % _("Now"),
			"GPRINT:reasm_timeout_avg:%s %%5.0lf%%s" % _("Avg"),
			"GPRINT:reasm_timeout_max:%s %%5.0lf%%s" % _("Max"),
			"GPRINT:reasm_timeout_min:%s %%5.0lf%%s\\j" % _("Min"),

			"LINE2:reasm_oks%s:%-24s" % (BLACK, _("Successful Reassemblies")),
			"GPRINT:reasm_oks_cur:%s %%5.0lf%%s" % _("Now"),
			"GPRINT:reasm_oks_avg:%s %%5.0lf%%s" % _("Avg"),
			"GPRINT:reasm_oks_max:%s %%5.0lf%%s" % _("Max"),
			"GPRINT:reasm_oks_min:%s %%5.0lf%%s\\j" % _("Min"),

			"COMMENT: \\n", # empty line

			# Fragmentation
			"LINE2:frags_fails%s:%-24s" % (COLOUR_ERROR, _("Failed Fragmentations")),
			"GPRINT:frags_fails_cur:%s %%5.0lf%%s" % _("Now"),
			"GPRINT:frags_fails_avg:%s %%5.0lf%%s" % _("Avg"),
			"GPRINT:frags_fails_max:%s %%5.0lf%%s" % _("Max"),
			"GPRINT:frags_fails_min:%s %%5.0lf%%s\\j" % _("Min"),

			"LINE2:frags_oks%s:%-24s" % (COLOUR_OK, _("Fragmented Packets")),
			"GPRINT:frags_oks_cur:%s %%5.0lf%%s" % _("Now"),
			"GPRINT:frags_oks_avg:%s %%5.0lf%%s" % _("Avg"),
			"GPRINT:frags_oks_max:%s %%5.0lf%%s" % _("Max"),
			"GPRINT:frags_oks_min:%s %%5.0lf%%s\\j" % _("Min"),
		]

	@property
	def graph_title(self):
		_ = self.locale.translate

		if self.object.interface:
			return _("IPv4 Fragmentation on %s") % self.object.interface

		return _("IPv4 Fragmentation")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
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
