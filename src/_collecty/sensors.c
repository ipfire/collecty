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

#include <errno.h>
#include <mntent.h>
#include <sensors/error.h>
#include <sensors/sensors.h>

#include "_collectymodule.h"

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

PyTypeObject SensorType = {
	PyObject_HEAD_INIT(NULL)
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

void Sensor_dealloc(SensorObject* self) {
	Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* Sensor_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
	SensorObject* self = (SensorObject*)type->tp_alloc(type, 0);

	return (PyObject *)self;
}

int Sensor_init(SensorObject* self, PyObject* args, PyObject* kwds) {
	return 0;
}

PyObject* Sensor_get_label(SensorObject* self) {
	char* label = sensors_get_label(self->chip, self->feature);

	if (label) {
		PyObject* string = PyUnicode_FromString(label);
		free(label);

		return string;
	}

	Py_RETURN_NONE;
}

PyObject* Sensor_get_name(SensorObject* self) {
	char chip_name[512];

	int r = sensors_snprintf_chip_name(chip_name, sizeof(chip_name), self->chip);
	if (r < 0) {
		PyErr_Format(PyExc_RuntimeError, "Could not print chip name");
		return NULL;
	}

	return PyUnicode_FromString(chip_name);
}

PyObject* Sensor_get_type(SensorObject* self) {
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
		return PyUnicode_FromString(type);

	Py_RETURN_NONE;
}

PyObject* Sensor_get_bus(SensorObject* self) {
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
		return PyUnicode_FromString(type);

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

PyObject* Sensor_return_value(SensorObject* sensor, sensors_subfeature_type subfeature_type) {
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

PyObject* Sensor_get_value(SensorObject* self) {
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

PyObject* Sensor_get_critical(SensorObject* self) {
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

PyObject* Sensor_get_maximum(SensorObject* self) {
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

PyObject* Sensor_get_minimum(SensorObject* self) {
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

PyObject* Sensor_get_high(SensorObject* self) {
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

PyObject* _collecty_sensors_init() {
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

PyObject* _collecty_sensors_cleanup() {
	sensors_cleanup();
	Py_RETURN_NONE;
}

PyObject* _collecty_get_detected_sensors(PyObject* o, PyObject* args) {
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
