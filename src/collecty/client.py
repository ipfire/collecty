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

	def list_templates(self):
		templates = self.proxy.ListTemplates()

		return ["%s" % t for t in templates]

	def list_templates_cli(self, ns):
		templates = self.list_templates()

		for t in sorted(templates):
			print(t)

	def generate_graph(self, template_name, **kwargs):
		byte_array = self.proxy.GenerateGraph(template_name, kwargs,
			signature="sa{sv}")

		# Convert the byte array into a byte string again
		if byte_array:
			return bytes(byte_array)

	def generate_graph_cli(self, ns):
		kwargs = {
			"format"    : ns.format,
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

		# Write file to disk
		with open(ns.filename, "wb") as f:
			f.write(graph)

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
		parser_generate_graph.add_argument("--format",
			help=_("image format"), default=DEFAULT_IMAGE_FORMAT)
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

		# list-templates
		parser_list_templates = subparsers.add_parser("list-templates",
			help=_("Lists all graph templates"))
		parser_list_templates.set_defaults(func=self.list_templates_cli)

		# version
		parser_version = subparsers.add_parser("version", help=_("Show version"))
		parser_version.set_defaults(func=self.version_cli)

		return parser.parse_args(args)

	def run_cli(self, args=None):
		args = self.parse_cli(args or sys.argv[1:])

		return args.func(args)
