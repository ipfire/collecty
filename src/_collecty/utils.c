/*
 * collecty
 * Copyright (C) 2015 IPFire Team (www.ipfire.org)
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <Python.h>
#include <mntent.h>

#include "_collectymodule.h"

int _collecty_mountpoint_is_virtual(const struct mntent* mp) {
	// Ignore all ramdisks
	if (mp->mnt_fsname[0] != '/')
		return 1;

	// Ignore network mounts
	if (hasmntopt(mp, "_netdev") != NULL)
		return 1;

	return 0;
}

PyObject* _collecty_get_mountpoints() {
	FILE* fp = setmntent(_PATH_MOUNTED, "r");
	if (!fp)
		return NULL;

	PyObject* list = PyList_New(0);
	int r = 0;

	struct mntent* mountpoint = getmntent(fp);
	while (mountpoint) {
		if (!_collecty_mountpoint_is_virtual(mountpoint)) {
			// Create a tuple with the information of the mountpoint
			PyObject* mp = PyTuple_New(4);
			PyTuple_SET_ITEM(mp, 0, PyUnicode_FromString(mountpoint->mnt_fsname));
			PyTuple_SET_ITEM(mp, 1, PyUnicode_FromString(mountpoint->mnt_dir));
			PyTuple_SET_ITEM(mp, 2, PyUnicode_FromString(mountpoint->mnt_type));
			PyTuple_SET_ITEM(mp, 3, PyUnicode_FromString(mountpoint->mnt_opts));

			// Append the tuple to the list
			r = PyList_Append(list, mp);
			if (r)
				break;
		}

		// Move on to the next mountpoint
		mountpoint = getmntent(fp);
	}

	endmntent(fp);

	if (r) {
		Py_DECREF(list);
		return NULL;
	}

	return list;
}
