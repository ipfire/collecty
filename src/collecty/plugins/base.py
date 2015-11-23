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
import logging
import math
import os
import rrdtool
import tempfile
import threading
import time
import unicodedata

from .. import locales
from ..constants import *
from ..i18n import _

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


class Environment(object):
	"""
		Sets the correct environment for rrdtool to create
		localised graphs and graphs in the correct timezone.
	"""
	def __init__(self, timezone, locale):
		# Build the new environment
		self.new_environment = {
			"TZ" : timezone or DEFAULT_TIMEZONE,
		}

		for k in ("LANG", "LC_ALL"):
			self.new_environment[k] = locale or DEFAULT_LOCALE

	def __enter__(self):
		# Save the current environment
		self.old_environment = {}
		for k in self.new_environment:
			self.old_environment[k] = os.environ.get(k, None)

		# Apply the new one
		os.environ.update(self.new_environment)

	def __exit__(self, type, value, traceback):
		# Roll back to the previous environment
		for k, v in self.old_environment.items():
			if v is None:
				try:
					del os.environ[k]
				except KeyError:
					pass
			else:
				os.environ[k] = v


class PluginRegistration(type):
	plugins = {}

	def __init__(plugin, name, bases, dict):
		type.__init__(plugin, name, bases, dict)

		# The main class from which is inherited is not registered
		# as a plugin.
		if name == "Plugin":
			return

		if not all((plugin.name, plugin.description)):
			raise RuntimeError(_("Plugin is not properly configured: %s") % plugin)

		PluginRegistration.plugins[plugin.name] = plugin


def get():
	"""
		Returns a list with all automatically registered plugins.
	"""
	return PluginRegistration.plugins.values()

class Plugin(object, metaclass=PluginRegistration):
	# The name of this plugin.
	name = None

	# A description for this plugin.
	description = None

	# Templates which can be used to generate a graph out of
	# the data from this data source.
	templates = []

	# The default interval for all plugins
	interval = 60

	def __init__(self, collecty, **kwargs):
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

				result = self._format_result(result)
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
		delay = time.time() - time_start

		# Log some warning when a collect method takes too long to return some data
		if delay >= 60:
			self.log.warning(_("A worker thread was stalled for %.4fs") % delay)

	@staticmethod
	def _format_result(result):
		if not isinstance(result, tuple) and not isinstance(result, list):
			return result

		# Replace all Nones by NaN
		s = []

		for e in result:
			if e is None:
				e = "NaN"

			# Format as string
			e = "%s" % e

			s.append(e)

		return ":".join(s)

	def get_object(self, id):
		for object in self.objects:
			if not object.id == id:
				continue

			return object

	def get_template(self, template_name, object_id, locale=None, timezone=None):
		for template in self.templates:
			if not template.name == template_name:
				continue

			return template(self, object_id, locale=locale, timezone=timezone)

	def generate_graph(self, template_name, object_id="default",
			timezone=None, locale=None, **kwargs):
		template = self.get_template(template_name, object_id=object_id,
			timezone=timezone, locale=locale)
		if not template:
			raise RuntimeError("Could not find template %s" % template_name)

		time_start = time.time()

		graph = template.generate_graph(**kwargs)

		duration = time.time() - time_start
		self.log.debug(_("Generated graph %s in %.1fms") \
			% (template, duration * 1000))

		return graph

	def graph_info(self, template_name, object_id="default",
			timezone=None, locale=None, **kwargs):
		template = self.get_template(template_name, object_id=object_id,
			timezone=timezone, locale=locale)
		if not template:
			raise RuntimeError("Could not find template %s" % template_name)

		return template.graph_info()

	def last_update(self, object_id="default"):
		object = self.get_object(object_id)
		if not object:
			raise RuntimeError("Could not find object %s" % object_id)

		return object.last_update()


class Object(object):
	# The schema of the RRD database.
	rrd_schema = None

	# RRA properties.
	rra_types     = ("AVERAGE", "MIN", "MAX")
	rra_timespans = (
		("1m", "10d"),
		("1h", "18M"),
		("1d",  "5y"),
	)

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
		filename = self._normalise_filename("%s.rrd" % self.id)

		return os.path.join(DATABASE_DIR, self.plugin.path, filename)

	@staticmethod
	def _normalise_filename(filename):
		# Convert the filename into ASCII characters only
		filename = unicodedata.normalize("NFKC", filename)

		# Replace any spaces by dashes
		filename = filename.replace(" ", "-")

		return filename

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

	def last_update(self):
		"""
			Returns a dictionary with the timestamp and
			data set of the last database update.
		"""
		return {
			"dataset"   : self.last_dataset,
			"timestamp" : self.last_updated,
		}

	def _last_update(self):
		return rrdtool.lastupdate(self.file)

	@property
	def last_updated(self):
		"""
			Returns the timestamp when this database was last updated
		"""
		lu = self._last_update()

		if lu:
			return lu.get("date")

	@property
	def last_dataset(self):
		"""
			Returns the latest dataset in the database
		"""
		lu = self._last_update()

		if lu:
			return lu.get("ds")

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

		for steps, rows in self.rra_timespans:
			for type in self.rra_types:
				schema.append("RRA:%s:%s:%s:%s" % (type, xff, steps, rows))

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
		"month": "-30d",
		"week" : "-360h",
		"year" : "-365d",
	}

	# Default dimensions for this graph
	height = GRAPH_DEFAULT_HEIGHT
	width  = GRAPH_DEFAULT_WIDTH

	def __init__(self, plugin, object_id, locale=None, timezone=None):
		self.plugin = plugin

		# Save localisation parameters
		self.locale = locales.get(locale)
		self.timezone = timezone

		# Get all required RRD objects
		self.object_id = object_id

		# Get the main object
		self.object = self.get_object(self.object_id)

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

		try:
			interval = self.intervals[interval]
		except KeyError:
			interval = "end-%s" % interval

		# Add interval
		args += ["--start", interval]

		return args

	def get_object(self, *args, **kwargs):
		return self.plugin.get_object(*args, **kwargs)

	def get_object_table(self):
		return {
			"file" : self.object,
		}

	@property
	def object_table(self):
		if not hasattr(self, "_object_table"):
			self._object_table = self.get_object_table()

		return self._object_table

	def get_object_files(self):
		files = {}

		for id, obj in self.object_table.items():
			files[id] = obj.file

		return files

	def generate_graph(self, interval=None, **kwargs):
		args = self._make_command_line(interval, **kwargs)

		self.log.info(_("Generating graph %s") % self)
		self.log.debug("  args: %s" % args)

		object_files = self.get_object_files()

		for item in self.rrd_graph:
			try:
				args.append(item % object_files)
			except TypeError:
				args.append(item)

			self.log.debug("  %s" % args[-1])

		# Convert arguments to string
		args = [str(e) for e in args]

		with Environment(self.timezone, self.locale.lang):
			graph = rrdtool.graphv("-", *args)

		return {
			"image"        : graph.get("image"),
			"image_height" : graph.get("image_height"),
			"image_width"  : graph.get("image_width"),
		}

	def graph_info(self):
		"""
			Returns a dictionary with useful information
			about this graph.
		"""
		return {
			"title"        : self.graph_title,
			"object_id"    : self.object_id or "",
			"template"     : self.name,
		}
