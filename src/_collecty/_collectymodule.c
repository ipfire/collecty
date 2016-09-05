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

#include "_collectymodule.h"

static PyMethodDef collecty_module_methods[] = {
	{"get_detected_sensors", (PyCFunction)_collecty_get_detected_sensors, METH_VARARGS, NULL},
	{"get_mountpoints", (PyCFunction)_collecty_get_mountpoints, METH_NOARGS, NULL},
	{"sensors_cleanup", (PyCFunction)_collecty_sensors_cleanup, METH_NOARGS, NULL},
	{"sensors_init", (PyCFunction)_collecty_sensors_init, METH_NOARGS, NULL},
	{NULL},
};

static struct PyModuleDef collecty_module = {
	PyModuleDef_HEAD_INIT,
	"_collecty",                        /* m_name */
	"_collecty module",                 /* m_doc */
	-1,                                 /* m_size */
	collecty_module_methods,            /* m_methods */
	NULL,                               /* m_reload */
	NULL,                               /* m_traverse */
	NULL,                               /* m_clear */
	NULL,                               /* m_free */
};

PyMODINIT_FUNC PyInit__collecty(void) {
	if (PyType_Ready(&BlockDeviceType) < 0)
		return NULL;

	if (PyType_Ready(&PingType) < 0)
		return NULL;

	if (PyType_Ready(&SensorType) < 0)
		return NULL;

	PyObject* m = PyModule_Create(&collecty_module);

	Py_INCREF(&BlockDeviceType);
	PyModule_AddObject(m, "BlockDevice", (PyObject*)&BlockDeviceType);

	Py_INCREF(&PingType);
	PyModule_AddObject(m, "Ping", (PyObject*)&PingType);

	PyExc_PingError = PyErr_NewException("_collecty.PingError", NULL, NULL);
	Py_INCREF(PyExc_PingError);
	PyModule_AddObject(m, "PingError", PyExc_PingError);

	PyExc_PingAddHostError = PyErr_NewException("_collecty.PingAddHostError", NULL, NULL);
	Py_INCREF(PyExc_PingAddHostError);
	PyModule_AddObject(m, "PingAddHostError", PyExc_PingAddHostError);

	PyExc_PingNoReplyError = PyErr_NewException("_collecty.PingNoReplyError", NULL, NULL);
	Py_INCREF(PyExc_PingNoReplyError);
	PyModule_AddObject(m, "PingNoReplyError", PyExc_PingNoReplyError);

	Py_INCREF(&SensorType);
	PyModule_AddObject(m, "Sensor", (PyObject*)&SensorType);

	return m;
}
