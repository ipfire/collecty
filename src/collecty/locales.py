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

import gettext
import logging
import os

from .constants import *
from .i18n import TEXTDOMAIN

log = logging.getLogger("collecty.locale")

class Locale(object):
	def __init__(self, lang):
		self.lang = lang

	def translate(self, message, plural_message=None, count=None):
		if plural_message is not None:
			assert count is not None

			# Replace the message by the plural message if
			# we are using plural.
			if count > 1:
				message = plural_message

		return message


class GettextLocale(Locale):
	def __init__(self, lang, translation):
		Locale.__init__(self, lang)

		self.translation = translation

		# Bind gettext functions
		self.gettext = self.translation.gettext
		self.ngettext = self.translation.ngettext

	def translate(self, message, plural_message=None, count=None):
		if plural_message is not None:
			assert count is not None
			return self.ngettext(message, plural_message, count)

		return self.gettext(message)


def _find_all_locales(domain, directory):
	locales = {
		DEFAULT_LOCALE : Locale(DEFAULT_LOCALE),
	}

	for lang in os.listdir(directory):
		if lang.startswith("."):
			continue

		filename = os.path.join(directory, lang, "LC_MESSAGES",
			"%s.mo" % domain)

		# Check if a translation file exists and go on if not
		if not os.path.exists(filename):
			continue

		try:
			translation = gettext.translation(domain,
				directory, languages=[lang])
		except Exception as e:
			log.error("Cound not load translation for %s: %s" \
				% (lang, e))
			continue

		locales[lang] = GettextLocale(lang, translation)

	log.debug("Loaded translations: %s" % ", ".join(locales.keys()))

	return locales

_locales = _find_all_locales(TEXTDOMAIN, "/usr/share/locale")

def get_supported_locales():
	return list(_locales.keys())

def get_closest(*langs):
	for lang in langs:
		if not lang:
			continue

		lang = lang.replace("-", "_")
		parts = lang.split("_")

		if len(parts) > 2:
			continue

		elif len(parts) == 2:
			parts[0] = parts[0].lower()
			parts[1] = parts[1].upper()
			lang = "_".join(parts)

		for l in (lang, parts[0]):
			try:
				return _locales[l]
			except KeyError:
				pass

def get(*langs):
	return get_closest(*langs) or _locales.get(DEFAULT_LOCALE, None)
