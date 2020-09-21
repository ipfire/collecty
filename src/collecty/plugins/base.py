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
import os
import re
import rrdtool
import time
import unicodedata

from .. import locales
from .. import util
from ..constants import *
from ..i18n import _

DEF_MATCH = r"C?DEF:([A-Za-z0-9_]+)="

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

	# Priority
	priority = 0

	def __init__(self, collecty, **kwargs):
		self.collecty = collecty

		# Check if this plugin was configured correctly.
		assert self.name, "Name of the plugin is not set: %s" % self.name
		assert self.description, "Description of the plugin is not set: %s" % self.description

		# Initialize the logger.
		self.log = logging.getLogger("collecty.plugins.%s" % self.name)

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

		# Replace all Nones by UNKNOWN
		s = []

		for e in result:
			if e is None:
				e = "U"

			s.append("%s" % e)

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

	def __lt__(self, other):
		return self.id < other.id

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

	@property
	def rrd_schema_names(self):
		ret = []

		for line in self.rrd_schema:
			(prefix, name, type, lower_limit, upper_limit) = line.split(":")
			ret.append(name)

		return ret

	def make_rrd_defs(self, prefix=None):
		defs = []

		for name in self.rrd_schema_names:
			if prefix:
				p = "%s_%s" % (prefix, name)
			else:
				p = name

			defs += [
				"DEF:%s=%s:%s:AVERAGE" % (p, self.file, name),
			]

		return defs

	def get_stddev(self, interval=None):
		args = self.make_rrd_defs()

		# Add the correct interval
		args += ["--start", util.make_interval(interval)]

		for name in self.rrd_schema_names:
			args += [
				"VDEF:%s_stddev=%s,STDEV" % (name, name),
				"PRINT:%s_stddev:%%lf" % name,
			]

		x, y, vals = rrdtool.graph("/dev/null", *args)
		return dict(zip(self.rrd_schema_names, vals))

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

		# Write everything to disk that is in the write queue
		self.collecty.write_queue.commit_file(self.file)

	# Convenience functions for plugin authors

	def read_file(self, *args, strip=True):
		"""
			Reads the content of the given file
		"""
		filename = os.path.join(*args)

		with open(filename) as f:
			value = f.read()

		# Strip any excess whitespace
		if strip:
			value = value.strip()

		return value

	def read_file_integer(self, filename):
		"""
			Reads the content from a file and returns it as an integer
		"""
		value = self.read_file(filename)

		try:
			return int(value)
		except ValueError:
			return None

	def read_proc_stat(self):
		"""
			Reads /proc/stat and returns it as a dictionary
		"""
		ret = {}

		with open("/proc/stat") as f:
			for line in f:
				# Split the key from the rest of the line
				key, line = line.split(" ", 1)

				# Remove any line breaks
				ret[key] = line.rstrip()

		return ret


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
		self.objects = self.get_objects(self.object_id)
		self.objects.sort()

	def __repr__(self):
		return "<%s>" % self.__class__.__name__

	@property
	def collecty(self):
		return self.plugin.collecty

	@property
	def log(self):
		return self.plugin.log

	@property
	def object(self):
		"""
			Shortcut to the main object
		"""
		if len(self.objects) == 1:
			return self.objects[0]

	def _make_command_line(self, interval, format=DEFAULT_IMAGE_FORMAT,
			width=None, height=None, with_title=True, thumbnail=False):
		args = [e for e in GRAPH_DEFAULT_ARGUMENTS]

		# Set the default dimensions
		default_height, default_width = GRAPH_DEFAULT_HEIGHT, GRAPH_DEFAULT_WIDTH

		# A thumbnail doesn't have a legend and other labels
		if thumbnail:
			args.append("--only-graph")

			default_height = THUMBNAIL_DEFAULT_HEIGHT
			default_width = THUMBNAIL_DEFAULT_WIDTH

		args += [
			"--imgformat", format,
			"--height", "%s" % (height or default_height),
			"--width", "%s" % (width or default_width),
		]

		args += self.rrd_graph_args

		# Graph title
		if with_title and self.graph_title:
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
		args += ["--start", util.make_interval(interval)]

		return args

	def _add_defs(self):
		use_prefix = len(self.objects) >= 2

		args = []
		for object in self.objects:
			if use_prefix:
				args += object.make_rrd_defs(object.id)
			else:
				args += object.make_rrd_defs()

		return args

	def _add_vdefs(self, args):
		ret = []

		for arg in args:
			ret.append(arg)

			# Search for all DEFs and CDEFs
			m = re.match(DEF_MATCH, "%s" % arg)
			if m:
				name = m.group(1)

				# Add the VDEFs for minimum, maximum, etc. values
				ret += [
					"VDEF:%s_cur=%s,LAST" % (name, name),
					"VDEF:%s_avg=%s,AVERAGE" % (name, name),
					"VDEF:%s_max=%s,MAXIMUM" % (name, name),
					"VDEF:%s_min=%s,MINIMUM" % (name, name),
				]

		return ret

	def get_objects(self, *args, **kwargs):
		object = self.plugin.get_object(*args, **kwargs)

		if object:
			return [object,]

		return []

	def generate_graph(self, interval=None, **kwargs):
		assert self.objects, "Cannot render graph without any objects"

		# Make sure that all collected data is in the database
		# to get a recent graph image
		for object in self.objects:
			object.commit()

		args = self._make_command_line(interval, **kwargs)

		self.log.info(_("Generating graph %s") % self)

		rrd_graph = self.rrd_graph

		# Add DEFs for all objects
		if not any((e.startswith("DEF:") for e in rrd_graph)):
			args += self._add_defs()

		args += rrd_graph
		args = self._add_vdefs(args)

		# Convert arguments to string
		args = [str(e) for e in args]

		for arg in args:
			self.log.debug("  %s" % arg)

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
