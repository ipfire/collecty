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

class Collecty(object):
	def __init__(self):
		self.bus = dbus.SystemBus()

		self.proxy = self.bus.get_object(BUS_DOMAIN, "/GraphGenerator")

	def backup(self, filename):
		"""
			Writes a backup of everything to file given filehandle
		"""
		self.proxy.Backup(filename)

	def last_update(self, template_name, **kwargs):
		last_update = self.proxy.LastUpdate(template_name, kwargs)

		if last_update:
			last_update["timestamp"] = datetime.datetime.strptime(last_update["timestamp"], "%Y-%m-%dT%H:%M:%S")

		return last_update

	def list_templates(self):
		templates = self.proxy.ListTemplates()

		return ["%s" % t for t in templates]

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

	def version(self):
		"""
			Returns the version of the daemon
		"""
		return self.proxy.Version()
