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

import os

import rrdtool
import time

from threading import Thread

from ..i18n import _

registered_plugins = []

def find(name):
	for plugin in registered_plugins:
		if plugin._type == name:
			return plugin

def register(plugin):
	registered_plugins.append(plugin)

class Plugin(Thread):
	def __init__(self, collecty, **kwargs):
		Thread.__init__(self)
		self.collecty = collecty

		self.interval = int(kwargs.get("interval", 60))

		# Keepalive options
		self.heartbeat = 2
		self.killed = False

		self.wakeup = self.interval / self.heartbeat

		self.file = kwargs.get("file", None)
		if not self.file.startswith("/"):
			self.file = os.path.join("/var/rrd", self.file) 

		self.data = []

		self.create()
	
	def __repr__(self):
		return "<Plugin %s>" % self._type
	
	def __str__(self):
		return "Plugin %s %s" % (self._type, self.file)
	
	def run(self):
		self.collecty.debug("%s started..." % self)
		
		c = 0
		while True:
			if self.killed:
				self.update()
				self.collecty.debug("%s stoppped..." % self)
				return

			if c == 0:
				self.data.append(self.collect())
				self.collecty.debug("%s collectd: %s..." % (self, self.data[-1]))

				self.update()

				c = self.wakeup

			c = c - 1
			time.sleep(self.heartbeat)

	def shutdown(self):
		self.killed = True
	
	def time(self):
		return int(time.time()) # Should return time as int in UTC

	def create(self):
		if not os.path.exists(self.file):
			rrdtool.create(self.file, *self._rrd)
		
	def update(self):
		if self.data:
			self.collecty.debug("%s saving data..." % self)
			rrdtool.update(self.file, *self.data)
			self.data = []

	def collect(self):
		raise Exception, "Not implemented"

	def graph(self, file, interval=None):
		args = [ "--imgformat", "PNG",
				 "-w", "580", # Width of the graph
				 "-h", "240", # Height of the graph
				"--interlaced", "--slope-mode", ]

		intervals = { None   : "-3h",
					  "hour" : "-1h",
					  "day"  : "-25h",
					  "week" : "-360h" }

		args.append("--start")
		if intervals.has_key(interval):
			args.append(intervals[interval])
		else:
			args.append(interval)

		info = { "file" : self.file }
		for item in self._graph:
			try:
				args.append(item % info)
			except TypeError:
				args.append(item)

		rrdtool.graph(file, *args)

	def info(self):
		return rrdtool.info(self.file)


class PluginCpu(Plugin):
	_name = "CPU Usage Plugin"
	_type = "cpu"

	_rrd = [ "DS:user:GAUGE:120:0:100",
			 "DS:nice:GAUGE:120:0:100",
			 "DS:sys:GAUGE:120:0:100",
			 "DS:idle:GAUGE:120:0:100",
			 "DS:wait:GAUGE:120:0:100",
			 "DS:interrupt:GAUGE:120:0:100",
			 "RRA:AVERAGE:0.5:1:2160",
			 "RRA:AVERAGE:0.5:5:2016",
			 "RRA:AVERAGE:0.5:15:2880",
			 "RRA:AVERAGE:0.5:60:8760" ]

	_graph = [ "DEF:user=%(file)s:user:AVERAGE",
			   "DEF:nice=%(file)s:nice:AVERAGE",
			   "DEF:sys=%(file)s:sys:AVERAGE",
			   "DEF:idle=%(file)s:idle:AVERAGE",
			   "DEF:wait=%(file)s:wait:AVERAGE",
			   "DEF:interrupt=%(file)s:interrupt:AVERAGE",
			   "AREA:user#ff0000:%-15s" % _("User"),
			     "VDEF:usermin=user,MINIMUM",
			     "VDEF:usermax=user,MAXIMUM",
			     "VDEF:useravg=user,AVERAGE",
			     "GPRINT:usermax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:usermin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:useravg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:nice#ff3300:%-15s" % _("Nice"),
			   	 "VDEF:nicemin=nice,MINIMUM",
			     "VDEF:nicemax=nice,MAXIMUM",
			     "VDEF:niceavg=nice,AVERAGE",
			     "GPRINT:nicemax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:nicemin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:niceavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:sys#ff6600:%-15s" % _("System"),
			     "VDEF:sysmin=sys,MINIMUM",
			     "VDEF:sysmax=sys,MAXIMUM",
			     "VDEF:sysavg=sys,AVERAGE",
			     "GPRINT:sysmax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:sysmin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:sysavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:wait#ff9900:%-15s" % _("Wait"),
			     "VDEF:waitmin=wait,MINIMUM",
			     "VDEF:waitmax=wait,MAXIMUM",
			     "VDEF:waitavg=wait,AVERAGE",
			     "GPRINT:waitmax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:waitmin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:waitavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:interrupt#ffcc00:%-15s" % _("Interrupt"),
			     "VDEF:interruptmin=interrupt,MINIMUM",
			     "VDEF:interruptmax=interrupt,MAXIMUM",
			     "VDEF:interruptavg=interrupt,AVERAGE",
			     "GPRINT:interruptmax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:interruptmin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:interruptavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:idle#ffff00:%-15s" % _("Idle"),
			     "VDEF:idlemin=idle,MINIMUM",
			     "VDEF:idlemax=idle,MAXIMUM",
			     "VDEF:idleavg=idle,AVERAGE",
			     "GPRINT:idlemax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:idlemin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:idleavg:%12s\:" % _("Average") + " %6.2lf\\n", ]

	def __init__(self, collecty, **kwargs):
		Plugin.__init__(self, collecty, **kwargs)
	
	def collect(self):
		ret = "%s" % self.time()
		f = open("/proc/stat")
		for line in f.readlines():
			if not line.startswith("cpu"):
				continue
			a = line.split()
			if len(a) < 6:
				continue

			user = float(a[1])
			nice = float(a[2])
			sys = float(a[3])
			idle = float(a[4])
			wait = float(a[5])
			interrupt = float(a[6])
			sum = float(user + nice + sys + idle + wait + interrupt)

			ret += ":%s" % (user * 100 / sum)
			ret += ":%s" % (nice * 100 / sum)
			ret += ":%s" % (sys * 100 / sum)
			ret += ":%s" % (idle * 100 / sum)
			ret += ":%s" % (wait * 100 / sum)
			ret += ":%s" % (interrupt * 100 / sum)
			break

		f.close()
		return ret

register(PluginCpu)


class PluginLoad(Plugin):
	_name = "Loadaverage Plugin"
	_type = "load"

	_rrd = ["DS:load1:GAUGE:120:0:U",
			"DS:load5:GAUGE:120:0:U",
			"DS:load15:GAUGE:120:0:U",
			"RRA:AVERAGE:0.5:1:2160",
			"RRA:AVERAGE:0.5:5:2016",
			"RRA:AVERAGE:0.5:15:2880",
			"RRA:AVERAGE:0.5:60:8760" ]

	_graph = [ "DEF:load1=%(file)s:load1:AVERAGE",
			   "DEF:load5=%(file)s:load5:AVERAGE",
			   "DEF:load15=%(file)s:load15:AVERAGE",
			   "AREA:load1#ff0000:%s" % _("Load average  1m"),
			     "VDEF:load1min=load1,MINIMUM",
			     "VDEF:load1max=load1,MAXIMUM",
			     "VDEF:load1avg=load1,AVERAGE",
			     "GPRINT:load1max:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:load1min:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:load1avg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "AREA:load5#ff9900:%s" % _("Load average  5m"),
			   	 "VDEF:load5min=load5,MINIMUM",
			     "VDEF:load5max=load5,MAXIMUM",
			     "VDEF:load5avg=load5,AVERAGE",
			     "GPRINT:load5max:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:load5min:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:load5avg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "AREA:load15#ffff00:%s" % _("Load average 15m"),
			   	 "VDEF:load15min=load15,MINIMUM",
			     "VDEF:load15max=load15,MAXIMUM",
			     "VDEF:load15avg=load15,AVERAGE",
			     "GPRINT:load15max:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:load15min:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:load15avg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "LINE:load5#dd8800",
			   "LINE:load1#dd0000", ]

	def __init__(self, collecty, **kwargs):
		Plugin.__init__(self, collecty, **kwargs)

	def collect(self):
		ret = "%s" % self.time()
		for load in os.getloadavg():
			ret += ":%s" % load
		return ret

register(PluginLoad)


class PluginMem(Plugin):
	_name = "Memory Usage Plugin"
	_type = "mem"

	_rrd = ["DS:used:GAUGE:120:0:100",
			"DS:cached:GAUGE:120:0:100",
			"DS:buffered:GAUGE:120:0:100",
			"DS:free:GAUGE:120:0:100",
			"DS:swap:GAUGE:120:0:100",
			"RRA:AVERAGE:0.5:1:2160",
			"RRA:AVERAGE:0.5:5:2016",
			"RRA:AVERAGE:0.5:15:2880",
			"RRA:AVERAGE:0.5:60:8760" ]

	_graph = [ "DEF:used=%(file)s:used:AVERAGE",
			   "DEF:cached=%(file)s:cached:AVERAGE",
			   "DEF:buffered=%(file)s:buffered:AVERAGE",
			   "DEF:free=%(file)s:free:AVERAGE",
			   "DEF:swap=%(file)s:swap:AVERAGE",
			   "AREA:used#0000ee:%-15s" % _("Used memory"),
   			     "VDEF:usedmin=used,MINIMUM",
			     "VDEF:usedmax=used,MAXIMUM",
			     "VDEF:usedavg=used,AVERAGE",
			     "GPRINT:usedmax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:usedmin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:usedavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:cached#0099ee:%-15s" % _("Cached data"),
			     "VDEF:cachedmin=cached,MINIMUM",
			     "VDEF:cachedmax=cached,MAXIMUM",
			     "VDEF:cachedavg=cached,AVERAGE",
			     "GPRINT:cachedmax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:cachedmin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:cachedavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:buffered#4499ff:%-15s" % _("Buffered data"),
			   	 "VDEF:bufferedmin=buffered,MINIMUM",
			     "VDEF:bufferedmax=buffered,MAXIMUM",
			     "VDEF:bufferedavg=buffered,AVERAGE",
			     "GPRINT:bufferedmax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:bufferedmin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:bufferedavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "STACK:free#7799ff:%-15s" % _("Free memory"),
			     "VDEF:freemin=free,MINIMUM",
			     "VDEF:freemax=free,MAXIMUM",
			     "VDEF:freeavg=free,AVERAGE",
			     "GPRINT:freemax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:freemin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:freeavg:%12s\:" % _("Average") + " %6.2lf\\n",
			   "LINE3:swap#ff0000:%-15s" % _("Used Swap space"),
			     "VDEF:swapmin=swap,MINIMUM",
			     "VDEF:swapmax=swap,MAXIMUM",
			     "VDEF:swapavg=swap,AVERAGE",
			     "GPRINT:swapmax:%12s\:" % _("Maximum") + " %6.2lf" ,
			     "GPRINT:swapmin:%12s\:" % _("Minimum") + " %6.2lf",
			     "GPRINT:swapavg:%12s\:" % _("Average") + " %6.2lf\\n", ]

	def __init__(self, collecty, **kwargs):
		Plugin.__init__(self, collecty, **kwargs)

	def collect(self):
		ret = "%s" % self.time()
		f = open("/proc/meminfo")
		for line in f.readlines():
			if line.startswith("MemTotal:"):
				total = float(line.split()[1])
			if line.startswith("MemFree:"):
				free = float(line.split()[1])
			elif line.startswith("Buffers:"):
				buffered = float(line.split()[1])
			elif line.startswith("Cached:"):
				cached = float(line.split()[1])
			elif line.startswith("SwapTotal:"):
				swapt = float(line.split()[1])
			elif line.startswith("SwapFree:"):
				swapf = float(line.split()[1])

		f.close()

		ret += ":%s" % ((total - (free + buffered + cached)) * 100 / total)
		ret += ":%s" % (cached * 100 / total)
		ret += ":%s" % (buffered * 100 / total)
		ret += ":%s" % (free * 100 / total)
		ret += ":%s" % ((swapt - swapf) * 100 / swapt)

		return ret

register(PluginMem)
