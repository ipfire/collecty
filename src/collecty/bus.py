#!/usr/bin/python3
###############################################################################
#                                                                             #
# collecty - A system statistics collection daemon for IPFire                 #
# Copyright (C) 2015 IPFire development team                                  #
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

import dbus
import dbus.mainloop.glib
import dbus.service
import gi.repository.GLib
import gi.repository.GObject
import logging
import threading

from .i18n import _
from .constants import *

log = logging.getLogger("collecty.bus")

DOMAIN = "org.ipfire.collecty1"

class Bus(threading.Thread):
	def __init__(self, collecty):
		threading.Thread.__init__(self)
		self.daemon = True

		self.collecty = collecty

		# Initialise the main loop
		gi.repository.GObject.threads_init()
		dbus.mainloop.glib.threads_init()
		dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

		self.loop = gi.repository.GLib.MainLoop()

		# Register the GraphGenerator interface
		self.generator = GraphGenerator(self.collecty)

	def run(self):
		log.debug(_("Bus thread has started"))

		# Run the main loop
		try:
			self.loop.run()
		except KeyboardInterrupt:
			self.collecty.shutdown()

		log.debug(_("Bus thread has ended"))

	def shutdown(self):
		log.debug(_("Stopping bus thread"))

		# End the main loop
		self.loop.quit()

		# Return when this thread has finished
		return self.join()


class GraphGenerator(dbus.service.Object):
	def __init__(self, collecty):
		bus_name = dbus.service.BusName(DOMAIN, bus=dbus.SystemBus())
		dbus.service.Object.__init__(self, bus_name, "/%s" % self.__class__.__name__)

		self.collecty = collecty

	@dbus.service.method(DOMAIN, in_signature="s")
	def Backup(self, filename):
		self.collecty.backup(filename)

	@dbus.service.method(DOMAIN, in_signature="sa{sv}", out_signature="a{sv}")
	def GenerateGraph(self, template_name, kwargs):
		"""
			Returns a graph generated from the given template and object.
		"""
		graph = self.collecty.generate_graph(template_name, **kwargs)

		# Convert the graph back to normal Python format
		if graph:
			graph["image"] = dbus.ByteArray(graph["image"] or [])

		return graph

	@dbus.service.method(DOMAIN, in_signature="", out_signature="a{sv}")
	def GraphInfo(self, template_name, kwargs):
		"""
			Returns a dictionary with information about the graph.
		"""
		return self.collecty.graph_info(template_name, **kwargs)

	@dbus.service.method(DOMAIN, in_signature="sa{sv}", out_signature="a{sv}")
	def LastUpdate(self, template_name, kwargs):
		"""
			Returns a graph generated from the given template and object.
		"""
		last_update = self.collecty.last_update(template_name, **kwargs)

		# Serialise datetime as string
		if last_update:
			last_update["timestamp"] = last_update["timestamp"].isoformat()

		return last_update

	@dbus.service.method(DOMAIN, in_signature="", out_signature="as")
	def ListTemplates(self):
		"""
			Returns a list of all available templates
		"""
		return [t.name for t in self.collecty.templates]

	@dbus.service.method(DOMAIN, in_signature="", out_signature="s")
	def Version(self):
		return COLLECTY_VERSION
