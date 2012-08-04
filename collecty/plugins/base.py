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

from threading import Thread

from ..i18n import _

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

