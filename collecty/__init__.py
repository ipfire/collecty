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

import ConfigParser as configparser

import plugins

class ConfigError(Exception):
	pass

class Collecty(object):
	def __init__(self):
		self.config = configparser.ConfigParser()
		self.instances = []

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

	def debug(self, message):
		print message

	def run(self):
		signal.signal(signal.SIGTERM, lambda *args: self.shutdown())

		for i in self.instances:
			i.start()

	def shutdown(self):
		for i in self.instances:
			self.debug("Stopping %s..." % i)
			i.shutdown()
