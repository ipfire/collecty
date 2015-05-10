#!/usr/bin/python
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
import gobject
import threading

from constants import *
from i18n import _

import logging
log = logging.getLogger("collecty.bus")
log.propagate = 1

# Initialise the glib main loop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
dbus.mainloop.glib.threads_init()

class Bus(threading.Thread):
	def __init__(self, collecty):
		threading.Thread.__init__(self)
		self.daemon = True

		self.collecty = collecty

		# Initialise the main loop
		gobject.threads_init()
		self.loop = gobject.MainLoop()

		# Register the GraphGenerator interface
		self.generator = GraphGenerator(self.collecty)

	def run(self):
		log.debug(_("Bus thread has started"))

		# Run the main loop
		self.loop.run()

	def shutdown(self):
		log.debug(_("Stopping bus thread"))

		# End the main loop
		self.loop.quit()

		# Return when this thread has finished
		return self.join()


class GraphGenerator(dbus.service.Object):
	def __init__(self, collecty):
		bus_name = dbus.service.BusName(BUS_DOMAIN, bus=dbus.SystemBus())
		dbus.service.Object.__init__(self, bus_name, "/%s" % self.__class__.__name__)

		self.collecty = collecty

	@dbus.service.method(BUS_DOMAIN, in_signature="sa{sv}", out_signature="ay")
	def GenerateGraph(self, template_name, kwargs):
		"""
			Returns a graph generated from the given template and object.
		"""
		graph = self.collecty.generate_graph(template_name, **kwargs)

		return dbus.ByteArray(graph or [])

	@dbus.service.method(BUS_DOMAIN, in_signature="", out_signature="as")
	def ListTemplates(self):
		"""
			Returns a list of all available templates
		"""
		return [t.name for t in self.collecty.templates]
