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
#include <linux/hdreg.h>
#include <mntent.h>
#include <oping.h>
#include <sensors/error.h>
#include <sensors/sensors.h>

#define MODEL_SIZE  40
#define SERIAL_SIZE 20

#define PING_HISTORY_SIZE 1024
#define PING_DEFAULT_COUNT 10
#define PING_DEFAULT_TIMEOUT 8

/* block devices */
typedef struct {
	PyObject_HEAD
	char* path;
	struct hd_driveid identity;
	SkDisk* disk;
} BlockDevice;

PyTypeObject BlockDeviceType;

void BlockDevice_dealloc(BlockDevice* self);
int BlockDevice_get_identity(BlockDevice* device);
int BlockDevice_smart_is_available(BlockDevice* device);
int BlockDevice_check_sleep_mode(BlockDevice* device);
PyObject * BlockDevice_new(PyTypeObject* type, PyObject* args, PyObject* kwds);
int BlockDevice_init(BlockDevice* self, PyObject* args, PyObject* kwds);
PyObject* BlockDevice_get_path(PyObject* self);
PyObject* BlockDevice_get_model(PyObject* self);
PyObject* BlockDevice_get_serial(PyObject* self);
PyObject* BlockDevice_is_smart_supported(PyObject* self);
PyObject* BlockDevice_is_awake(PyObject* self);
PyObject* BlockDevice_get_bad_sectors(PyObject* self);
PyObject* BlockDevice_get_temperature(PyObject* self);

/* ping */
PyObject* PyExc_PingError;
PyObject* PyExc_PingAddHostError;
PyObject* PyExc_PingNoReplyError;

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

PyTypeObject PingType;

void Ping_dealloc(PingObject* self);
void Ping_init_stats(PingObject* self);
PyObject* Ping_new(PyTypeObject* type, PyObject* args, PyObject* kwds);
int Ping_init(PingObject* self, PyObject* args, PyObject* kwds);
double Ping_compute_average(PingObject* self);
double Ping_compute_stddev(PingObject* self, double mean);
PyObject* Ping_ping(PingObject* self, PyObject* args, PyObject* kwds);
PyObject* Ping_get_packets_sent(PingObject* self);
PyObject* Ping_get_packets_rcvd(PingObject* self);
PyObject* Ping_get_average(PingObject* self);
PyObject* Ping_get_stddev(PingObject* self);
PyObject* Ping_get_loss(PingObject* self);

/* sensors */
typedef struct {
	PyObject_HEAD
	const sensors_chip_name* chip;
	const sensors_feature* feature;
} SensorObject;

PyTypeObject SensorType;

void Sensor_dealloc(SensorObject* self);
PyObject* Sensor_new(PyTypeObject* type, PyObject* args, PyObject* kwds);
int Sensor_init(SensorObject* self, PyObject* args, PyObject* kwds);
PyObject* Sensor_get_label(SensorObject* self);
PyObject* Sensor_get_name(SensorObject* self);
PyObject* Sensor_get_type(SensorObject* self);
PyObject* Sensor_get_bus(SensorObject* self);
PyObject* Sensor_return_value(SensorObject* sensor, sensors_subfeature_type subfeature_type);
PyObject* Sensor_get_value(SensorObject* self);
PyObject* Sensor_get_critical(SensorObject* self);
PyObject* Sensor_get_maximum(SensorObject* self);
PyObject* Sensor_get_minimum(SensorObject* self);
PyObject* Sensor_get_high(SensorObject* self);

PyObject* _collecty_sensors_init();
PyObject* _collecty_sensors_cleanup();
PyObject* _collecty_get_detected_sensors(PyObject* o, PyObject* args);

/* utils */
int _collecty_mountpoint_is_virtual(const struct mntent* mp);
PyObject* _collecty_get_mountpoints();
