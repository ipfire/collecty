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
import time

import ConfigParser as configparser

import plugins

from i18n import _

# Initialize logging.
import logging
log = logging.getLogger("collecty")
log.level = logging.DEBUG

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
log.handlers.append(handler)

formatter = logging.Formatter("%(asctime)s | %(name)-20s - %(levelname)-6s | %(message)s")
handler.setFormatter(formatter)

class ConfigError(Exception):
	pass

class Collecty(object):
	# The default interval, when all data is written to disk.
	SUBMIT_INTERVAL = 300

	HEARTBEAT = 2

	def __init__(self):
		self.config = configparser.ConfigParser()
		self.instances = []

		# Indicates whether this process should be running or not.
		self.running = True

		# Add all automatic plugins.
		self.add_autocreate_plugins()

		log.info(_("Collecty successfully initialized."))

	def add_autocreate_plugins(self):
		for plugin in plugins.registered_plugins:
			if not hasattr(plugin, "autocreate"):
				continue

			ret = plugin.autocreate(self)
			if not ret:
				continue

			if not type(ret) == type([]):
				ret = [ret,]

			log.debug(_("Plugin '%(name)s' registered %(number)s instance(s).") % \
				{ "name" : plugin.name, "number" : len(ret) })

			self.instances += ret

	def read_config(self, config):
		self.config.read(config)
		
		for section in self.config.sections():
			try:
				plugin = self.config.get(section, "plugin")
				plugin = plugins.find(plugin)
			except configparser.NoOptionError:
				raise ConfigError, "Syntax error in configuration: plugin option is missing."
			except:
				raise Exception, "Plugin configuration error: Maybe plugin wasn't found? %s" % plugin

			kwargs = {}
			for (key, value) in self.config.items(section):
				if key == "plugin":
					continue

				kwargs[key] = value
			kwargs["file"] = section

			i = plugin(self, **kwargs)
			self.instances.append(i)

	def run(self):
		# Register signal handlers.
		self.register_signal_handler()

		# Start all plugin instances.
		for i in self.instances:
			i.start()

		# Regularly submit all data to disk.
		counter = self.SUBMIT_INTERVAL / self.HEARTBEAT
		while self.running:
			time.sleep(self.HEARTBEAT)
			counter -= 1

			if counter == 0:
				self.submit_all()
				counter = self.SUBMIT_INTERVAL / self.HEARTBEAT

		# Wait until all instances are finished.
		while self.instances:
			for instance in self.instances[:]:
				if not instance.isAlive():
					log.debug(_("%s is not alive anymore. Removing.") % instance)
					self.instances.remove(instance)

			# Wait a bit.
			time.sleep(0.1)

		log.debug(_("No thread running. Exiting main thread."))

	def submit_all(self):
		"""
			Submit all data right now.
		"""
		for i in self.instances:
			i._submit()

	def shutdown(self):
		log.debug(_("Received shutdown signal"))

		self.running = False

		# Propagating shutdown to all threads.
		for i in self.instances:
			i.shutdown()

	def register_signal_handler(self):
		for s in (signal.SIGTERM, signal.SIGINT):
			signal.signal(s, self.signal_handler)

	def signal_handler(self, *args, **kwargs):
		# Shutdown this application.
		self.shutdown()
