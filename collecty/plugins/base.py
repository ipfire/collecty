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

import logging
import os
import rrdtool
import threading
import time

from ..constants import *
from ..i18n import _

class Plugin(threading.Thread):
	# The name of this plugin.
	name = None

	# A description for this plugin.
	description = None

	# The schema of the RRD database.
	rrd_schema = None

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

		# Keepalive options
		self.heartbeat = 2
		self.running = True

		self.data = []

		# Create the database file.
		self.create()

		# Run some custom initialization.
		self.init()

		self.log.info(_("Successfully initialized."))
	
	def __repr__(self):
		return "<Plugin %s>" % self.name
	
	def __str__(self):
		return "Plugin %s %s" % (self.name, self.file)

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
	def file(self):
		"""
			The absolute path to the RRD file of this plugin.
		"""
		return os.path.join(DATABASE_DIR, "%s.rrd" % self.name)

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

		rrdtool.create(self.file, *self.rrd_schema)

		self.log.debug(_("Created RRD file %s.") % self.file)

	def info(self):
		return rrdtool.info(self.file)

	### Basic methods

	def init(self):
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

		counter = 0
		while self.running:
			if counter == 0:
				self.log.debug(_("Collecting..."))
				self._read()

				self.log.debug(_("Sleeping for %.4fs.") % self.interval)

				counter = self.interval / self.heartbeat

			time.sleep(self.heartbeat)
			counter -= 1

		self._submit()
		self.log.debug(_("Stopped."))

	def shutdown(self):
		self.log.debug(_("Received shutdown signal."))
		self.running = False

	@property
	def now(self):
		"""
			Returns the current timestamp in the UNIX timestamp format (UTC).
		"""
		return int(time.time())

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
