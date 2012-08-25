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

import logging
import math
import os
import rrdtool
import threading
import time

from ..constants import *
from ..i18n import _

class Timer(object):
	def __init__(self, timeout, heartbeat=1):
		self.timeout = timeout
		self.heartbeat = heartbeat

		self.reset()

	def reset(self):
		# Save start time.
		self.start = time.time()

		# Has this timer been killed?
		self.killed = False

	@property
	def elapsed(self):
		return time.time() - self.start

	def cancel(self):
		self.killed = True

	def wait(self):
		while self.elapsed < self.timeout and not self.killed:
			time.sleep(self.heartbeat)

		return self.elapsed > self.timeout


class DataSource(threading.Thread):
	# The name of this plugin.
	name = None

	# A description for this plugin.
	description = None

	# Templates which can be used to generate a graph out of
	# the data from this data source.
	templates = []

	# The schema of the RRD database.
	rrd_schema = None

	# RRA properties.
	rra_types = ["AVERAGE", "MIN", "MAX"]
	rra_timespans = [3600, 86400, 604800, 2678400, 31622400]
	rra_rows = 2880

	# The default interval of this plugin.
	default_interval = 60

	def __init__(self, collecty, **kwargs):
		threading.Thread.__init__(self, name=self.description)
		self.daemon = True

		self.collecty = collecty

		# Check if this plugin was configured correctly.
		assert self.name, "Name of the plugin is not set: %s" % self.name
		assert self.description, "Description of the plugin is not set: %s" % self.description
		assert self.rrd_schema

		# Initialize the logger.
		self.log = logging.getLogger("collecty.plugins.%s" % self.name)
		self.log.propagate = 1

		self.data = []

		# Run some custom initialization.
		self.init(**kwargs)

		# Create the database file.
		self.create()

		# Keepalive options
		self.running = True
		self.timer = Timer(self.interval)

		self.log.info(_("Successfully initialized (%s).") % self.id)
	
	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.id)

	@property
	def id(self):
		"""
			A unique ID of the plugin instance.
		"""
		return self.name

	@property
	def interval(self):
		"""
			Returns the interval in milliseconds, when the read method
			should be called again.
		"""
		# XXX read this from the settings

		# Otherwise return the default.
		return self.default_interval

	@property
	def stepsize(self):
		return self.interval

	@property
	def file(self):
		"""
			The absolute path to the RRD file of this plugin.
		"""
		return os.path.join(DATABASE_DIR, "%s.rrd" % self.id)

	def create(self):
		"""
			Creates an empty RRD file with the desired data structures.
		"""
		# Skip if the file does already exist.
		if os.path.exists(self.file):
			return

		dirname = os.path.dirname(self.file)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

		# Create argument list.
		args = [
			"--step", "%s" % self.default_interval,
		] + self.get_rrd_schema()

		rrdtool.create(self.file, *args)

		self.log.debug(_("Created RRD file %s.") % self.file)

	def get_rrd_schema(self):
		schema = [
			"--step", "%s" % self.stepsize,
		]
		for line in self.rrd_schema:
			if line.startswith("DS:"):
				try:
					(prefix, name, type, lower_limit, upper_limit) = line.split(":")

					line = ":".join((
						prefix,
						name,
						type,
						"%s" % self.stepsize,
						lower_limit,
						upper_limit
					))
				except ValueError:
					pass

			schema.append(line)

		xff = 0.1

		cdp_length = 0
		for rra_timespan in self.rra_timespans:
			if (rra_timespan / self.stepsize) < self.rra_rows:
				rra_timespan = self.stepsize * self.rra_rows

			if cdp_length == 0:
				cdp_length = 1
			else:
				cdp_length = rra_timespan // (self.rra_rows * self.stepsize)

			cdp_number = math.ceil(rra_timespan / (cdp_length * self.stepsize))

			for rra_type in self.rra_types:
				schema.append("RRA:%s:%.10f:%d:%d" % \
					(rra_type, xff, cdp_length, cdp_number))

		return schema

	def info(self):
		return rrdtool.info(self.file)

	### Basic methods

	def init(self, **kwargs):
		"""
			Do some custom initialization stuff here.
		"""
		pass

	def read(self):
		"""
			Gathers the statistical data, this plugin collects.
		"""
		raise NotImplementedError

	def submit(self):
		"""
			Flushes the read data to disk.
		"""
		# Do nothing in case there is no data to submit.
		if not self.data:
			return

		self.log.debug(_("Submitting data to database. %d entries.") % len(self.data))
		rrdtool.update(self.file, *self.data)
		self.data = []

	def _read(self, *args, **kwargs):
		"""
			This method catches errors from the read() method and logs them.
		"""
		try:
			return self.read(*args, **kwargs)

		# Catch any exceptions, so collecty does not crash.
		except Exception, e:
			self.log.critical(_("Unhandled exception in read()!"), exc_info=True)

	def _submit(self, *args, **kwargs):
		"""
			This method catches errors from the submit() method and logs them.
		"""
		try:
			return self.submit(*args, **kwargs)

		# Catch any exceptions, so collecty does not crash.
		except Exception, e:
			self.log.critical(_("Unhandled exception in submit()!"), exc_info=True)

	def run(self):
		self.log.debug(_("Started."))

		while self.running:
			# Reset the timer.
			self.timer.reset()

			# Wait until the timer has successfully elapsed.
			if self.timer.wait():
				self.log.debug(_("Collecting..."))
				self._read()

		self._submit()
		self.log.debug(_("Stopped."))

	def shutdown(self):
		self.log.debug(_("Received shutdown signal."))
		self.running = False

		# Kill any running timers.
		if self.timer:
			self.timer.cancel()

	@property
	def now(self):
		"""
			Returns the current timestamp in the UNIX timestamp format (UTC).
		"""
		return int(time.time())


class GraphTemplate(object):
	# A unique name to identify this graph template.
	name = None

	# Instructions how to create the graph.
	rrd_graph = None

	# Extra arguments passed to rrdgraph.
	rrd_graph_args = []

	def __init__(self, ds):
		self.ds = ds

	@property
	def collecty(self):
		return self.ds.collecty

	def graph(self, file, interval=None,
			width=GRAPH_DEFAULT_WIDTH, height=GRAPH_DEFAULT_HEIGHT):
		args = [
			"--width", "%d" % width,
			"--height", "%d" % height,
		]
		args += self.collecty.graph_default_arguments
		args += self.rrd_graph_args

		intervals = {
			None   : "-3h",
			"hour" : "-1h",
			"day"  : "-25h",
			"week" : "-360h",
			"year" : "-365d",
		}

		args.append("--start")
		try:
			args.append(intervals[interval])
		except KeyError:
			args.append(interval)

		info = { "file" : self.ds.file }
		for item in self.rrd_graph:
			try:
				args.append(item % info)
			except TypeError:
				args.append(item)

		rrdtool.graph(file, *args)
