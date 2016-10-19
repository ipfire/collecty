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

#include <atasmart.h>
#include <errno.h>
#include <fcntl.h>
#include <mntent.h>
#include <stdbool.h>
#include <string.h>
#include <sys/ioctl.h>

#include "_collectymodule.h"

static PyGetSetDef BlockDevice_getsetters[] = {
	{"path", (getter)BlockDevice_get_path, NULL, NULL, NULL},
	{"model", (getter)BlockDevice_get_model, NULL, NULL, NULL},
	{"serial", (getter)BlockDevice_get_serial, NULL, NULL, NULL},
};

static PyMethodDef BlockDevice_methods[] = {
	{"get_bad_sectors", (PyCFunction)BlockDevice_get_bad_sectors, METH_NOARGS, NULL},
	{"get_temperature", (PyCFunction)BlockDevice_get_temperature, METH_NOARGS, NULL},
	{"is_smart_supported", (PyCFunction)BlockDevice_is_smart_supported, METH_NOARGS, NULL},
	{"is_awake", (PyCFunction)BlockDevice_is_awake, METH_NOARGS, NULL},
	{NULL}
};

PyTypeObject BlockDeviceType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"_collecty.BlockDevice",            /*tp_name*/
	sizeof(BlockDevice),                /*tp_basicsize*/
	0,                                  /*tp_itemsize*/
	(destructor)BlockDevice_dealloc,    /*tp_dealloc*/
	0,                                  /*tp_print*/
	0,                                  /*tp_getattr*/
	0,                                  /*tp_setattr*/
	0,                                  /*tp_compare*/
	0,                                  /*tp_repr*/
	0,                                  /*tp_as_number*/
	0,                                  /*tp_as_sequence*/
	0,                                  /*tp_as_mapping*/
	0,                                  /*tp_hash */
	0,                                  /*tp_call*/
	0,                                  /*tp_str*/
	0,                                  /*tp_getattro*/
	0,                                  /*tp_setattro*/
	0,                                  /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
	"BlockDevice objects",              /* tp_doc */
	0,		                            /* tp_traverse */
	0,		                            /* tp_clear */
	0,		                            /* tp_richcompare */
	0,		                            /* tp_weaklistoffset */
	0,		                            /* tp_iter */
	0,		                            /* tp_iternext */
	BlockDevice_methods,                /* tp_methods */
	0,                                  /* tp_members */
	BlockDevice_getsetters,             /* tp_getset */
	0,                                  /* tp_base */
	0,                                  /* tp_dict */
	0,                                  /* tp_descr_get */
	0,                                  /* tp_descr_set */
	0,                                  /* tp_dictoffset */
	(initproc)BlockDevice_init,         /* tp_init */
	0,                                  /* tp_alloc */
	BlockDevice_new,                    /* tp_new */
};

void BlockDevice_dealloc(BlockDevice* self) {
	if (self->disk)
		sk_disk_free(self->disk);

	if (self->path)
		free(self->path);

	Py_TYPE(self)->tp_free((PyObject*)self);
}

int BlockDevice_get_identity(BlockDevice* device) {
	int fd;

	if ((fd = open(device->path, O_RDONLY | O_NONBLOCK)) < 0) {
		return 1;
	}

	int r = ioctl(fd, HDIO_GET_IDENTITY, &device->identity);
	close(fd);

	if (r)
		return 1;

	return 0;
}

int BlockDevice_smart_is_available(BlockDevice* device) {
	SkBool available = FALSE;

	int r = sk_disk_smart_is_available(device->disk, &available);
	if (r)
		return -1;

	if (available)
		return 0;

	return 1;
}

int BlockDevice_check_sleep_mode(BlockDevice* device) {
	SkBool awake = FALSE;

	int r = sk_disk_check_sleep_mode(device->disk, &awake);
	if (r)
		return -1;

	if (awake)
		return 0;

	return 1;
}

PyObject * BlockDevice_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
	BlockDevice* self = (BlockDevice*)type->tp_alloc(type, 0);

	if (self) {
		self->path = NULL;

		// libatasmart
		self->disk = NULL;
	}

	return (PyObject *)self;
}

int BlockDevice_init(BlockDevice* self, PyObject* args, PyObject* kwds) {
	const char* path = NULL;

	if (!PyArg_ParseTuple(args, "s", &path))
		return -1;

	self->path = strdup(path);

	int r = BlockDevice_get_identity(self);
	if (r) {
		PyErr_Format(PyExc_OSError, "Could not open block device: %s", path);
		return -1;
	}

	r = sk_disk_open(path, &self->disk);
	if (r == 0) {
		if (BlockDevice_smart_is_available(self) == 0) {
			if (BlockDevice_check_sleep_mode(self) == 0) {
				r = sk_disk_smart_read_data(self->disk);
				if (r) {
					PyErr_Format(PyExc_OSError, "Could not open block device %s: %s", path,
						strerror(errno));
					return -1;
				}
			}
		}
	} else {
		PyErr_Format(PyExc_OSError, "Could not open block device %s: %s", path,
			strerror(errno));
		return -1;
	}

	//sk_disk_identify_is_available

	return 0;
}

PyObject* BlockDevice_get_path(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	return PyUnicode_FromString(device->path);
}

static void clean_string(char *s) {
	for (char* e = s; *e; e++) {
		if (*e < ' ' || *e >= 127)
			*e = ' ';
	}
}

static void drop_spaces(char *s) {
	char *d = s;
	bool prev_space = false;

	s += strspn(s, " ");

	for (; *s; s++) {
		if (prev_space) {
			if (*s != ' ') {
				prev_space = false;
				*(d++) = ' ';
				*(d++) = *s;
			}
		} else {
			if (*s == ' ')
				prev_space = true;
			else
				*(d++) = *s;
		}
	}

	*d = 0;
}

static void copy_string(char* d, const char* s, size_t n) {
	// Copy the source buffer to the destination buffer up to n
	memcpy(d, s, n);

	// Terminate the destination buffer with NULL
	d[n] = '\0';

	// Clean up the string from non-printable characters
	clean_string(d);
	drop_spaces(d);
}

PyObject* BlockDevice_get_model(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	char model[MODEL_SIZE + 1];
	copy_string(model, device->identity.model, sizeof(model));

	return PyUnicode_FromString(model);
}

PyObject* BlockDevice_get_serial(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	char serial[SERIAL_SIZE + 1];
	copy_string(serial, device->identity.serial_no, sizeof(serial));

	return PyUnicode_FromString(serial);
}

PyObject* BlockDevice_is_smart_supported(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	if (BlockDevice_smart_is_available(device) == 0)
		Py_RETURN_TRUE;

	Py_RETURN_FALSE;
}

PyObject* BlockDevice_is_awake(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	if (BlockDevice_check_sleep_mode(device) == 0)
		Py_RETURN_TRUE;

	Py_RETURN_FALSE;
}

PyObject* BlockDevice_get_bad_sectors(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	if (BlockDevice_smart_is_available(device)) {
		PyErr_Format(PyExc_OSError, "Device does not support SMART");
		return NULL;
	}

	uint64_t bad_sectors;
	int r = sk_disk_smart_get_bad(device->disk, &bad_sectors);
	if (r)
		return NULL;

	return PyLong_FromUnsignedLongLong((unsigned long long)bad_sectors);
}

PyObject* BlockDevice_get_temperature(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	if (BlockDevice_smart_is_available(device)) {
		PyErr_Format(PyExc_OSError, "Device does not support SMART");
		return NULL;
	}

	uint64_t mkelvin;
	int r = sk_disk_smart_get_temperature(device->disk, &mkelvin);
	if (r) {
		// Temperature not available but SMART is supported
		if (errno == ENOENT) {
			PyErr_Format(PyExc_OSError, "Device does not have a temperature");
		}

		return NULL;
	}

	// Convert the temperature to Kelvin
	return PyFloat_FromDouble((double)mkelvin / 1000.0);
}
