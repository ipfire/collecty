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

from . import base

from ..colours import *

CONNTRACK_FILE = "/proc/net/nf_conntrack"

class ConntrackTable(object):
	_layer3_protocols = (
		"ipv6",
		"ipv4",
		"other",
	)

	_layer4_protocols = (
		"dccp",
		"icmp",
		"igmp",
		"sctp",
		"tcp",
		"udp",
		"udplite",
		"other",
	)

	_stateful_layer4_protocols = {
		"dccp" : (
			"CLOSEREQ",
			"CLOSING",
			"IGNORE",
			"INVALID",
			"NONE",
			"OPEN",
			"PARTOPEN",
			"REQUEST",
			"RESPOND",
			"TIME_WAIT",
		),
		"sctp" : (
			"CLOSED",
			"COOKIE_ECHOED",
			"COOKIE_WAIT",
			"ESTABLISHED",
			"NONE",
			"SHUTDOWN_ACK_SENT",
			"SHUTDOWN_RECD",
			"SHUTDOWN_SENT",
		),
		"tcp" : (
			"CLOSE",
			"CLOSE_WAIT",
			"ESTABLISHED",
			"FIN_WAIT",
			"LAST_ACK",
			"NONE",
			"SYN_RECV",
			"SYN_SENT",
			"SYN_SENT2",
			"TIME_WAIT",
		),
	}

	def __init__(self, filename):
		with open(filename) as f:
			self.layer3_protocols = {}
			for proto in self._layer3_protocols:
				self.layer3_protocols[proto] = 0

			self.layer4_protocols = {}
			for proto in self._layer4_protocols:
				self.layer4_protocols[proto] = 0

			self.protocol_states = {}
			for proto, states in self._stateful_layer4_protocols.items():
				self.protocol_states[proto] = dict((state, 0) for state in states)

			for line in f.readlines():
				line = line.split()

				# Layer 3 protocol
				layer3_protocol = line[0]

				try:
					self.layer3_protocols[layer3_protocol] += 1
				except KeyError:
					self.layer3_protocols["other"] += 1

				# Layer 4 protocol
				layer4_protocol = line[2]

				try:
					self.layer4_protocols[layer4_protocol] += 1
				except KeyError:
					self.layer4_protocols["other"] += 1
					layer4_protocol = "other"

				# Count connection states
				if layer4_protocol in self.protocol_states:
					state = line[5]

					try:
						self.protocol_states[layer4_protocol][state] += 1
					except KeyError:
						pass


class ConntrackLayer3ProtocolsGraphTemplate(base.GraphTemplate):
	name = "conntrack-layer3-protocols"

	_protocols = ConntrackTable._layer3_protocols

	protocol_colours = {
		"ipv6"  : COLOUR_IPV6,
		"ipv4"  : COLOUR_IPV4,
		"other" : COLOUR_IPVX,
	}

	def get_objects(self, *args):
		return [
			self.plugin.get_object("layer3-protocols"),
		]

	@property
	def protocols(self):
		# Order the protocols by standard deviation which will give us cleaner graphs
		# http://stackoverflow.com/questions/13958409/how-to-graph-rrd-stackable-data-by-standard-deviation-to-maximize-readability
		stddev = self.object.get_stddev()

		protos = {}
		for p in self._protocols:
			protos[p] = stddev.get(p)

		return sorted(protos, key=protos.get)

	@property
	def protocol_descriptions(self):
		_ = self.locale.translate

		return {
			"ipv6"  : _("IPv6"),
			"ipv4"  : _("IPv4"),
			"other" : _("Other"),
		}

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Connections by Layer 3 Protocols")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Number of open connections")

	@property
	def rrd_defs(self):
		return []

	@property
	def rrd_graph(self):
		_ = self.locale.translate
		args = []

		for proto in self.protocols:
			colour = self.protocol_colours.get(proto, COLOUR_OTHER)
			description = self.protocol_descriptions.get(proto, proto)

			args += [
				"AREA:%s%s:%-15s:STACK" % (proto, colour, description),
				"GPRINT:%s_cur:%-6s %%8.0lf" % (proto, _("Now")),
				"GPRINT:%s_avg:%-6s %%8.0lf" % (proto, _("Avg")),
				"GPRINT:%s_min:%-6s %%8.0lf" % (proto, _("Min")),
				"GPRINT:%s_max:%-6s %%8.0lf\\l" % (proto, _("Max")),
			]

		return args

	@property
	def rrd_graph_args(self):
		return [
			"--legend-direction=bottomup",
		]


class ConntrackLayer4ProtocolsGraphTemplate(ConntrackLayer3ProtocolsGraphTemplate):
	name = "conntrack-layer4-protocols"

	protocol_colours = {
		"tcp"     : COLOUR_TCP,
		"udp"     : COLOUR_UDP,
		"icmp"    : COLOUR_ICMP,
		"igmp"    : COLOUR_IGMP,
		"udplite" : COLOUR_UDPLITE,
		"sctp"    : COLOUR_SCTP,
		"dccp"    : COLOUR_DCCP,
	}

	@property
	def protocol_descriptions(self):
		_ = self.locale.translate

		return {
			"tcp"     : _("TCP"),
			"udp"     : _("UDP"),
			"icmp"    : _("ICMP"),
			"igmp"    : _("IGMP"),
			"udplite" : _("UDP Lite"),
			"sctp"    : _("SCTP"),
			"dccp"    : _("DCCP"),
			"other"   : _("Other"),
		}

	protocol_sortorder = {
		"tcp"     : 1,
		"udp"     : 2,
		"icmp"    : 3,
		"igmp"    : 4,
		"udplite" : 5,
		"sctp"    : 6,
		"dccp"    : 7,
	}

	def get_objects(self, *args):
		return [
			self.plugin.get_object("layer4-protocols"),
		]

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Connections by IP Protocols")

	@property
	def _protocols(self):
		return sorted(ConntrackTable._layer4_protocols,
			key=lambda x: self.protocol_sortorder.get(x, 99))


class ConntrackProtocolWithStatesGraphTemplate(base.GraphTemplate):
	name = "conntrack-protocol-states"

	lower_limit = 0

	states_descriptions = {
		"dccp" : {},
		"sctp" : {},
		"tcp"  : {},
	}

	states_sortorder = {
		"dccp" : {
			"CLOSEREQ"          : 0,
			"CLOSING"           : 0,
			"IGNORE"            : 0,
			"INVALID"           : 0,
			"NONE"              : 0,
			"OPEN"              : 0,
			"PARTOPEN"          : 0,
			"REQUEST"           : 0,
			"RESPOND"           : 0,
			"TIME_WAIT"         : 0,
		},
		"sctp" : {
			"CLOSED"            : 0,
			"COOKIE_ECHOED"     : 0,
			"COOKIE_WAIT"       : 0,
			"ESTABLISHED"       : 0,
			"NONE"              : 0,
			"SHUTDOWN_ACK_SENT" : 0,
			"SHUTDOWN_RECD"     : 0,
			"SHUTDOWN_SENT"     : 0,
		},
		"tcp" : {
			"CLOSE"             : 9,
			"CLOSE_WAIT"        : 8,
			"ESTABLISHED"       : 1,
			"FIN_WAIT"          : 6,
			"LAST_ACK"          : 7,
			"NONE"              : 10,
			"SYN_RECV"          : 2,
			"SYN_SENT"          : 3,
			"SYN_SENT2"         : 4,
			"TIME_WAIT"         : 5,
		},
	}

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Protocol States of all %s connections") % self.protocol.upper()

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Number of open connections")

	@property
	def protocol(self):
		return self.object.protocol

	@property
	def states(self):
		return sorted(ConntrackTable._stateful_layer4_protocols[self.protocol],
			key=lambda x: self.states_sortorder[self.protocol].get(x, 99))

	@property
	def rrd_graph(self):
		_ = self.locale.translate
		args = []

		for state in reversed(self.states):
			i = {
				"colour"      : COLOURS_PROTOCOL_STATES.get(state, BLACK),
				"description" : self.states_descriptions[self.protocol].get(state, state),
				"proto"       : self.protocol,
				"state"       : state,

				"legend_min"  : "%10s\: %%8.0lf" % _("Minimum"),
				"legend_max"  : "%10s\: %%8.0lf" % _("Maximum"),
				"legend_avg"  : "%10s\: %%8.0lf" % _("Average"),
				"legend_cur"  : "%10s\: %%8.0lf" % _("Current"),
			}

			args += self.object.make_rrd_defs(state) + [
				"AREA:%(state)s%(colour)s:%(description)-15s:STACK" % i,
				"GPRINT:%(state)s_cur:%(legend_cur)s" % i,
				"GPRINT:%(state)s_avg:%(legend_avg)s" % i,
				"GPRINT:%(state)s_min:%(legend_min)s" % i,
				"GPRINT:%(state)s_max:%(legend_max)s" % i,
			]

		return args

	@property
	def rrd_graph_args(self):
		return [
			"--legend-direction=bottomup",
		]


class ConntrackObject(base.Object):
	protocol = None

	def init(self, conntrack_table):
		self.conntrack_table = conntrack_table

	@property
	def id(self):
		return self.protocol


class ConntrackLayer3ProtocolsObject(ConntrackObject):
	protocols = ConntrackTable._layer3_protocols

	rrd_schema = [
		"DS:%s:GAUGE:0:U" % p for p in protocols
	]

	@property
	def id(self):
		return "layer3-protocols"

	def collect(self):
		results = []

		for proto in self.protocols:
			r = self.conntrack_table.layer3_protocols.get(proto, 0)
			results.append("%s" % r)

		return results


class ConntrackLayer4ProtocolsObject(ConntrackObject):
	protocols = ConntrackTable._layer4_protocols

	rrd_schema = [
		"DS:%s:GAUGE:0:U" % p for p in protocols
	]

	@property
	def id(self):
		return "layer4-protocols"

	def collect(self):
		results = []

		for proto in self.protocols:
			r = self.conntrack_table.layer4_protocols.get(proto, 0)
			results.append("%s" % r)

		return results


class ConntrackProtocolWithStatesObject(ConntrackObject):
	def init(self, conntrack_table, protocol):
		ConntrackObject.init(self, conntrack_table)
		self.protocol = protocol

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.protocol)

	@property
	def states(self):
		return ConntrackTable._stateful_layer4_protocols.get(self.protocol)

	@property
	def rrd_schema(self):
		return ["DS:%s:GAUGE:0:U" % state for state in self.states]

	def get_states(self):
		results = []

		for state in self.states:
			r = self.conntrack_table.protocol_states[self.protocol].get(state, 0)
			results.append("%s" % r)

		return results

	def collect(self):
		return self.get_states()


class ConntrackPlugin(base.Plugin):
	name = "conntrack"
	description = "Conntrack Plugin"

	templates = [
		ConntrackLayer3ProtocolsGraphTemplate,
		ConntrackLayer4ProtocolsGraphTemplate,
		ConntrackProtocolWithStatesGraphTemplate,
	]

	@property
	def objects(self):
		ct = self.get_conntrack_table()

		if ct:
			yield ConntrackLayer3ProtocolsObject(self, ct)
			yield ConntrackLayer4ProtocolsObject(self, ct)

			for protocol in ConntrackTable._stateful_layer4_protocols:
				yield ConntrackProtocolWithStatesObject(self, ct, protocol)

	def get_conntrack_table(self):
		if not os.path.exists(CONNTRACK_FILE):
			return

		return ConntrackTable(CONNTRACK_FILE)
