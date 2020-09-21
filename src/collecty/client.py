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

import argparse
import datetime
import dbus
import os
import platform
import sys

from .constants import *
from .i18n import _

import logging
log = logging.getLogger("collectly.client")

class CollectyClient(object):
	def __init__(self):
		self.bus = dbus.SystemBus()

		self.proxy = self.bus.get_object(BUS_DOMAIN, "/GraphGenerator")

	def backup(self, filename):
		"""
			Writes a backup of everything to file given filehandle
		"""
		self.proxy.Backup(filename)

	def backup_cli(self, ns):
		print(_("Backing up..."))

		self.backup(ns.filename)

	def last_update(self, template_name, **kwargs):
		last_update = self.proxy.LastUpdate(template_name, kwargs)

		if last_update:
			last_update["timestamp"] = datetime.datetime.strptime(last_update["timestamp"], "%Y-%m-%dT%H:%M:%S")

		return last_update

	def last_update_cli(self, ns):
		last_update = self.last_update(ns.template, object_id=ns.object)

		print(_("Last update: %s") % last_update.get("timestamp"))

		dataset = last_update.get("dataset")
		for k, v in dataset.items():
			print("%16s = %s" % (k, v))

	def list_templates(self):
		templates = self.proxy.ListTemplates()

		return ["%s" % t for t in templates]

	def list_templates_cli(self, ns):
		templates = self.list_templates()

		for t in sorted(templates):
			print(t)

	def graph_info(self, template_name, **kwargs):
		graph_info = self.proxy.GraphInfo(template_name, kwargs,
			signature="sa{sv}")

		return dict(graph_info)

	def generate_graph(self, template_name, **kwargs):
		graph = self.proxy.GenerateGraph(template_name, kwargs,
			signature="sa{sv}")

		# Convert the byte array into a byte string again
		if graph:
			graph["image"] = bytes(graph["image"])

		return graph

	def generate_graph_cli(self, ns):
		kwargs = {
			"format"    : ns.format or self._guess_format(ns.filename),
			"object_id" : ns.object,
		}

		if ns.height or ns.width:
			kwargs.update({
				"height" : ns.height or 0,
				"width"  : ns.width or 0,
			})

		if ns.interval:
			kwargs["interval"] = ns.interval

		kwargs.update({
			"locale"   : ns.locale,
			"timezone" : ns.timezone,
		})

		# Generate the graph image
		graph = self.generate_graph(ns.template, **kwargs)

		# Add some useful information
		info = self.graph_info(ns.template, **kwargs)
		if info:
			graph.update(info)

		# Write file to disk
		with open(ns.filename, "wb") as f:
			f.write(graph["image"])

		print(_("Title      : %(title)s (%(template)s - %(object_id)s)") % graph)
		print(_("Image size : %(image_width)sx%(image_height)spx") % graph)

	def _guess_format(self, filename):
		parts = filename.split(".")

		if parts:
			# The extension is the last part
			extension = parts[-1]

			# Image formats are all uppercase
			extension = extension.upper()

			if extension in SUPPORTED_IMAGE_FORMATS:
				return extension

		# Otherwise fall back to the default format
		return DEFAULT_IMAGE_FORMAT

	def version_cli(self, args):
		daemon_version = self.proxy.Version()

		print(_("collecty %s running on Python %s") % \
			(COLLECTY_VERSION, platform.python_version()))

		if not COLLECTY_VERSION == daemon_version:
			print(_("daemon %s") % daemon_version)

	def parse_cli(self, args):
		parser = argparse.ArgumentParser(prog="collecty-client")
		subparsers = parser.add_subparsers(help="sub-command help")

		# generate-graph
		parser_generate_graph = subparsers.add_parser("generate-graph",
			help=_("Generate a graph image"))
		parser_generate_graph.set_defaults(func=self.generate_graph_cli)
		parser_generate_graph.add_argument("--filename",
			help=_("filename"), required=True)
		parser_generate_graph.add_argument("--format", help=_("image format"))
		parser_generate_graph.add_argument("--interval", help=_("interval"))
		parser_generate_graph.add_argument("--object",
			help=_("Object identifier"), default="default")
		parser_generate_graph.add_argument("--template",
			help=_("The graph template identifier"), required=True)
		parser_generate_graph.add_argument("--timezone", default=os.environ.get("TZ", "UTC"),
			help=_("Generate the graph with timestamps plotted for the given timezone"))
		parser_generate_graph.add_argument("--locale", default=os.environ.get("LANG", "en_GB.utf8"),
			help=_("Generate the graph with this locale"))

		# Dimensions
		parser_generate_graph.add_argument("--height", type=int, default=0,
			help=_("Height of the generated image"))
		parser_generate_graph.add_argument("--width", type=int, default=0,
			help=_("Width of the generated image"))

		# last-update
		parser_last_update = subparsers.add_parser("last-update",
			help=_("Fetch the last dataset in the database"))
		parser_last_update.add_argument("--template",
			help=_("The graph template identifier"), required=True)
		parser_last_update.add_argument("--object",
			help=_("Object identifier"), default="default")
		parser_last_update.set_defaults(func=self.last_update_cli)

		# list-templates
		parser_list_templates = subparsers.add_parser("list-templates",
			help=_("Lists all graph templates"))
		parser_list_templates.set_defaults(func=self.list_templates_cli)

		# backup
		backup = subparsers.add_parser("backup",
			help=_("Backup all RRD data"),
		)
		backup.add_argument("filename", nargs="?")
		backup.set_defaults(func=self.backup_cli)

		# version
		parser_version = subparsers.add_parser("version", help=_("Show version"))
		parser_version.set_defaults(func=self.version_cli)

		return parser.parse_args(args)

	def run_cli(self, args=None):
		args = self.parse_cli(args or sys.argv[1:])

		return args.func(args)
