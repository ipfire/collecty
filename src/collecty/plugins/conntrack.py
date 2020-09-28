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

from . import base

from ..colours import *
from ..constants import *

class ConntrackGraphTemplate(base.GraphTemplate):
	name = "conntrack"

	lower_limit = 0

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			"COMMENT:%s" % EMPTY_LABEL,
			"COMMENT:%s" % (COLUMN % _("Current")),
			"COMMENT:%s" % (COLUMN % _("Average")),
			"COMMENT:%s" % (COLUMN % _("Minimum")),
			"COMMENT:%s\\j" % (COLUMN % _("Maximum")),

			"AREA:count%s:%s" % (
				transparency(PRIMARY, AREA_OPACITY),
				LABEL % _("Entries"),
			),
			"GPRINT:count_cur:%s" % INTEGER,
			"GPRINT:count_avg:%s" % INTEGER,
			"GPRINT:count_min:%s" % INTEGER,
			"GPRINT:count_max:%s" % INTEGER,
			"LINE1:count%s" % PRIMARY,

			# Draw maximum line
			"LINE:max%s:%s:dashes:skipscale" % (
				COLOUR_CRITICAL, LABEL % _("Maximum"),
			),
		]

	@property
	def graph_title(self):
		_ = self.locale.translate

		return _("Connection Tracking Table")

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate

		return _("Entries")


class ConntrackObject(base.Object):
	rrd_schema = [
		"DS:count:GAUGE:0:U",
		"DS:max:GAUGE:0:U",
	]

	@property
	def id(self):
		return "default"

	def collect(self):
		"""
			Read count and max values from /proc
		"""
		return (
			self.read_file_integer("/proc/sys/net/netfilter/nf_conntrack_count"),
			self.read_file_integer("/proc/sys/net/netfilter/nf_conntrack_max"),
		)


class ConntrackPlugin(base.Plugin):
	name = "conntrack"
	description = "Conntrack Plugin"

	templates = [
		ConntrackGraphTemplate,
	]

	@property
	def objects(self):
		yield ConntrackObject(self)
