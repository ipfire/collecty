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

import os

from .. import util
from . import base

from ..colours import *
from ..constants import *
from ..i18n import _

class GraphTemplateInterfaceBase(base.GraphTemplate):
	@property
	def interface(self):
		return self.object.interface


class GraphTemplateInterfaceBits(GraphTemplateInterfaceBase):
	name = "interface-bits"

	@property
	def rrd_graph(self):
		return [
			# Headline
			"COMMENT:%s" % EMPTY_LABEL,
			"COMMENT:%s" % (COLUMN % _("Current")),
			"COMMENT:%s" % (COLUMN % _("Average")),
			"COMMENT:%s" % (COLUMN % _("Minimum")),
			"COMMENT:%s\\j" % (COLUMN % _("Maximum")),

			# Convert everything into bits.
			"CDEF:bits_rx=bytes_rx,8,*",
			"CDEF:bits_tx=bytes_tx,8,*",

			# Compute 95% lines.
			"VDEF:bits_rx_95p=bits_rx,95,PERCENT",
			"VDEF:bits_tx_95p=bits_tx,95,PERCENT",

			# Draw the received area.
			"AREA:bits_rx%s:%s" % (
				transparency(COLOUR_RX, AREA_OPACITY),
				LABEL % _("Received"),
			),
			"GPRINT:bits_rx_cur:%s" % BPS,
			"GPRINT:bits_rx_avg:%s" % BPS,
			"GPRINT:bits_rx_min:%s" % BPS,
			"GPRINT:bits_rx_max:%s\\j" % BPS,

			# Draw the transmitted area.
			"AREA:bits_tx%s:%-15s" % (
				transparency(COLOUR_TX, AREA_OPACITY),
				LABEL % _("Transmitted"),
			),
			"GPRINT:bits_tx_cur:%s" % BPS,
			"GPRINT:bits_tx_avg:%s" % BPS,
			"GPRINT:bits_tx_min:%s" % BPS,
			"GPRINT:bits_tx_max:%s\\j" % BPS,

			# Draw outlines.
			"LINE1:bits_rx%s" % COLOUR_RX,
			"LINE1:bits_tx%s" % COLOUR_TX,

			EMPTY_LINE,

			# Draw the 95% lines.
			"COMMENT:%s" % _("95th Percentile"),
			"LINE:bits_rx_95p%s:%s:dashes" % (COLOUR_RX, LABEL % _("Received")),
			"GPRINT:bits_rx_95p:%s\\r" % BPS,
			"LINE:bits_tx_95p%s:%s:dashes" % (COLOUR_TX, LABEL % _("Transmitted")),
			"GPRINT:bits_tx_95p:%s\\r" % BPS,
		]

	@property
	def graph_title(self):
		return _("Bandwidth Usage on %s") % self.interface

	@property
	def graph_vertical_label(self):
		return _("Bit/s")


class GraphTemplateInterfacePackets(GraphTemplateInterfaceBase):
	name = "interface-packets"

	@property
	def rrd_graph(self):
		return [
			# Headline
			"COMMENT:%s" % EMPTY_LABEL,
			"COMMENT:%s" % (COLUMN % _("Current")),
			"COMMENT:%s" % (COLUMN % _("Average")),
			"COMMENT:%s" % (COLUMN % _("Minimum")),
			"COMMENT:%s\\j" % (COLUMN % _("Maximum")),

			# Draw the received area.
			"AREA:packets_rx%s:%s" % (
				transparency(COLOUR_RX, AREA_OPACITY),
				LABEL % _("Received"),
			),
			"GPRINT:packets_rx_cur:%s" % PPS,
			"GPRINT:packets_rx_avg:%s" % PPS,
			"GPRINT:packets_rx_min:%s" % PPS,
			"GPRINT:packets_rx_max:%s\\j" % PPS,

			# Draw the transmitted area.
			"AREA:packets_tx%s:%s" % (
				transparency(COLOUR_TX, AREA_OPACITY),
				LABEL % _("Transmitted"),
			),
			"GPRINT:packets_tx_cur:%s" % PPS,
			"GPRINT:packets_tx_avg:%s" % PPS,
			"GPRINT:packets_tx_min:%s" % PPS,
			"GPRINT:packets_tx_max:%s\\j" % PPS,

			# Draw outlines of the areas on top.
			"LINE1:packets_rx%s" % COLOUR_RX,
			"LINE1:packets_tx%s" % COLOUR_TX,
		]

	@property
	def graph_title(self):
		return _("Transferred Packets on %s") % self.interface

	@property
	def graph_vertical_label(self):
		return _("Packets/s")


class GraphTemplateInterfaceErrors(GraphTemplateInterfaceBase):
	name = "interface-errors"

	@property
	def rrd_graph(self):
		return [
			# Headline
			"COMMENT:%s" % EMPTY_LABEL,
			"COMMENT:%s" % (COLUMN % _("Current")),
			"COMMENT:%s" % (COLUMN % _("Average")),
			"COMMENT:%s" % (COLUMN % _("Minimum")),
			"COMMENT:%s\\j" % (COLUMN % _("Maximum")),

			# Invert the transmitted packets to create upside down graph.
			"CDEF:errors_tx_inv=errors_tx,-1,*",
			"CDEF:dropped_tx_inv=dropped_tx,-1,*",

			# Draw the receive errors.
			"AREA:errors_rx%s:%-15s" % (
				transparency(COLOUR_RX, AREA_OPACITY),
				LABEL % _("Receive Errors"),
			),
			"GPRINT:errors_rx_cur:%s" % PPS,
			"GPRINT:errors_rx_avg:%s" % PPS,
			"GPRINT:errors_rx_min:%s" % PPS,
			"GPRINT:errors_rx_max:%s\\j" % PPS,
			"LINE1:errors_rx%s" % COLOUR_RX,

			# Draw the transmit errors.
			"AREA:errors_tx_inv%s:%-15s" % (
				transparency(COLOUR_TX, AREA_OPACITY),
				LABEL % _("Transmit Errors"),
			),
			"GPRINT:errors_tx_cur:%s" % PPS,
			"GPRINT:errors_tx_avg:%s" % PPS,
			"GPRINT:errors_tx_min:%s" % PPS,
			"GPRINT:errors_tx_max:%s\\j" % PPS,
			"LINE1:errors_tx_inv%s" % COLOUR_TX,

			# Draw the receive drops.
			"LINE2:dropped_rx%s:%-15s" % (
				transparency(AMBER, AREA_OPACITY),
				LABEL % _("Receive Drops"),
			),
			"GPRINT:dropped_rx_cur:%s" % PPS,
			"GPRINT:dropped_rx_avg:%s" % PPS,
			"GPRINT:dropped_rx_min:%s" % PPS,
			"GPRINT:dropped_rx_max:%s\\j" % PPS,
			"LINE1:dropped_rx#228B22",

			# Draw the transmit drops.
			"LINE2:dropped_tx%s:%-15s" % (
				transparency(TEAL, AREA_OPACITY),
				LABEL % _("Transmit Drops"),
			),
			"GPRINT:dropped_tx_cur:%s" % PPS,
			"GPRINT:dropped_tx_avg:%s" % PPS,
			"GPRINT:dropped_tx_min:%s" % PPS,
			"GPRINT:dropped_tx_max:%s\\j" % PPS,
			"LINE1:dropped_tx%s" % TEAL,

			EMPTY_LINE,

			# Draw the collisions as a line.
			"LINE2:collisions%s:%s" % (
				COLOUR_CRITICAL,
				LABEL % _("Collisions"),
			),
			"GPRINT:collisions_cur:%s" % PPS,
			"GPRINT:collisions_avg:%s" % PPS,
			"GPRINT:collisions_min:%s" % PPS,
			"GPRINT:collisions_max:%s\\j" % PPS,
		]

	@property
	def graph_title(self):
		return _("Errors/Dropped Packets on %s") % self.interface

	@property
	def graph_vertical_label(self):
		return _("Packets/s")


class InterfaceObject(base.Object):
	rrd_schema = [
		"DS:bytes_rx:DERIVE:0:U",
		"DS:bytes_tx:DERIVE:0:U",
		"DS:collisions:DERIVE:0:U",
		"DS:dropped_rx:DERIVE:0:U",
		"DS:dropped_tx:DERIVE:0:U",
		"DS:errors_rx:DERIVE:0:U",
		"DS:errors_tx:DERIVE:0:U",
		"DS:multicast:DERIVE:0:U",
		"DS:packets_rx:DERIVE:0:U",
		"DS:packets_tx:DERIVE:0:U",
	]

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.interface)

	def init(self, interface):
		self.interface = interface

	@property
	def id(self):
		return self.interface

	def collect(self):
		interface_path = os.path.join("/sys/class/net", self.interface)

		# Check if the interface exists.
		if not os.path.exists(interface_path):
			self.log.debug(_("Interface %s does not exists. Cannot collect.") \
				% self.interface)
			return

		files = (
			"rx_bytes", "tx_bytes",
			"collisions",
			"rx_dropped", "tx_dropped",
			"rx_errors", "tx_errors",
			"multicast",
			"rx_packets", "tx_packets",
		)
		ret = []

		for file in files:
			path = os.path.join(interface_path, "statistics", file)

			ret.append(
				self.read_file_integer(path),
			)

		return ret


class InterfacePlugin(base.Plugin):
	name = "interface"
	description = "Interface Statistics Plugin"

	templates = [
		GraphTemplateInterfaceBits,
		GraphTemplateInterfacePackets,
		GraphTemplateInterfaceErrors,
	]

	interval = 30

	@property
	def objects(self):
		for interface in util.get_network_interfaces():
			yield InterfaceObject(self, interface=interface)
