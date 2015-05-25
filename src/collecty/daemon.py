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

import Queue as queue
import rrdtool
import signal
import threading
import time

import bus
import plugins

from constants import *
from i18n import _

import logging
log = logging.getLogger("collecty")

class Collecty(object):
	# The default interval, when all data is written to disk.
	SUBMIT_INTERVAL = 300

	HEARTBEAT = 5

	def __init__(self, debug=False):
		self.debug = debug

		# Enable debug logging when running in debug mode
		if self.debug:
			log.setLevel(logging.DEBUG)

		self.plugins = []

		# Indicates whether this process should be running or not.
		self.running = True

		# The write queue holds all collected pieces of data which
		# will be written to disk later.
		self.write_queue = WriteQueue(self, self.SUBMIT_INTERVAL)

		# Create a thread that connects to dbus and processes requests we
		# get from there.
		self.bus = bus.Bus(self)

		# Add all plugins
		for plugin in plugins.get():
			self.add_plugin(plugin)

		log.debug(_("Collecty successfully initialized with %s plugins") \
			% len(self.plugins))

	def add_plugin(self, plugin_class):
		# Try initialising a new plugin. If that fails, we will log the
		# error and try to go on.
		try:
			plugin = plugin_class(self)
		except:
			log.critical(_("Plugin %s could not be initialised") % plugin_class, exc_info=True)
			return

		self.plugins.append(plugin)

	@property
	def templates(self):
		for plugin in self.plugins:
			for template in plugin.templates:
				yield template

	def run(self):
		# Register signal handlers.
		self.register_signal_handler()

		# Start the bus
		self.bus.start()

		# Start all data source threads.
		for p in self.plugins:
			p.start()

		# Run the write queue thread
		self.write_queue.start()

		# Regularly submit all data to disk.
		while self.running:
			try:
				time.sleep(self.HEARTBEAT)
			except KeyboardInterrupt:
				self.shutdown()
				break

		# Wait until all plugins are finished.
		for p in self.plugins:
			p.join()

		# Stop the bus thread
		self.bus.shutdown()

		# Write all collected data to disk before ending the main thread
		self.write_queue.shutdown()

		log.debug(_("Main thread exited"))

	def shutdown(self):
		if not self.running:
			return

		log.info(_("Received shutdown signal"))
		self.running = False

		# Propagating shutdown to all threads.
		for p in self.plugins:
			p.shutdown()

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


class WriteQueue(threading.Thread):
	def __init__(self, collecty, submit_interval):
		threading.Thread.__init__(self)
		self.daemon = True

		self.collecty = collecty

		self.log = logging.getLogger("collecty.queue")
		self.log.propagate = 1

		self.timer = plugins.Timer(submit_interval)
		self._queue = queue.PriorityQueue()

		self.log.debug(_("Initialised write queue"))

	def run(self):
		self.log.debug(_("Write queue process started"))
		self.running = True

		while self.running:
			# Reset the timer.
			self.timer.reset()

			# Wait until the timer has successfully elapsed.
			if self.timer.wait():
				self.commit()

		self.commit()
		self.log.debug(_("Write queue process stopped"))

	def shutdown(self):
		self.running = False
		self.timer.cancel()

		# Wait until all data has been written.
		self.join()

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
		for filename, results in results.items():
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


class QueueObject(object):
	def __init__(self, file, time, data):
		self.file = file
		self.time = time
		self.data = data

	def __str__(self):
		return "%s:%s" % (self.time.strftime("%s"), self.data)

	def __cmp__(self, other):
		return cmp(self.time, other.time)
