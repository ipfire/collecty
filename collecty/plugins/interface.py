#!/usr/bin/python
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

from __future__ import division

import os

import base

from ..i18n import _

SYS_CLASS_NET = "/sys/class/net"

class GraphTemplateInterfaceBytes(base.GraphTemplate):
	name = "interface-bytes"

	rrd_graph = [
		"DEF:bytes_rx=%(file)s:bytes_rx:AVERAGE",
		"DEF:bytes_tx=%(file)s:bytes_tx:AVERAGE",

		# Convert everything into bits.
		"CDEF:bits_rx=bytes_rx,8,*",
		"CDEF:bits_tx=bytes_tx,8,*",

		# Invert the transmitted bytes to create upside down graph.
		"CDEF:bits_tx_inv=bits_tx,-1,*",

		# Compute the total bandwidth.
		"CDEF:bits=bits_rx,bits_tx,+",

		# Compute 95% line.
		"VDEF:bits_95p=bits,95,PERCENT",

		# Draw the received area.
		"AREA:bits_rx#228B2277:%-15s" % _("Received"),
		"VDEF:bits_rx_min=bits_rx,MINIMUM",
		"VDEF:bits_rx_max=bits_rx,MAXIMUM",
		"VDEF:bits_rx_avg=bits_rx,AVERAGE",
		"GPRINT:bits_rx_max:%12s\: " % _("Maximum") + _("%8.2lf %sbps"),
		"GPRINT:bits_rx_min:%12s\: " % _("Minimum") + _("%8.2lf %sbps"),
		"GPRINT:bits_rx_avg:%12s\: " % _("Average") + _("%8.2lf %sbps") + "\\n",
		"LINE1:bits_rx#228B22",

		# Draw the transmitted area.
		"AREA:bits_tx_inv#B2222277:%-15s" % _("Transmitted"),
		"VDEF:bits_tx_min=bits_tx,MINIMUM",
		"VDEF:bits_tx_max=bits_tx,MAXIMUM",
		"VDEF:bits_tx_avg=bits_tx,AVERAGE",
		"GPRINT:bits_tx_max:%12s\: " % _("Maximum") + _("%8.2lf %sbps"),
		"GPRINT:bits_tx_min:%12s\: " % _("Minimum") + _("%8.2lf %sbps"),
		"GPRINT:bits_tx_avg:%12s\: " % _("Average") + _("%8.2lf %sbps") + "\\n",
		"LINE1:bits_tx_inv#B22222",

		# Draw the 95% line.
		"LINE1:bits_95p#000000:%-15s" % _("95th percentile"),
		"GPRINT:bits_95p:%s" % _("%8.2lf %sbps") + "\\n",
	]

	rrd_graph_args = [
		"--title", _("Bandwidth usage on %(interface)s"),
		"--vertical-label", _("Bit/s"),
	]


class GraphTemplateInterfacePackets(base.GraphTemplate):
	name = "interface-packets"

	rrd_graph = [
		"DEF:packets_rx=%(file)s:packets_rx:AVERAGE",
		"DEF:packets_tx=%(file)s:packets_tx:AVERAGE",

		# Invert the transmitted packets to create upside down graph.
		"CDEF:packets_tx_inv=packets_tx,-1,*",

		# Draw the received area.
		"AREA:packets_rx#228B2277:%-15s" % _("Received"),
		"VDEF:packets_rx_min=packets_rx,MINIMUM",
		"VDEF:packets_rx_max=packets_rx,MAXIMUM",
		"VDEF:packets_rx_avg=packets_rx,AVERAGE",
		"GPRINT:packets_rx_max:%12s\: " % _("Maximum") + _("%8.0lf %spps"),
		"GPRINT:packets_rx_min:%12s\: " % _("Minimum") + _("%8.0lf %spps"),
		"GPRINT:packets_rx_avg:%12s\: " % _("Average") + _("%8.2lf %spps") + "\\n",
		"LINE1:packets_rx#228B22",

		# Draw the transmitted area.
		"AREA:packets_tx_inv#B2222277:%-15s" % _("Transmitted"),
		"VDEF:packets_tx_min=packets_tx,MINIMUM",
		"VDEF:packets_tx_max=packets_tx,MAXIMUM",
		"VDEF:packets_tx_avg=packets_tx,AVERAGE",
		"GPRINT:packets_tx_max:%12s\: " % _("Maximum") + _("%8.0lf %spps"),
		"GPRINT:packets_tx_min:%12s\: " % _("Minimum") + _("%8.0lf %spps"),
		"GPRINT:packets_tx_avg:%12s\: " % _("Average") + _("%8.2lf %spps") + "\\n",
		"LINE1:packets_tx_inv#B22222",
	]

	rrd_graph_args = [
		"--title", _("Transferred packets on %(interface)s"),
		"--vertical-label", _("Packets/s"),
	]


class GraphTemplateInterfaceErrors(base.GraphTemplate):
	name = "interface-errors"

	rrd_graph = [
		"DEF:errors_rx=%(file)s:errors_rx:AVERAGE",
		"DEF:errors_tx=%(file)s:errors_tx:AVERAGE",
		"DEF:dropped_rx=%(file)s:dropped_rx:AVERAGE",
		"DEF:dropped_tx=%(file)s:dropped_tx:AVERAGE",
		"DEF:collisions=%(file)s:collisions:AVERAGE",

		# Invert the transmitted packets to create upside down graph.
		"CDEF:errors_tx_inv=errors_tx,-1,*",
		"CDEF:dropped_tx_inv=dropped_tx,-1,*",

		# Draw the receive errors.
		"AREA:errors_rx#228B2277:%-15s" % _("Receive errors"),
		"VDEF:errors_rx_min=errors_rx,MINIMUM",
		"VDEF:errors_rx_max=errors_rx,MAXIMUM",
		"VDEF:errors_rx_avg=errors_rx,AVERAGE",
		"GPRINT:errors_rx_max:%12s\: " % _("Maximum") + _("%8.0lf %spps"),
		"GPRINT:errors_rx_min:%12s\: " % _("Minimum") + _("%8.0lf %spps"),
		"GPRINT:errors_rx_avg:%12s\: " % _("Average") + _("%8.2lf %spps") + "\\n",
		"LINE1:errors_rx#228B22",

		# Draw the transmit errors.
		"AREA:errors_tx_inv#B2222277:%-15s" % _("Transmit errors"),
		"VDEF:errors_tx_min=errors_tx,MINIMUM",
		"VDEF:errors_tx_max=errors_tx,MAXIMUM",
		"VDEF:errors_tx_avg=errors_tx,AVERAGE",
		"GPRINT:errors_tx_max:%12s\: " % _("Maximum") + _("%8.0lf %spps"),
		"GPRINT:errors_tx_min:%12s\: " % _("Minimum") + _("%8.0lf %spps"),
		"GPRINT:errors_tx_avg:%12s\: " % _("Average") + _("%8.2lf %spps") + "\\n",
		"LINE1:errors_tx_inv#B22222",

		# Draw the receive drops.
		"LINE2:dropped_rx#228B22:%-15s" % _("Receive drops"),
		"VDEF:dropped_rx_min=dropped_rx,MINIMUM",
		"VDEF:dropped_rx_max=dropped_rx,MAXIMUM",
		"VDEF:dropped_rx_avg=dropped_rx,AVERAGE",
		"GPRINT:dropped_rx_max:%12s\: " % _("Maximum") + _("%8.0lf %spps"),
		"GPRINT:dropped_rx_min:%12s\: " % _("Minimum") + _("%8.0lf %spps"),
		"GPRINT:dropped_rx_avg:%12s\: " % _("Average") + _("%8.2lf %spps") + "\\n",
		"LINE1:dropped_rx#228B22",

		# Draw the transmit drops.
		"LINE2:dropped_tx#B22222:%-15s" % _("Transmit drops"),
		"VDEF:dropped_tx_min=dropped_tx,MINIMUM",
		"VDEF:dropped_tx_max=dropped_tx,MAXIMUM",
		"VDEF:dropped_tx_avg=dropped_tx,AVERAGE",
		"GPRINT:dropped_tx_max:%12s\: " % _("Maximum") + _("%8.0lf %spps"),
		"GPRINT:dropped_tx_min:%12s\: " % _("Minimum") + _("%8.0lf %spps"),
		"GPRINT:dropped_tx_avg:%12s\: " % _("Average") + _("%8.2lf %spps") + "\\n",
		"LINE1:dropped_tx#B22222",

		# Draw the collisions as a line.
		"LINE3:collisions#8B0000:%-15s" % _("Collisions") + "\\n",
	]

	rrd_graph_args = [
		"--title", _("Errors/dropped packets on %(interface)s"),
		"--vertical-label", _("Packets/s"),
	]


class DataSourceInterface(base.DataSource):
	name = "interface"
	description = "Interface Statistics Data Source"

	templates = [
		GraphTemplateInterfaceBytes,
		GraphTemplateInterfacePackets,
		GraphTemplateInterfaceErrors,
	]

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

	@classmethod
	def autocreate(cls, collecty, **kwargs):
		if not os.path.exists(SYS_CLASS_NET):
			return

		instances = []
		for interface in os.listdir(SYS_CLASS_NET):
			path = os.path.join(SYS_CLASS_NET, interface)
			if not os.path.isdir(path):
				continue

			instance = cls(collecty, interface=interface)
			instances.append(instance)

		return instances

	def init(self, **kwargs):
		self.interface = kwargs.get("interface")

	@property
	def id(self):
		return "-".join((self.name, self.interface))

	def read(self):
		files = (
			"rx_bytes", "tx_bytes",
			"collisions",
			"rx_dropped", "tx_dropped",
			"rx_errors", "tx_errors",
			"multicast",
			"rx_packets", "tx_packets",
		)
		ret = ["%s" % self.now,]

		for file in files:
			path = os.path.join(SYS_CLASS_NET, self.interface, "statistics", file)

			# Open file and read it's content.
			f = open(path)

			line = f.readline()
			line = line.strip()
			ret.append(line)

			f.close()

		self.data.append(":".join(ret))