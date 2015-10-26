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

import datetime
import multiprocessing
import os
import queue
import rrdtool
import signal
import threading
import time

from . import bus
from . import locales
from . import plugins

from .constants import *
from .i18n import _

import logging
log = logging.getLogger("collecty")

class Collecty(object):
	# The default interval, when all data is written to disk.
	SUBMIT_INTERVAL = 300

	HEARTBEAT = 1

	def __init__(self, debug=False):
		self.debug = debug

		# Reset timezone to UTC
		# rrdtool is reading that from the environment
		os.environ["TZ"] = "UTC"

		# Enable debug logging when running in debug mode
		if self.debug:
			log.setLevel(logging.DEBUG)

		self.plugins = []

		# Indicates whether this process should be running or not.
		self.running = True

		# The write queue holds all collected pieces of data which
		# will be written to disk later.
		self.write_queue = WriteQueue(self, self.SUBMIT_INTERVAL)

		# Create worker threads
		self.worker_threads = self.create_worker_threads()

		self._timer_queue = queue.PriorityQueue()
		self._worker_queue = queue.Queue()

		# Create a thread that connects to dbus and processes requests we
		# get from there.
		self.bus = bus.Bus(self)

		# Add all plugins
		for plugin in plugins.get():
			self.add_plugin(plugin)

		log.debug(_("Collecty successfully initialized with %s plugins") \
			% len(self.plugins))

		log.debug(_("Supported locales: %s") % ", ".join(locales.get_supported_locales()))

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

		# Cannot do anything if no plugins have been initialised
		if not self.plugins:
			log.critical(_("No plugins have been initialised"))
			return

		# Start the bus
		self.bus.start()

		# Initialise the timer queue
		self.initialise_timer_queue()

		# Start worker threads
		for w in self.worker_threads:
			w.start()

		# Run the write queue thread
		self.write_queue.start()

		# Regularly submit all data to disk.
		while self.running:
			try:
				# Try processing one event from the queue. If that succeeded
				# we will retry immediately.
				if self.process_timer_queue():
					continue

				# Otherwise we will sleep for a bit
				time.sleep(self.HEARTBEAT)

				# Log warnings if the worker queue is filling up
				queue_size = self._worker_queue.qsize()
				if queue_size >= 5:
					log.warning(_("Worker queue is filling up with %s events") % queue_size)

			except KeyboardInterrupt:
				self.shutdown()
				break

		# Wait until all worker threads are finished
		for w in self.worker_threads:
			w.join()

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
		for w in self.worker_threads:
			w.shutdown()

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

	def create_worker_threads(self, num=None):
		"""
			Creates a number of worker threads
		"""
		# If no number of threads is given, we will create as many as we have
		# active processor cores but never less than two.
		if num is None:
			num = max(multiprocessing.cpu_count(), 2)

		worker_threads = []

		for id in range(num):
			worker_thread = WorkerThread(self, id)
			worker_threads.append(worker_thread)

		return worker_threads

	def initialise_timer_queue(self):
		for p in self.plugins:
			timer = PluginTimer(p)

			self._timer_queue.put(timer)

	def process_timer_queue(self):
		# Take the item from the timer queue that is to be due first
		timer = self._timer_queue.get()

		try:
			# If the timer event is to be executed, we will put the plugin
			# into the worker queue and reset the timer
			if timer.is_due():
				self._worker_queue.put(timer.plugin)
				timer.reset_deadline()

				return timer
		finally:
			# Put the timer back into the timer queue.
			self._timer_queue.put(timer)


class WorkerThread(threading.Thread):
	HEARTBEAT = 2.5

	def __init__(self, collecty, id):
		threading.Thread.__init__(self)
		self.daemon = True

		self.log = logging.getLogger("collecty.worker")
		self.log.propagate = 1

		self.collecty = collecty
		self.id = id

		self.log.debug(_("Worker thread %s has been initialised") % self.id)

	@property
	def queue(self):
		"""
			The queue this thread is getting events from
		"""
		return self.collecty._worker_queue

	def run(self):
		self.log.debug(_("Worker thread %s has been started") % self.id)
		self.running = True

		while self.running:
			try:
				plugin = self.queue.get(block=True, timeout=self.HEARTBEAT)

			# If the queue has been empty we just retry
			except queue.Empty:
				continue

			# Execute the collect operation for this plugin
			plugin.collect()

		self.log.debug(_("Worker thread %s has been terminated") % self.id)

	def shutdown(self):
		self.running = False


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


class QueueObject(object):
	def __init__(self, file, time, data):
		self.file = file
		self.time = time
		self.data = data

	def __str__(self):
		return "%s:%s" % (self.time.strftime("%s"), self.data)

	def __lt__(self, other):
		return self.time < other.time


class PluginTimer(object):
	def __init__(self, plugin):
		self.plugin = plugin

		self.deadline = datetime.datetime.utcnow()

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.deadline)

	def __lt__(self, other):
		return self.deadline < other.deadline

	def reset_deadline(self):
		self.deadline = datetime.datetime.utcnow() \
			+ datetime.timedelta(seconds=self.plugin.interval)

	def is_due(self):
		return datetime.datetime.utcnow() >= self.deadline
