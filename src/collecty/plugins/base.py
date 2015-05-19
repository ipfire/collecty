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

import datetime
import logging
import math
import os
import rrdtool
import tempfile
import threading
import time

from ..constants import *
from ..i18n import _

_plugins = {}

def get():
	"""
		Returns a list with all automatically registered plugins.
	"""
	return _plugins.values()

class Timer(object):
	def __init__(self, timeout, heartbeat=1):
		self.timeout = timeout
		self.heartbeat = heartbeat

		self.delay = 0

		self.reset()

	def reset(self, delay=0):
		# Save start time.
		self.start = time.time()

		self.delay = delay

		# Has this timer been killed?
		self.killed = False

	@property
	def elapsed(self):
		return time.time() - self.start - self.delay

	def cancel(self):
		self.killed = True

	def wait(self):
		while self.elapsed < self.timeout and not self.killed:
			time.sleep(self.heartbeat)

		return self.elapsed > self.timeout


class Plugin(threading.Thread):
	# The name of this plugin.
	name = None

	# A description for this plugin.
	description = None

	# Templates which can be used to generate a graph out of
	# the data from this data source.
	templates = []

	# The default interval for all plugins
	interval = 60

	# Automatically register all providers.
	class __metaclass__(type):
		def __init__(plugin, name, bases, dict):
			type.__init__(plugin, name, bases, dict)

			# The main class from which is inherited is not registered
			# as a plugin.
			if name == "Plugin":
				return

			if not all((plugin.name, plugin.description)):
				raise RuntimeError(_("Plugin is not properly configured: %s") \
					% plugin)

			_plugins[plugin.name] = plugin

	def __init__(self, collecty, **kwargs):
		threading.Thread.__init__(self, name=self.description)
		self.daemon = True

		self.collecty = collecty

		# Check if this plugin was configured correctly.
		assert self.name, "Name of the plugin is not set: %s" % self.name
		assert self.description, "Description of the plugin is not set: %s" % self.description

		# Initialize the logger.
		self.log = logging.getLogger("collecty.plugins.%s" % self.name)
		self.log.propagate = 1

		self.data = []

		# Run some custom initialization.
		self.init(**kwargs)

		# Keepalive options
		self.running = True
		self.timer = Timer(self.interval)

		self.log.debug(_("Successfully initialized %s") % self.__class__.__name__)

	@property
	def path(self):
		"""
			Returns the name of the sub directory in which all RRD files
			for this plugin should be stored in.
		"""
		return self.name

	### Basic methods

	def init(self, **kwargs):
		"""
			Do some custom initialization stuff here.
		"""
		pass

	def collect(self):
		"""
			Gathers the statistical data, this plugin collects.
		"""
		time_start = time.time()

		# Run through all objects of this plugin and call the collect method.
		for o in self.objects:
			now = datetime.datetime.utcnow()
			try:
				result = o.collect()
			except:
				self.log.warning(_("Unhandled exception in %s.collect()") % o, exc_info=True)
				continue

			if not result:
				self.log.warning(_("Received empty result: %s") % o)
				continue

			self.log.debug(_("Collected %s: %s") % (o, result))

			# Add the object to the write queue so that the data is written
			# to the databases later.
			self.collecty.write_queue.add(o, now, result)

		# Returns the time this function took to complete.
		return (time.time() - time_start)

	def run(self):
		self.log.debug(_("%s plugin has started") % self.name)

		# Initially collect everything
		self.collect()

		while self.running:
			# Reset the timer.
			self.timer.reset()

			# Wait until the timer has successfully elapsed.
			if self.timer.wait():
				delay = self.collect()
				self.timer.reset(delay)

		self.log.debug(_("%s plugin has stopped") % self.name)

	def shutdown(self):
		self.log.debug(_("Received shutdown signal."))
		self.running = False

		# Kill any running timers.
		if self.timer:
			self.timer.cancel()

	def get_object(self, id):
		for object in self.objects:
			if not object.id == id:
				continue

			return object

	def get_template(self, template_name):
		for template in self.templates:
			if not template.name == template_name:
				continue

			return template(self)

	def generate_graph(self, template_name, object_id="default", **kwargs):
		template = self.get_template(template_name)
		if not template:
			raise RuntimeError("Could not find template %s" % template_name)

		time_start = time.time()

		graph = template.generate_graph(object_id=object_id, **kwargs)

		duration = time.time() - time_start
		self.log.debug(_("Generated graph %s in %.1fms") \
			% (template, duration * 1000))

		return graph


class Object(object):
	# The schema of the RRD database.
	rrd_schema = None

	# RRA properties.
	rra_types     = ["AVERAGE", "MIN", "MAX"]
	rra_timespans = [3600, 86400, 604800, 2678400, 31622400]
	rra_rows      = 2880

	def __init__(self, plugin, *args, **kwargs):
		self.plugin = plugin

		# Indicates if this object has collected its data
		self.collected = False

		# Initialise this object
		self.init(*args, **kwargs)

		# Create the database file.
		self.create()

	def __repr__(self):
		return "<%s>" % self.__class__.__name__

	@property
	def collecty(self):
		return self.plugin.collecty

	@property
	def log(self):
		return self.plugin.log

	@property
	def id(self):
		"""
			Returns a UNIQUE identifier for this object. As this is incorporated
			into the path of RRD file, it must only contain ASCII characters.
		"""
		raise NotImplementedError

	@property
	def file(self):
		"""
			The absolute path to the RRD file of this plugin.
		"""
		return os.path.join(DATABASE_DIR, self.plugin.path, "%s.rrd" % self.id)

	### Basic methods

	def init(self, *args, **kwargs):
		"""
			Do some custom initialization stuff here.
		"""
		pass

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
		args = self.get_rrd_schema()

		rrdtool.create(self.file, *args)

		self.log.debug(_("Created RRD file %s.") % self.file)
		for arg in args:
			self.log.debug("  %s" % arg)

	def info(self):
		return rrdtool.info(self.file)

	@property
	def stepsize(self):
		return self.plugin.interval

	@property
	def heartbeat(self):
		return self.stepsize * 2

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
						"%s" % self.heartbeat,
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

	def execute(self):
		if self.collected:
			raise RuntimeError("This object has already collected its data")

		self.collected = True
		self.now = datetime.datetime.utcnow()

		# Call the collect
		result = self.collect()

	def commit(self):
		"""
			Will commit the collected data to the database.
		"""
		# Make sure that the RRD database has been created
		self.create()


class GraphTemplate(object):
	# A unique name to identify this graph template.
	name = None

	# Headline of the graph image
	graph_title = None

	# Vertical label of the graph
	graph_vertical_label = None

	# Limits
	lower_limit = None
	upper_limit = None

	# Instructions how to create the graph.
	rrd_graph = None

	# Extra arguments passed to rrdgraph.
	rrd_graph_args = []

	intervals = {
		None   : "-3h",
		"hour" : "-1h",
		"day"  : "-25h",
		"week" : "-360h",
		"year" : "-365d",
	}

	# Default dimensions for this graph
	height = GRAPH_DEFAULT_HEIGHT
	width  = GRAPH_DEFAULT_WIDTH

	def __init__(self, plugin):
		self.plugin = plugin

	def __repr__(self):
		return "<%s>" % self.__class__.__name__

	@property
	def collecty(self):
		return self.plugin.collecty

	@property
	def log(self):
		return self.plugin.log

	def _make_command_line(self, interval, format=DEFAULT_IMAGE_FORMAT,
			width=None, height=None):
		args = []

		args += GRAPH_DEFAULT_ARGUMENTS

		args += [
			"--imgformat", format,
			"--height", "%s" % (height or self.height),
			"--width", "%s" % (width or self.width),
		]

		args += self.rrd_graph_args

		# Graph title
		if self.graph_title:
			args += ["--title", self.graph_title]

		# Vertical label
		if self.graph_vertical_label:
			args += ["--vertical-label", self.graph_vertical_label]

		if self.lower_limit is not None or self.upper_limit is not None:
			# Force to honour the set limits
			args.append("--rigid")

			if self.lower_limit is not None:
				args += ["--lower-limit", self.lower_limit]

			if self.upper_limit is not None:
				args += ["--upper-limit", self.upper_limit]

		# Add interval
		args.append("--start")

		try:
			args.append(self.intervals[interval])
		except KeyError:
			args.append(str(interval))

		return args

	def get_object_table(self, object_id):
		return {
			"file" : self.plugin.get_object(object_id),
		}

	def get_object_files(self, object_id):
		files = {}

		for id, obj in self.get_object_table(object_id).items():
			files[id] = obj.file

		return files

	def generate_graph(self, object_id, interval=None, **kwargs):
		args = self._make_command_line(interval, **kwargs)

		self.log.info(_("Generating graph %s") % self)
		self.log.debug("  args: %s" % args)

		object_files = self.get_object_files(object_id)

		for item in self.rrd_graph:
			try:
				args.append(item % object_files)
			except TypeError:
				args.append(item)

		return self.write_graph(*args)

	def write_graph(self, *args):
		# Convert all arguments to string
		args = [str(e) for e in args]

		with tempfile.NamedTemporaryFile() as f:
			rrdtool.graph(f.name, *args)

			# Get back to the beginning of the file
			f.seek(0)

			# Return all the content
			return f.read()
