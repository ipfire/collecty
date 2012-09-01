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

import collecty.ping

import base

from ..i18n import _

PING_HOSTS = [
	"ping.ipfire.org",
]

class GraphTemplateLatency(base.GraphTemplate):
	name = "latency"

	@property
	def rrd_graph(self):
		return [
			"DEF:latency=%(file)s:latency:AVERAGE",
			"DEF:latency_loss=%(file)s:latency_loss:AVERAGE",
			"DEF:latency_stddev=%(file)s:latency_stddev:AVERAGE",

			# Compute loss in percentage.
			"CDEF:latency_ploss=latency_loss,100,*",

			# Compute standard deviation.
			"CDEF:stddev1=latency,latency_stddev,+",
			"CDEF:stddev2=latency,latency_stddev,-",

			"CDEF:l005=latency_ploss,0,5,LIMIT,UN,UNKN,INF,IF",
			"CDEF:l010=latency_ploss,5,10,LIMIT,UN,UNKN,INF,IF",
			"CDEF:l025=latency_ploss,10,25,LIMIT,UN,UNKN,INF,IF",
			"CDEF:l050=latency_ploss,25,50,LIMIT,UN,UNKN,INF,IF",
			"CDEF:l100=latency_ploss,50,100,LIMIT,UN,UNKN,INF,IF",

			"AREA:l005#ffffff:%s" % _("0-5%%"),
			"AREA:l010#000000:%s" % _("5-10%%"),
			"AREA:l025#ff0000:%s" % _("10-25%%"),
			"AREA:l050#00ff00:%s" % _("25-50%%"),
			"AREA:l100#0000ff:%s" % _("50-100%%") + "\\n",

			"LINE1:stddev1#00660088",
			"LINE1:stddev2#00660088",

			"LINE3:latency#ff0000:%s" % _("Latency"),
			"VDEF:latencymin=latency,MINIMUM",
			"VDEF:latencymax=latency,MAXIMUM",
			"VDEF:latencyavg=latency,AVERAGE",
			"GPRINT:latencymax:%12s\:" % _("Maximum") + " %6.2lf",
			"GPRINT:latencymin:%12s\:" % _("Minimum") + " %6.2lf",
			"GPRINT:latencyavg:%12s\:" % _("Average") + " %6.2lf\\n",

			"LINE1:latencyavg#000000:%s" % _("Average latency"),
		]

	@property
	def rrd_graph_args(self):
		return [
			"--title", _("Latency to %(host)s"),
			"--vertical-label", _("Milliseconds"),

			"--lower-limit", "0", "--rigid",
		]


class DataSourceLatency(base.DataSource):
	name = "latency"
	description = "Latency (ICMP ping) Data Source"

	templates = [GraphTemplateLatency,]

	rrd_schema = [
		"DS:latency:GAUGE:0:U",
		"DS:latency_loss:GAUGE:0:100",
		"DS:latency_stddev:GAUGE:0:U",
	]

	@property
	def id(self):
		return "-".join((self.name, self.host))

	@classmethod
	def autocreate(cls, collecty, **kwargs):
		ret = []
		for host in PING_HOSTS:
			ds = cls(collecty, host=host, **kwargs)
			ret.append(ds)

		return ret

	def init(self, **kwargs):
		self.host = kwargs.get("host")
		assert self.host

	@property
	def deadline(self):
		return self.interval - 10

	def read(self):
		# Send up to five ICMP echo requests.
		try:
			ping = collecty.ping.Ping(destination=self.host, timeout=20000)
			ping.run(count=5, deadline=self.deadline)
	
		except collecty.ping.PingError, e:
			self.log.warning(_("Could not run latency check for %(host)s: %(msg)s") \
				% { "host" : self.host, "msg" : e.msg })
			return

		return ":".join((
			"%.10f" % ping.avg_time,
			"%.10f" % ping.loss,
			"%.10f" % ping.stddev,
		))
