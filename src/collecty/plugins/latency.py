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

import socket

from .. import _collecty
from ..i18n import _
from . import base

from ..colours import *
from ..constants import *

PING_HOSTS = [
	# gateway is a special name that is automatically
	# resolved by myhostname to the default gateway.
	"gateway",

	# The IPFire main server
	"ping.ipfire.org",
]

class GraphTemplateLatency(base.GraphTemplate):
	name = "latency"

	lower_limit = 0

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			# Compute the biggest loss and convert into percentage
			"CDEF:ploss=loss6,loss4,MAX,100,*",

			# Compute standard deviation
			"CDEF:stddevarea6=stddev6,2,*",
			"CDEF:spacer6=latency6,stddev6,-",
			"CDEF:stddevarea4=stddev4,2,*",
			"CDEF:spacer4=latency4,stddev4,-",

			"CDEF:l005=ploss,0,5,LIMIT,UN,UNKN,INF,IF",
			"CDEF:l010=ploss,5,10,LIMIT,UN,UNKN,INF,IF",
			"CDEF:l025=ploss,10,25,LIMIT,UN,UNKN,INF,IF",
			"CDEF:l050=ploss,25,50,LIMIT,UN,UNKN,INF,IF",
			"CDEF:l099=ploss,50,99,LIMIT,UN,UNKN,INF,IF",

			# Draw average lines
			"LINE:latency6_avg%s::dashes" % (
				lighten(COLOUR_IPV6),
			),
			"LINE:latency4_avg%s::dashes" % (
				lighten(COLOUR_IPV4),
			),

			# Colour background on packet loss
			"COMMENT:%s" % _("Packet Loss"),
			"AREA:l005%s:%s" % (
				transparency(BLACK, .2), _("0-5%"),
			),
			"AREA:l010%s:%s" % (
				transparency(BLACK, .4), _("5-10%"),
			),
			"AREA:l025%s:%s" % (
				transparency(BLACK, .6), _("10-25%"),
			),
			"AREA:l050%s:%s" % (
				transparency(BLACK, .8), _("25-50%"),
			),
			"AREA:l099%s:%s\\r" % (BLACK, _("50-99%")),

			EMPTY_LINE,

			# Plot standard deviation
			"AREA:spacer4",
			"AREA:stddevarea4%s:STACK" % transparency(COLOUR_IPV4, STDDEV_OPACITY),
			"LINE2:latency4%s:%s" % (
				COLOUR_IPV4,
				LABEL % _("Latency (IPv4)"),
			),
			"GPRINT:latency4_cur:%s" % MS,
			"GPRINT:latency4_avg:%s" % MS,
			"GPRINT:latency4_min:%s" % MS,
			"GPRINT:latency4_max:%s\\j" % MS,

			"AREA:spacer6",
			"AREA:stddevarea6%s:STACK" % transparency(COLOUR_IPV6, STDDEV_OPACITY),
			"LINE2:latency6%s:%s" % (
				COLOUR_IPV6,
				LABEL % _("Latency (IPv6)"),
			),
			"GPRINT:latency6_cur:%s" % MS,
			"GPRINT:latency6_avg:%s" % MS,
			"GPRINT:latency6_min:%s" % MS,
			"GPRINT:latency6_max:%s\\j" % MS,

			# Headline
			"COMMENT:%s" % EMPTY_LABEL,
			"COMMENT:%s" % (COLUMN % _("Current")),
			"COMMENT:%s" % (COLUMN % _("Average")),
			"COMMENT:%s" % (COLUMN % _("Minimum")),
			"COMMENT:%s\\j" % (COLUMN % _("Maximum")),
		]

	@property
	def graph_title(self):
		_ = self.locale.translate

		if self.object.hostname == "gateway":
			hostname = _("Default Gateway")
		else:
			hostname = self.object.hostname

		return _("Latency to %s") % hostname

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Milliseconds")

	@property
	def rrd_graph_args(self):
		return [
			"--legend-direction=bottomup",
		]


class LatencyObject(base.Object):
	rrd_schema = [
		"DS:latency6:GAUGE:0:U",
		"DS:stddev6:GAUGE:0:U",
		"DS:loss6:GAUGE:0:100",
		"DS:latency4:GAUGE:0:U",
		"DS:stddev4:GAUGE:0:U",
		"DS:loss4:GAUGE:0:100",
	]

	def init(self, hostname):
		self.hostname = hostname

	@property
	def id(self):
		return self.hostname

	def collect(self):
		result = []

		for family in (socket.AF_INET6, socket.AF_INET):
			try:
				p = _collecty.Ping(self.hostname, family=family)
				p.ping(count=10, deadline=10)

				result += (p.average, p.stddev, p.loss)

			except _collecty.PingAddHostError as e:
				self.log.debug(_("Could not add host %(host)s for family %(family)s") \
					% { "host" : self.hostname, "family" : family })

				# No data available
				result += (None, None, None)
				continue

			except _collecty.PingNoReplyError:
				# Unknown but 100% loss
				result += (None, None, 1)
				continue

			except _collecty.PingError as e:
				self.log.warning(_("Could not run latency check for %(host)s: %(msg)s") \
					% { "host" : self.hostname, "msg" : e })

				# A hundred percent loss
				result += (None, None, 1)

		return result


class LatencyPlugin(base.Plugin):
	name = "latency"
	description = "Latency (ICMP ping) Plugin"

	templates = [GraphTemplateLatency]

	# Because this plugin has the potential to block, we give it a slightly lower priority
	priority = 10

	@property
	def objects(self):
		for hostname in PING_HOSTS:
			yield LatencyObject(self, hostname)
