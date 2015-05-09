#!/usr/bin/python
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

import base

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
				if self.protocol_states.has_key(layer4_protocol):
					state = line[5]

					try:
						self.protocol_states[layer4_protocol][state] += 1
					except KeyError:
						pass


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

		return ":".join(results)


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

		return ":".join(results)


class ConntrackProtocolWithStatesObject(ConntrackObject):
	def init(self, conntrack_table, protocol):
		ConntrackObject.init(self, conntrack_table)
		self.protocol = protocol

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
		return ":".join(self.get_states())


class ConntrackPlugin(base.Plugin):
	name = "conntrack"
	description = "Conntrack Plugin"

	templates = []

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
