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
#include <linux/hdreg.h>
#include <sensors/error.h>
#include <sensors/sensors.h>
#include <stdbool.h>
#include <string.h>
#include <sys/ioctl.h>

#define MODEL_SIZE  40
#define SERIAL_SIZE 20

typedef struct {
	PyObject_HEAD
	char* path;
	struct hd_driveid identity;
	SkDisk* disk;
} BlockDevice;

static void BlockDevice_dealloc(BlockDevice* self) {
	if (self->disk)
		sk_disk_free(self->disk);

	if (self->path)
		free(self->path);

	self->ob_type->tp_free((PyObject*)self);
}

static int BlockDevice_get_identity(BlockDevice* device) {
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

static int BlockDevice_smart_is_available(BlockDevice* device) {
	SkBool available = FALSE;

	int r = sk_disk_smart_is_available(device->disk, &available);
	if (r)
		return -1;

	if (available)
		return 0;

	return 1;
}

static int BlockDevice_check_sleep_mode(BlockDevice* device) {
	SkBool awake = FALSE;

	int r = sk_disk_check_sleep_mode(device->disk, &awake);
	if (r)
		return -1;

	if (awake)
		return 0;

	return 1;
}

static PyObject * BlockDevice_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
	BlockDevice* self = (BlockDevice*)type->tp_alloc(type, 0);

	if (self) {
		self->path = NULL;

		// libatasmart
		self->disk = NULL;
	}

	return (PyObject *)self;
}

static int BlockDevice_init(BlockDevice* self, PyObject* args, PyObject* kwds) {
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

static PyObject* BlockDevice_get_path(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	return PyString_FromString(device->path);
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

static PyObject* BlockDevice_get_model(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	char model[MODEL_SIZE + 1];
	copy_string(model, device->identity.model, sizeof(model));

	return PyString_FromString(model);
}

static PyObject* BlockDevice_get_serial(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	char serial[SERIAL_SIZE + 1];
	copy_string(serial, device->identity.serial_no, sizeof(serial));

	return PyString_FromString(serial);
}

static PyObject* BlockDevice_is_smart_supported(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	if (BlockDevice_smart_is_available(device) == 0)
		Py_RETURN_TRUE;

	Py_RETURN_FALSE;
}

static PyObject* BlockDevice_is_awake(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	if (BlockDevice_check_sleep_mode(device) == 0)
		Py_RETURN_TRUE;

	Py_RETURN_FALSE;
}

static PyObject* BlockDevice_get_bad_sectors(PyObject* self) {
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

static PyObject* BlockDevice_get_temperature(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	if (BlockDevice_smart_is_available(device)) {
		PyErr_Format(PyExc_OSError, "Device does not support SMART");
		return NULL;
	}

	uint64_t mkelvin;
	int r = sk_disk_smart_get_temperature(device->disk, &mkelvin);
	if (r)
		return NULL;

	return PyLong_FromUnsignedLongLong((unsigned long long)mkelvin);
}

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

static PyTypeObject BlockDeviceType = {
	PyObject_HEAD_INIT(NULL)
	0,                                  /*ob_size*/
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

typedef struct {
	PyObject_HEAD
	const sensors_chip_name* chip;
	const sensors_feature* feature;
} SensorObject;

static void Sensor_dealloc(SensorObject* self) {
	self->ob_type->tp_free((PyObject*)self);
}

static PyObject* Sensor_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
	SensorObject* self = (SensorObject*)type->tp_alloc(type, 0);

	return (PyObject *)self;
}

static int Sensor_init(SensorObject* self, PyObject* args, PyObject* kwds) {
	return 0;
}

static PyObject* Sensor_get_label(SensorObject* self) {
	char* label = sensors_get_label(self->chip, self->feature);

	if (label) {
		PyObject* string = PyString_FromString(label);
		free(label);

		return string;
	}

	Py_RETURN_NONE;
}

static PyObject* Sensor_get_name(SensorObject* self) {
	char chip_name[512];

	int r = sensors_snprintf_chip_name(chip_name, sizeof(chip_name), self->chip);
	if (r < 0) {
		PyErr_Format(PyExc_RuntimeError, "Could not print chip name");
		return NULL;
	}

	return PyString_FromString(chip_name);
}

static PyObject* Sensor_get_type(SensorObject* self) {
	const char* type = NULL;

	switch (self->feature->type) {
		case SENSORS_FEATURE_IN:
			type = "voltage";
			break;

		case SENSORS_FEATURE_FAN:
			type = "fan";
			break;

		case SENSORS_FEATURE_TEMP:
			type = "temperature";
			break;

		case SENSORS_FEATURE_POWER:
			type = "power";
			break;

		default:
			break;
	}

	if (type)
		return PyString_FromString(type);

	Py_RETURN_NONE;
}

static PyObject* Sensor_get_bus(SensorObject* self) {
	const char* type = NULL;

	switch (self->chip->bus.type) {
		case SENSORS_BUS_TYPE_I2C:
			type = "i2c";
			break;

		case SENSORS_BUS_TYPE_ISA:
			type = "isa";
			break;

		case SENSORS_BUS_TYPE_PCI:
			type = "pci";
			break;

		case SENSORS_BUS_TYPE_SPI:
			type = "spi";
			break;

		case SENSORS_BUS_TYPE_VIRTUAL:
			type = "virtual";
			break;

		case SENSORS_BUS_TYPE_ACPI:
			type = "acpi";
			break;

		case SENSORS_BUS_TYPE_HID:
			type = "hid";
			break;

		default:
			break;
	}

	if (type)
		return PyString_FromString(type);

	Py_RETURN_NONE;
}

static const sensors_subfeature* Sensor_get_subfeature(SensorObject* sensor, sensors_subfeature_type type) {
	const sensors_subfeature* subfeature;
	int subfeature_num = 0;

	while ((subfeature = sensors_get_all_subfeatures(sensor->chip, sensor->feature, &subfeature_num))) {
		if (subfeature->type == type)
			break;
	}

	return subfeature;
}

static PyObject* Sensor_return_value(SensorObject* sensor, sensors_subfeature_type subfeature_type) {
	double value;

	const sensors_subfeature* subfeature = Sensor_get_subfeature(sensor, subfeature_type);
	if (!subfeature) {
		PyErr_Format(PyExc_AttributeError, "Could not find sensor of requested type");
		return NULL;
	}

	// Fetch value from the sensor
	int r = sensors_get_value(sensor->chip, subfeature->number, &value);
	if (r < 0) {
		PyErr_Format(PyExc_ValueError, "Error retrieving value from sensor: %s",
			sensors_strerror(errno));
		return NULL;
	}

	// Convert all temperature values from Celcius to Kelvon
	if (sensor->feature->type == SENSORS_FEATURE_TEMP)
		value += 273.15;

	return PyFloat_FromDouble(value);
}

static PyObject* Sensor_no_value() {
	PyErr_Format(PyExc_ValueError, "Value not supported for this sensor type");
	return NULL;
}

static PyObject* Sensor_get_value(SensorObject* self) {
	sensors_subfeature_type subfeature_type;

	switch (self->feature->type) {
		case SENSORS_FEATURE_IN:
			subfeature_type = SENSORS_SUBFEATURE_IN_INPUT;
			break;

		case SENSORS_FEATURE_FAN:
			subfeature_type = SENSORS_SUBFEATURE_FAN_INPUT;
			break;

		case SENSORS_FEATURE_TEMP:
			subfeature_type = SENSORS_SUBFEATURE_TEMP_INPUT;
			break;

		case SENSORS_FEATURE_POWER:
			subfeature_type = SENSORS_SUBFEATURE_POWER_INPUT;
			break;

		default:
			return Sensor_no_value();
	}

	return Sensor_return_value(self, subfeature_type);
}

static PyObject* Sensor_get_critical(SensorObject* self) {
	sensors_subfeature_type subfeature_type;

	switch (self->feature->type) {
		case SENSORS_FEATURE_IN:
			subfeature_type = SENSORS_SUBFEATURE_IN_CRIT;
			break;

		case SENSORS_FEATURE_TEMP:
			subfeature_type = SENSORS_SUBFEATURE_TEMP_CRIT;
			break;

		case SENSORS_FEATURE_POWER:
			subfeature_type = SENSORS_SUBFEATURE_POWER_CRIT;
			break;

		default:
			return Sensor_no_value();
	}

	return Sensor_return_value(self, subfeature_type);
}

static PyObject* Sensor_get_maximum(SensorObject* self) {
	sensors_subfeature_type subfeature_type;

	switch (self->feature->type) {
		case SENSORS_FEATURE_IN:
			subfeature_type = SENSORS_SUBFEATURE_IN_MAX;
			break;

		case SENSORS_FEATURE_FAN:
			subfeature_type = SENSORS_SUBFEATURE_FAN_MAX;
			break;

		case SENSORS_FEATURE_TEMP:
			subfeature_type = SENSORS_SUBFEATURE_TEMP_MAX;
			break;

		case SENSORS_FEATURE_POWER:
			subfeature_type = SENSORS_SUBFEATURE_POWER_MAX;
			break;

		default:
			return Sensor_no_value();
	}

	return Sensor_return_value(self, subfeature_type);
}

static PyObject* Sensor_get_minimum(SensorObject* self) {
	sensors_subfeature_type subfeature_type;

	switch (self->feature->type) {
		case SENSORS_FEATURE_IN:
			subfeature_type = SENSORS_SUBFEATURE_IN_MIN;
			break;

		case SENSORS_FEATURE_FAN:
			subfeature_type = SENSORS_SUBFEATURE_FAN_MIN;
			break;

		case SENSORS_FEATURE_TEMP:
			subfeature_type = SENSORS_SUBFEATURE_TEMP_MIN;
			break;

		default:
			return Sensor_no_value();
	}

	return Sensor_return_value(self, subfeature_type);
}

static PyObject* Sensor_get_high(SensorObject* self) {
	sensors_subfeature_type subfeature_type;

	switch (self->feature->type) {
		case SENSORS_FEATURE_TEMP:
			subfeature_type = SENSORS_SUBFEATURE_TEMP_MAX;
			break;

		default:
			return Sensor_no_value();
	}

	return Sensor_return_value(self, subfeature_type);
}

static PyGetSetDef Sensor_getsetters[] = {
	{"bus", (getter)Sensor_get_bus, NULL, NULL, NULL},
	{"critical", (getter)Sensor_get_critical, NULL, NULL, NULL},
	{"high", (getter)Sensor_get_high, NULL, NULL, NULL},
	{"label", (getter)Sensor_get_label, NULL, NULL, NULL},
	{"maximum", (getter)Sensor_get_maximum, NULL, NULL, NULL},
	{"minumum", (getter)Sensor_get_minimum, NULL, NULL, NULL},
	{"name", (getter)Sensor_get_name, NULL, NULL, NULL},
	{"type", (getter)Sensor_get_type, NULL, NULL, NULL},
	{"value", (getter)Sensor_get_value, NULL, NULL, NULL},
	{NULL},
};

static PyTypeObject SensorType = {
	PyObject_HEAD_INIT(NULL)
	0,                                  /*ob_size*/
	"_collecty.Sensor",                 /*tp_name*/
	sizeof(SensorObject),               /*tp_basicsize*/
	0,                                  /*tp_itemsize*/
	(destructor)Sensor_dealloc,         /*tp_dealloc*/
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
	"Sensor objects",                   /* tp_doc */
	0,                                  /* tp_traverse */
	0,                                  /* tp_clear */
	0,                                  /* tp_richcompare */
	0,                                  /* tp_weaklistoffset */
	0,                                  /* tp_iter */
	0,                                  /* tp_iternext */
	0,                                  /* tp_methods */
	0,                                  /* tp_members */
	Sensor_getsetters,                  /* tp_getset */
	0,                                  /* tp_base */
	0,                                  /* tp_dict */
	0,                                  /* tp_descr_get */
	0,                                  /* tp_descr_set */
	0,                                  /* tp_dictoffset */
	(initproc)Sensor_init,              /* tp_init */
	0,                                  /* tp_alloc */
	Sensor_new,                         /* tp_new */
};

static SensorObject* make_sensor_object(const sensors_chip_name* chip, const sensors_feature* feature) {
	SensorObject* sensor = PyObject_New(SensorObject, &SensorType);
	if (!sensor)
		return NULL;

	if (!PyObject_Init((PyObject*)sensor, &SensorType)) {
		Py_DECREF(sensor);
		return NULL;
	}

	sensor->chip = chip;
	sensor->feature = feature;

	return sensor;
}

static PyObject* _collecty_sensors_init() {
	// Clean up everything first in case sensors_init was called earlier
	sensors_cleanup();

	int r = sensors_init(NULL);
	if (r) {
		PyErr_Format(PyExc_OSError, "Could not initialise sensors: %s",
			sensors_strerror(errno));
		return NULL;
	}

	Py_RETURN_NONE;
}

static PyObject* _collecty_sensors_cleanup() {
	sensors_cleanup();
	Py_RETURN_NONE;
}

static PyObject* _collecty_get_detected_sensors(PyObject* o, PyObject* args) {
	const char* name = NULL;
	sensors_chip_name chip_name;

	if (!PyArg_ParseTuple(args, "|z", &name))
		return NULL;

	if (name) {
		int r = sensors_parse_chip_name(name, &chip_name);
		if (r < 0) {
			PyErr_Format(PyExc_ValueError, "Could not parse chip name: %s", name);
			return NULL;
		}
	}

	PyObject* list = PyList_New(0);

	const sensors_chip_name* chip;
	int chip_num = 0;

	while ((chip = sensors_get_detected_chips((name) ? &chip_name : NULL, &chip_num))) {
		const sensors_feature* feature;
		int feature_num = 0;

		while ((feature = sensors_get_features(chip, &feature_num))) {
			// Skip sensors we do not want to support
			switch (feature->type) {
				case SENSORS_FEATURE_IN:
				case SENSORS_FEATURE_FAN:
				case SENSORS_FEATURE_TEMP:
				case SENSORS_FEATURE_POWER:
					break;

				default:
					continue;
			}

			SensorObject* sensor = make_sensor_object(chip, feature);
			PyList_Append(list, (PyObject*)sensor);
		}
	}

	return list;
}

static PyMethodDef collecty_module_methods[] = {
	{"get_detected_sensors", (PyCFunction)_collecty_get_detected_sensors, METH_VARARGS, NULL},
	{"sensors_cleanup", (PyCFunction)_collecty_sensors_cleanup, METH_NOARGS, NULL},
	{"sensors_init", (PyCFunction)_collecty_sensors_init, METH_NOARGS, NULL},
	{NULL},
};

void init_collecty(void) {
	if (PyType_Ready(&BlockDeviceType) < 0)
		return;

	if (PyType_Ready(&SensorType) < 0)
		return;

	PyObject* m = Py_InitModule("_collecty", collecty_module_methods);

	PyModule_AddObject(m, "BlockDevice", (PyObject*)&BlockDeviceType);
	PyModule_AddObject(m, "Sensor", (PyObject*)&SensorType);
}
