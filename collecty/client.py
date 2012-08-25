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

import daemon

import logging
log = logging.getLogger("collectly.client")

class CollectyClient(object):
	def __init__(self, **settings):
		self.collecty = daemon.Collecty(**settings)

	@property
	def instances(self):
		return self.collecty.instances

	def get_instance_by_id(self, id):
		for instance in self.instances:
			if not instance.id == id:
				continue

			return instance

	def graph(self, id, filename, interval=None, **kwargs):
		instance = self.get_instance_by_id(id)
		assert instance, "Could not find instance: %s" % id

		instance.graph(filename, interval=interval, **kwargs)
