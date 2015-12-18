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
#include <oping.h>
#include <time.h>

#include "_collectymodule.h"

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

PyTypeObject PingType = {
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

void Ping_dealloc(PingObject* self) {
	if (self->ping)
		ping_destroy(self->ping);

	Py_TYPE(self)->tp_free((PyObject*)self);
}

void Ping_init_stats(PingObject* self) {
	self->stats.history_index = 0;
	self->stats.history_size = 0;
	self->stats.packets_sent = 0;
	self->stats.packets_rcvd = 0;

	self->stats.average = 0.0;
	self->stats.stddev = 0.0;
	self->stats.loss = 0.0;
}

PyObject* Ping_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
	PingObject* self = (PingObject*)type->tp_alloc(type, 0);

	if (self) {
		self->ping = NULL;
		self->host = NULL;

		Ping_init_stats(self);
	}

	return (PyObject*)self;
}

int Ping_init(PingObject* self, PyObject* args, PyObject* kwds) {
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

double Ping_compute_average(PingObject* self) {
	assert(self->stats.packets_rcvd > 0);

	double total_latency = 0.0;

	for (int i = 0; i < self->stats.history_size; i++) {
		if (self->stats.history[i] > 0)
			total_latency += self->stats.history[i];
	}

	return total_latency / self->stats.packets_rcvd;
}

double Ping_compute_stddev(PingObject* self, double mean) {
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

PyObject* Ping_ping(PingObject* self, PyObject* args, PyObject* kwds) {
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

PyObject* Ping_get_packets_sent(PingObject* self) {
	return PyLong_FromUnsignedLong(self->stats.packets_sent);
}

PyObject* Ping_get_packets_rcvd(PingObject* self) {
	return PyLong_FromUnsignedLong(self->stats.packets_rcvd);
}

PyObject* Ping_get_average(PingObject* self) {
	return PyFloat_FromDouble(self->stats.average);
}

PyObject* Ping_get_stddev(PingObject* self) {
	return PyFloat_FromDouble(self->stats.stddev);
}

PyObject* Ping_get_loss(PingObject* self) {
	return PyFloat_FromDouble(self->stats.loss);
}
