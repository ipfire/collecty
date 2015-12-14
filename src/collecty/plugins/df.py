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

from collecty import _collecty
import os

from ..constants import *
from .. import util
from . import base

from ..i18n import _

class GraphTemplateDiskUsage(base.GraphTemplate):
	name = "disk-usage"
	lower_limit = 0

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		return [
			# Calculate the percentage of the currently used
			# space since this is helps the user very much to
			# judge
			"CDEF:percentage_used=100,used,*,used,free,+,/",
			"VDEF:percentage_used_now=percentage_used,LAST",
			"CDEF:percentage_left=100,percentage_used,-",
			"VDEF:percentage_left_now=percentage_left,LAST",

			# Area for the used space
			"AREA:used%s:%s" % (util.lighten(LIGHT_RED, .66), _("Used")),
			"GPRINT:percentage_used_now: (%6.2lf%%)",
			"GPRINT:used_cur:%12s\:" % _("Current") + " %9.2lf%s",
			"GPRINT:used_min:%12s\:" % _("Minimum") + " %9.2lf%s",
			"GPRINT:used_max:%12s\:" % _("Maximum") + " %9.2lf%s\\n",

			# Stacked area of unused space
			"AREA:free%s:%s:STACK" % (util.lighten(LIGHT_GREEN, .66), _("Free")),
			"GPRINT:percentage_left_now: (%6.2lf%%)",
			"GPRINT:free_cur:%12s\:" % _("Current") + " %9.2lf%s",
			"GPRINT:free_min:%12s\:" % _("Minimum") + " %9.2lf%s",
			"GPRINT:free_max:%12s\:" % _("Maximum") + " %9.2lf%s\\n",

			# Add contour lines for the areas
			"LINE:used%s" % LIGHT_RED,
			"LINE:free%s::STACK" % LIGHT_GREEN,
		]

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Disk Usage of %s") % self.object.mountpoint

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Bytes")


class GraphTemplateInodeUsage(base.GraphTemplate):
	name = "inode-usage"
	lower_limit = 0

	@property
	def rrd_graph(self):
		_ = self.locale.translate

		rrd_graph = [
			# Calculate the percentage of the currently used
			# inodes since this is helps the user very much to
			# judge
			"CDEF:percentage_used=100,inodes_used,*,inodes_used,inodes_free,+,/",
			"CDEF:percentage_left=100,percentage_used,-",

			# Area for the used inodes
			"AREA:inodes_used%s:%s" % (util.lighten(LIGHT_RED, .66), _("Used")),
			"GPRINT:percentage_used_now: (%6.2lf%%)",
			"GPRINT:inodes_used_cur:%12s\:" % _("Current") + " %9.2lf%s",
			"GPRINT:inodes_used_min:%12s\:" % _("Minimum") + " %9.2lf%s",
			"GPRINT:inodes_used_max:%12s\:" % _("Maximum") + " %9.2lf%s\\n",

			# Stacked area of unused inodes
			"AREA:inodes_free%s:%s:STACK" % (util.lighten(LIGHT_GREEN, .66), _("Free")),
			"GPRINT:percentage_left_now: (%6.2lf%%)",
			"GPRINT:inodes_free_cur:%12s\:" % _("Current") + " %9.2lf%s",
			"GPRINT:inodes_free_min:%12s\:" % _("Minimum") + " %9.2lf%s",
			"GPRINT:inodes_free_max:%12s\:" % _("Maximum") + " %9.2lf%s\\n",

			# Add contour lines for the areas
			"LINE:inodes_used%s" % LIGHT_RED,
			"LINE:inodes_free%s::STACK" % LIGHT_GREEN,
		]

		return rrd_graph

	rrd_graph_args = [
		"--base", "1000", # inodes
	]

	@property
	def graph_title(self):
		_ = self.locale.translate
		return _("Inode Usage of %s") % self.object.mountpoint

	@property
	def graph_vertical_label(self):
		_ = self.locale.translate
		return _("Inodes")


class DiskUsageObject(base.Object):
	rrd_schema = [
		"DS:used:GAUGE:0:U",
		"DS:free:GAUGE:0:U",
		"DS:inodes_used:GAUGE:0:U",
		"DS:inodes_free:GAUGE:0:U",
	]

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.mountpoint)

	def init(self, mountpoint):
		self.mountpoint = mountpoint

	@property
	def id(self):
		mountpoint = self.mountpoint

		if mountpoint.startswith("/"):
			mountpoint = mountpoint[1:]

		if not mountpoint:
			return "root"

		return mountpoint.replace("/", "-")

	def collect(self):
		stats = os.statvfs(self.mountpoint)

		return (
			# used
			(stats.f_blocks * stats.f_frsize) - \
				(stats.f_bfree * stats.f_bsize),
			# free
			stats.f_bfree * stats.f_bsize,
			# inodes used
			stats.f_files - stats.f_ffree,
			# inodes free
			stats.f_ffree,
		)


class DiskUsagePlugin(base.Plugin):
	name = "df"
	description = "Disk Usage Plugin"

	templates = [
		GraphTemplateDiskUsage,
		GraphTemplateInodeUsage,
	]

	@property
	def objects(self):
		for dev, mnt, fs, opts in _collecty.get_mountpoints():
			yield DiskUsageObject(self, mnt)
