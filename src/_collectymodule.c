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
#include <mntent.h>
#include <oping.h>
#include <sensors/error.h>
#include <sensors/sensors.h>
#include <stdbool.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>

#define MODEL_SIZE  40
#define SERIAL_SIZE 20

#define PING_HISTORY_SIZE 1024
#define PING_DEFAULT_COUNT 10
#define PING_DEFAULT_TIMEOUT 8

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

	Py_TYPE(self)->tp_free((PyObject*)self);
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

static PyObject* BlockDevice_get_model(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	char model[MODEL_SIZE + 1];
	copy_string(model, device->identity.model, sizeof(model));

	return PyUnicode_FromString(model);
}

static PyObject* BlockDevice_get_serial(PyObject* self) {
	BlockDevice* device = (BlockDevice*)self;

	char serial[SERIAL_SIZE + 1];
	copy_string(serial, device->identity.serial_no, sizeof(serial));

	return PyUnicode_FromString(serial);
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

	// Convert the temperature to Kelvin
	return PyFloat_FromDouble((double)mkelvin / 1000.0);
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

static PyObject* PyExc_PingError;
static PyObject* PyExc_PingAddHostError;

typedef struct {
	PyObject_HEAD
	pingobj_t* ping;
	const char* host;
	struct {
		double history[PING_HISTORY_SIZE];
		size_t history_index;
		size_t history_size;
		size_t packets_sent;
		size_t packets_rcvd;
		double average;
		double stddev;
		double loss;
	} stats;
} PingObject;

static void Ping_dealloc(PingObject* self) {
	if (self->ping)
		ping_destroy(self->ping);

	Py_TYPE(self)->tp_free((PyObject*)self);
}

static void Ping_init_stats(PingObject* self) {
	self->stats.history_index = 0;
	self->stats.history_size = 0;
	self->stats.packets_sent = 0;
	self->stats.packets_rcvd = 0;

	self->stats.average = 0.0;
	self->stats.stddev = 0.0;
	self->stats.loss = 0.0;
}

static PyObject* Ping_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
	PingObject* self = (PingObject*)type->tp_alloc(type, 0);

	if (self) {
		self->ping = NULL;
		self->host = NULL;

		Ping_init_stats(self);
	}

	return (PyObject*)self;
}

static int Ping_init(PingObject* self, PyObject* args, PyObject* kwds) {
	char* kwlist[] = {"host", "family", "timeout", "ttl", NULL};
	int family = PING_DEF_AF;
	double timeout = PING_DEFAULT_TIMEOUT;
	int ttl = PING_DEF_TTL;

	if (!PyArg_ParseTupleAndKeywords(args, kwds, "s|idi", kwlist, &self->host,
			&family, &timeout, &ttl))
		return -1;

	if (family != AF_UNSPEC && family != AF_INET6 && family != AF_INET) {
		PyErr_Format(PyExc_ValueError, "Family must be AF_UNSPEC, AF_INET6, or AF_INET");
		return -1;
	}

	if (timeout < 0) {
		PyErr_Format(PyExc_ValueError, "Timeout must be greater than zero");
		return -1;
	}

	if (ttl < 1 || ttl > 255) {
		PyErr_Format(PyExc_ValueError, "TTL must be between 1 and 255");
		return -1;
	}

	self->ping = ping_construct();
	if (!self->ping) {
		return -1;
	}

	// Set options
	int r;

	r = ping_setopt(self->ping, PING_OPT_AF, &family);
	if (r) {
		PyErr_Format(PyExc_RuntimeError, "Could not set address family: %s",
			ping_get_error(self->ping));
		return -1;
	}

	if (timeout > 0) {
		r = ping_setopt(self->ping, PING_OPT_TIMEOUT, &timeout);

		if (r) {
			PyErr_Format(PyExc_RuntimeError, "Could not set timeout: %s",
				ping_get_error(self->ping));
			return -1;
		}
	}

	r = ping_setopt(self->ping, PING_OPT_TTL, &ttl);
	if (r) {
		PyErr_Format(PyExc_RuntimeError, "Could not set TTL: %s",
			ping_get_error(self->ping));
		return -1;
	}

	return 0;
}

static double Ping_compute_average(PingObject* self) {
	assert(self->stats.packets_rcvd > 0);

	double total_latency = 0.0;

	for (int i = 0; i < self->stats.history_size; i++) {
		if (self->stats.history[i] > 0)
			total_latency += self->stats.history[i];
	}

	return total_latency / self->stats.packets_rcvd;
}

static double Ping_compute_stddev(PingObject* self, double mean) {
	assert(self->stats.packets_rcvd > 0);

	double deviation = 0.0;

	for (int i = 0; i < self->stats.history_size; i++) {
		if (self->stats.history[i] > 0) {
			deviation += pow(self->stats.history[i] - mean, 2);
		}
	}

	// Normalise
	deviation /= self->stats.packets_rcvd;

	return sqrt(deviation);
}

static void Ping_compute_stats(PingObject* self) {
	// Compute the average latency
	self->stats.average = Ping_compute_average(self);

	// Compute the standard deviation
	self->stats.stddev = Ping_compute_stddev(self, self->stats.average);

	// Compute lost packets
	self->stats.loss = 1.0;
	self->stats.loss -= (double)self->stats.packets_rcvd \
		/ (double)self->stats.packets_sent;
}

static double time_elapsed(struct timeval* t0) {
	struct timeval now;
	gettimeofday(&now, NULL);

	double r = now.tv_sec - t0->tv_sec;
	r += ((double)now.tv_usec / 1000000) - ((double)t0->tv_usec / 1000000);

	return r;
}

static PyObject* Ping_ping(PingObject* self, PyObject* args, PyObject* kwds) {
	char* kwlist[] = {"count", "deadline", NULL};
	size_t count = PING_DEFAULT_COUNT;
	double deadline = 0;

	if (!PyArg_ParseTupleAndKeywords(args, kwds, "|Id", kwlist, &count, &deadline))
		return NULL;

	int r = ping_host_add(self->ping, self->host);
	if (r) {
		PyErr_Format(PyExc_PingAddHostError, "Could not add host %s: %s",
			self->host, ping_get_error(self->ping));
		return NULL;
	}

	// Reset all collected statistics in case ping() is called more than once.
	Ping_init_stats(self);

	// Save start time
	struct timeval time_start;
	r = gettimeofday(&time_start, NULL);
	if (r) {
		PyErr_Format(PyExc_RuntimeError, "Could not determine start time");
		return NULL;
	}

	// Do the pinging
	while (count--) {
		self->stats.packets_sent++;

		Py_BEGIN_ALLOW_THREADS
		r = ping_send(self->ping);
		Py_END_ALLOW_THREADS

		// Count recieved packets
		if (r >= 0) {
			self->stats.packets_rcvd += r;

		// Raise any errors
		} else {
			PyErr_Format(PyExc_RuntimeError, "Error executing ping_send(): %s",
				ping_get_error(self->ping));
			return NULL;
		}

		// Extract all data
		pingobj_iter_t* iter = ping_iterator_get(self->ping);

		double* latency = &self->stats.history[self->stats.history_index];
		size_t buffer_size = sizeof(latency);
		ping_iterator_get_info(iter, PING_INFO_LATENCY, latency, &buffer_size);

		// Increase the history pointer
		self->stats.history_index++;
		self->stats.history_index %= sizeof(self->stats.history);

		// Increase the history size
		if (self->stats.history_size < sizeof(self->stats.history))
			self->stats.history_size++;

		// Check if the deadline is due
		if (deadline > 0) {
			double elapsed_time = time_elapsed(&time_start);

			// If we have run longer than the deadline is, we end the main loop
			if (elapsed_time >= deadline)
				break;
		}
	}

	if (self->stats.packets_rcvd == 0) {
		PyErr_Format(PyExc_PingError, "No replies received from %s", self->host);
		return NULL;
	}

	Ping_compute_stats(self);

	Py_RETURN_NONE;
}

static PyObject* Ping_get_packets_sent(PingObject* self) {
	return PyLong_FromUnsignedLong(self->stats.packets_sent);
}

static PyObject* Ping_get_packets_rcvd(PingObject* self) {
	return PyLong_FromUnsignedLong(self->stats.packets_rcvd);
}

static PyObject* Ping_get_average(PingObject* self) {
	return PyFloat_FromDouble(self->stats.average);
}

static PyObject* Ping_get_stddev(PingObject* self) {
	return PyFloat_FromDouble(self->stats.stddev);
}

static PyObject* Ping_get_loss(PingObject* self) {
	return PyFloat_FromDouble(self->stats.loss);
}

static PyGetSetDef Ping_getsetters[] = {
	{"average", (getter)Ping_get_average, NULL, NULL, NULL},
	{"loss", (getter)Ping_get_loss, NULL, NULL, NULL},
	{"stddev", (getter)Ping_get_stddev, NULL, NULL, NULL},
	{"packets_sent", (getter)Ping_get_packets_sent, NULL, NULL, NULL},
	{"packets_rcvd", (getter)Ping_get_packets_rcvd, NULL, NULL, NULL},
	{NULL}
};

static PyMethodDef Ping_methods[] = {
	{"ping", (PyCFunction)Ping_ping, METH_VARARGS|METH_KEYWORDS, NULL},
	{NULL}
};

static PyTypeObject PingType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"_collecty.Ping",                   /*tp_name*/
	sizeof(PingObject),                 /*tp_basicsize*/
	0,                                  /*tp_itemsize*/
	(destructor)Ping_dealloc,           /*tp_dealloc*/
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
	"Ping object",                      /* tp_doc */
	0,		                            /* tp_traverse */
	0,		                            /* tp_clear */
	0,		                            /* tp_richcompare */
	0,		                            /* tp_weaklistoffset */
	0,		                            /* tp_iter */
	0,		                            /* tp_iternext */
	Ping_methods,                       /* tp_methods */
	0,                                  /* tp_members */
	Ping_getsetters,                    /* tp_getset */
	0,                                  /* tp_base */
	0,                                  /* tp_dict */
	0,                                  /* tp_descr_get */
	0,                                  /* tp_descr_set */
	0,                                  /* tp_dictoffset */
	(initproc)Ping_init,                /* tp_init */
	0,                                  /* tp_alloc */
	Ping_new,                           /* tp_new */
};

typedef struct {
	PyObject_HEAD
	const sensors_chip_name* chip;
	const sensors_feature* feature;
} SensorObject;

static void Sensor_dealloc(SensorObject* self) {
	Py_TYPE(self)->tp_free((PyObject*)self);
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
		PyObject* string = PyUnicode_FromString(label);
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

	return PyUnicode_FromString(chip_name);
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
		return PyUnicode_FromString(type);

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

static int _collecty_mountpoint_is_virtual(const struct mntent* mp) {
	// Ignore all ramdisks
	if (mp->mnt_fsname[0] != '/')
		return 1;

	// Ignore network mounts
	if (hasmntopt(mp, "_netdev") != NULL)
		return 1;

	return 0;
}

static PyObject* _collecty_get_mountpoints() {
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

	Py_INCREF(&SensorType);
	PyModule_AddObject(m, "Sensor", (PyObject*)&SensorType);

	return m;
}
