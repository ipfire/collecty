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

import logging
import os
import queue
import rrdtool
import sched
import signal
import tarfile
import tempfile
import time

from . import bus
from . import plugins

from .constants import *
from .i18n import _

log = logging.getLogger("collecty")

class Collecty(object):
	# The default interval, when all data is written to disk.
	COMMIT_INTERVAL = 300

	def __init__(self, debug=False):
		self.debug = debug

		# Reset timezone to UTC
		# rrdtool is reading that from the environment
		os.environ["TZ"] = "UTC"

		# Enable debug logging when running in debug mode
		if self.debug:
			log.setLevel(logging.DEBUG)

		self.plugins = []

		# Create the scheduler
		self.scheduler = sched.scheduler()
		self._schedule_commit()

		# The write queue holds all collected pieces of data which
		# will be written to disk later.
		self.write_queue = WriteQueue(self)

		# Create a thread that connects to dbus and processes requests we
		# get from there.
		self.bus = bus.Bus(self)

		log.debug(_("Collecty successfully initialized"))

	def add_plugin(self, plugin_class):
		# Try initialising a new plugin. If that fails, we will log the
		# error and try to go on.
		try:
			plugin = plugin_class(self)
		except:
			log.critical(_("Plugin %s could not be initialised") % plugin_class, exc_info=True)
			return

		self.plugins.append(plugin)

		# Collect immediately
		self._schedule_plugin(plugin, interval=0)

	@property
	def templates(self):
		for plugin in self.plugins:
			for template in plugin.templates:
				yield template

	def _schedule_plugin(self, plugin, interval=None):
		"""
			Schedules a collection event for the given plugin
		"""
		log.debug("Scheduling plugin %s for executing in %ss" % (plugin, plugin.interval))

		self.scheduler.enter(
			plugin.interval if interval is None else interval, plugin.priority, self._collect, (plugin,),
		)

	def _schedule_commit(self):
		log.debug("Scheduling commit in %ss" % self.COMMIT_INTERVAL)

		self.scheduler.enter(
			self.COMMIT_INTERVAL, -1, self._commit,
		)

	def _collect(self, plugin, **kwargs):
		"""
			Called for each plugin when it is time to collect some data
		"""
		log.debug("Collection started for %s" % plugin)

		# Add the next collection event to the scheduler
		self._schedule_plugin(plugin)

		# Run collection
		try:
			plugin.collect()

		except Exception as e:
			log.error("Unhandled exception in %s" % plugin, exc_info=True)
			return

	def _commit(self):
		"""
			Called when all data should be committed to disk
		"""
		# Schedule the next commit
		self._schedule_commit()

		# Write everything in the queue
		self.write_queue.commit()

	def run(self):
		# Register signal handlers.
		self.register_signal_handler()

		# Start the bus
		self.bus.start()

		# Add all plugins
		for plugin in plugins.get():
			self.add_plugin(plugin)

		# Run the scheduler
		try:
			self.scheduler.run()
		except KeyboardInterrupt:
			pass

		# Clear all plugins
		self.plugins.clear()

		# Stop the bus thread
		self.bus.shutdown()

		# Write all collected data to disk before ending the main thread
		self.write_queue.commit()

		log.debug(_("Main thread exited"))

	def shutdown(self):
		log.info(_("Received shutdown signal"))

	def register_signal_handler(self):
		for s in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
			log.debug(_("Registering signal %d") % s)

		signal.signal(s, self.signal_handler)

	def signal_handler(self, sig, *args, **kwargs):
		log.info(_("Caught signal %d") % sig)

		if sig in (signal.SIGTERM, signal.SIGINT):
			# Shutdown this application.
			self.shutdown()

		elif sig == signal.SIGUSR1:
			# Commit all data.
			self.write_queue.commit()

	def get_plugin_from_template(self, template_name):
		for plugin in self.plugins:
			if not template_name in [t.name for t in plugin.templates]:
				continue

			return plugin

	def generate_graph(self, template_name, *args, **kwargs):
		plugin = self.get_plugin_from_template(template_name)
		if not plugin:
			raise RuntimeError("Could not find template %s" % template_name)

		return plugin.generate_graph(template_name, *args, **kwargs)

	def graph_info(self, template_name, *args, **kwargs):
		plugin = self.get_plugin_from_template(template_name)
		if not plugin:
			raise RuntimeError("Could not find template %s" % template_name)

		return plugin.graph_info(template_name, *args, **kwargs)

	def last_update(self, template_name, *args, **kwargs):
		plugin = self.get_plugin_from_template(template_name)
		if not plugin:
			raise RuntimeError("Could not find template %s" % template_name)

		return plugin.last_update(*args, **kwargs)

	def backup(self, filename):
		# Write all data to disk first
		self.write_queue.commit()

		log.info(_("Backing up to %s..." % filename))

		# Opening a compressed tar file with will have all files added to it
		with tarfile.open(filename, mode="w:gz") as archive:
			for path, directories, files in os.walk(DATABASE_DIR):
				for file in files:
					# Skip any non-RRD files
					if not file.endswith(".rrd"):
						continue

					# Compose the full file path
					file = os.path.join(path, file)

					log.debug(_("Adding %s to backup...") % file)

					with tempfile.NamedTemporaryFile() as t:
						rrdtool.dump(file, t.name)

						# Add the file to the archive
						archive.add(
							t.name, arcname=file[len(DATABASE_DIR):],
						)

		log.info(_("Backup finished"))


class WriteQueue(object):
	def __init__(self, collecty):
		self.collecty = collecty

		self.log = logging.getLogger("collecty.queue")

		self._queue = queue.PriorityQueue()

		self.log.debug(_("Initialised write queue"))

	def add(self, object, time, data):
		result = QueueObject(object.file, time, data)
		self._queue.put(result)

	def commit(self):
		"""
			Flushes the read data to disk.
		"""
		# There is nothing to do if the queue is empty
		if self._queue.empty():
			self.log.debug(_("No data to commit"))
			return

		time_start = time.time()

		self.log.debug(_("Submitting data to the databases..."))

		# Get all objects from the queue and group them by the RRD file
		# to commit them all at once
		results = {}
		while not self._queue.empty():
			result = self._queue.get()

			try:
				results[result.file].append(result)
			except KeyError:
				results[result.file] = [result]

		# Write the collected data to disk
		for filename, results in list(results.items()):
			self._commit_file(filename, results)

		duration = time.time() - time_start
		self.log.debug(_("Emptied write queue in %.2fs") % duration)

	def _commit_file(self, filename, results):
		self.log.debug(_("Committing %(counter)s entries to %(filename)s") \
			% { "counter" : len(results), "filename" : filename })

		for result in results:
			self.log.debug("  %s: %s" % (result.time, result.data))

		try:
			rrdtool.update(filename, *["%s" % r for r in results])

		# Catch operational errors like unreadable/unwritable RRD databases
		# or those where the format has changed. The collected data will be lost.
		except rrdtool.OperationalError as e:
			self.log.critical(_("Could not update RRD database %s: %s") \
				% (filename, e))

	def commit_file(self, filename):
		"""
			Commits all data that is in the write queue for the given
			RRD database.
		"""
		results, others = [], []

		# We will have to walk through the entire queue since we cannot
		# ready any items selectively. Everything that belongs to our
		# transaction is kept. Everything else will be put back into the
		# queue.
		while not self._queue.empty():
			result = self._queue.get()

			if result.file == filename:
				results.append(result)
			else:
				others.append(result)

		# Put back all items that did not match
		for result in others:
			self._queue.put(result)

		# Write everything else to disk
		if results:
			self._commit_file(filename, results)


class QueueObject(object):
	def __init__(self, file, time, data):
		self.file = file
		self.time = time
		self.data = data

	def __str__(self):
		return "%s:%s" % (self.time.strftime("%s"), self.data)

	def __lt__(self, other):
		return self.time < other.time
