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

import signal

import plugins

from constants import *
from i18n import _

import logging
log = logging.getLogger("collecty")

class Collecty(object):
	# The default interval, when all data is written to disk.
	SUBMIT_INTERVAL = 300

	def __init__(self, debug=False):
		# Enable debug logging when running in debug mode
		if debug:
			log.setLevel(logging.DEBUG)

		self.plugins = []

		# Indicates whether this process should be running or not.
		self.running = True
		self.timer = plugins.Timer(self.SUBMIT_INTERVAL, heartbeat=2)

		# Add all plugins
		for plugin in plugins.get():
			self.add_plugin(plugin)

		log.info(_("Collecty successfully initialized with %s plugins") \
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

	def run(self):
		# Register signal handlers.
		self.register_signal_handler()

		# Start all data source threads.
		for p in self.plugins:
			p.start()

		# Regularly submit all data to disk.
		while self.running:
			if self.timer.wait():
				self.submit_all()

		# Wait until all instances are finished.
		while self.plugins:
			for p in self.plugins[:]:
				if not p.isAlive():
					log.debug(_("%s is not alive anymore. Removing.") % p)
					self.plugins.remove(p)

			# Wait a bit.
			time.sleep(0.1)

		log.debug(_("No thread running. Exiting main thread."))

	def submit_all(self):
		"""
			Submit all data right now.
		"""
		log.debug(_("Submitting all data in memory"))
		for p in self.plugins:
			p._submit()

		# Schedule the next submit.
		self.timer.reset()

	def shutdown(self):
		log.debug(_("Received shutdown signal"))

		self.running = False
		if self.timer:
			self.timer.cancel()

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
			# Submit all data.
			self.submit_all()

	@property
	def graph_default_arguments(self):
		return GRAPH_DEFAULT_ARGUMENTS
