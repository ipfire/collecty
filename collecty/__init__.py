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
	def __init__(self):
		self.config = configparser.ConfigParser()
		self.instances = []

		log.info(_("Collecty successfully initialized."))

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

		# As long as at least one thread is alive, the main process
		# is in a while loop.
		while any([i.isAlive() for i in self.instances]):
			time.sleep(0.5)

		log.debug(_("No thread running. Exiting main thread."))

	def shutdown(self):
		log.debug(_("Received shutdown signal"))

		# Propagating shutdown to all threads.
		for i in self.instances:
			i.shutdown()

	def register_signal_handler(self):
		for s in (signal.SIGTERM, signal.SIGINT):
			signal.signal(s, self.signal_handler)

	def signal_handler(self, *args, **kwargs):
		# Shutdown this application.
		self.shutdown()
