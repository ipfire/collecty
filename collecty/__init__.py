#!/usr/bin/python

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
