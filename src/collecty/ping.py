#!/usr/bin/python

from __future__ import division

import array
import math
import os
import random
import select
import socket
import struct
import sys
import time

ICMP_TYPE_ECHO_REPLY = 0
ICMP_TYPE_ECHO_REQUEST = 8
ICMP_MAX_RECV = 2048

MAX_SLEEP = 1000

class PingError(Exception):
	msg = None


class PingResolveError(PingError):
	msg = "Could not resolve hostname"


class Ping(object):
	def __init__(self, destination, timeout=1000, packet_size=56):
		self.destination = self._resolve(destination)
		self.timeout = timeout
		self.packet_size = packet_size

		self.id = os.getpid() & 0xffff # XXX ? Is this a good idea?

		self.seq_number = 0

		# Number of sent packets.
		self.send_count = 0

		# Save the delay of all responses.
		self.times = []

	def run(self, count=None, deadline=None):
		while True:
			delay = self.do()

			self.seq_number += 1

			if count and self.seq_number >= count:
				break

			if deadline and self.total_time >= deadline:
				break

			if delay == None:
				delay = 0

			if MAX_SLEEP > delay:
				time.sleep((MAX_SLEEP - delay) / 1000)

	def do(self):
		s = None
		try:
			# Open a socket for ICMP communication.
			s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))

			# Send one packet.
			send_time = self.send_icmp_echo_request(s)

			# Increase number of sent packets (even if it could not be sent).
			self.send_count += 1

			# If the packet could not be sent, we may stop here.
			if send_time is None:
				return

			# Wait for the reply.
			receive_time, packet_size, ip, ip_header, icmp_header = self.receive_icmp_echo_reply(s)

		finally:
			# Close the socket.
			if s:
				s.close()

		# If a packet has been received...
		if receive_time:
			delay = (receive_time - send_time) * 1000
			self.times.append(delay)

			return delay

	def send_icmp_echo_request(self, s):
		# Header is type (8), code (8), checksum (16), id (16), sequence (16)
		checksum = 0

		# Create a header with checksum == 0.
		header = struct.pack("!BBHHH", ICMP_TYPE_ECHO_REQUEST, 0,
			checksum, self.id, self.seq_number)

		# Get some bytes for padding.
		padding = os.urandom(self.packet_size)

		# Calculate the checksum for header + padding data.
		checksum = self._calculate_checksum(header + padding)

		# Rebuild the header with the new checksum.
		header = struct.pack("!BBHHH", ICMP_TYPE_ECHO_REQUEST, 0,
			checksum, self.id, self.seq_number)

		# Build the packet.
		packet = header + padding

		# Save the time when the packet has been sent.
		send_time = time.time()

		# Send the packet.
		try:
			s.sendto(packet, (self.destination, 0))
		except socket.error, (errno, msg):
			if errno == 1: # Operation not permitted
				# The packet could not be sent, probably because of
				# wrong firewall settings.
				return

		return send_time

	def receive_icmp_echo_reply(self, s):
		timeout = self.timeout / 1000.0

		# Wait until the reply packet arrived or until we hit timeout.
		while True:
			select_start = time.time()

			inputready, outputready, exceptready = select.select([s], [], [], timeout)
			select_duration = (time.time() - select_start)

			if inputready == []: # Timeout
				return None, 0, 0, 0, 0

			# Save the time when the packet has been received.
			receive_time = time.time()

			# Read the packet from the socket.
			packet_data, address = s.recvfrom(ICMP_MAX_RECV)

			# Parse the ICMP header.
			icmp_header = self._header2dict(
				["type", "code", "checksum", "packet_id", "seq_number"],
				"!BBHHH", packet_data[20:28]
			)

			# This is the reply to our packet if the ID matches.
			if icmp_header["packet_id"] == self.id:
				# Parse the IP header.
				ip_header = self._header2dict(
					["version", "type", "length", "id", "flags",
					"ttl", "protocol", "checksum", "src_ip", "dst_ip"],
					"!BBHHHBBHII", packet_data[:20]
				)

				packet_size = len(packet_data) - 28
				ip = socket.inet_ntoa(struct.pack("!I", ip_header["src_ip"]))

				return receive_time, packet_size, ip, ip_header, icmp_header

			# Check if the timeout has already been hit.
			timeout = timeout - select_duration
			if timeout <= 0:
				return None, 0, 0, 0, 0

	def _header2dict(self, names, struct_format, data):
		"""
			Unpack tghe raw received IP and ICMP header informations to a dict
		"""
		unpacked_data = struct.unpack(struct_format, data)
		return dict(zip(names, unpacked_data))

	def _calculate_checksum(self, source_string):
		if len(source_string) % 2:
			source_string += "\x00"

		converted = array.array("H", source_string)
		if sys.byteorder == "big":
			converted.byteswap()

		val = sum(converted)

		# Truncate val to 32 bits (a variance from ping.c, which uses signed
		# integers, but overflow is unlinkely in ping).
		val &= 0xffffffff

		# Add high 16 bits to low 16 bits.
		val = (val >> 16) + (val & 0xffff)

		# Add carry from above (if any).
		val += (val >> 16)

		# Invert and truncate to 16 bits.
		answer = ~val & 0xffff

		return socket.htons(answer)

	def _resolve(self, host):
		"""
			Resolve host.
		"""
		if self._is_valid_ipv4_address(host):
			return host

		try:
			return socket.gethostbyname(host)
		except socket.gaierror as e:
			if e.errno == -3:
				raise PingResolveError

			raise

	def _is_valid_ipv4_address(self, addr):
		"""
			Check addr to be a valid IPv4 address.
		"""
		parts = addr.split(".")

		if not len(parts) == 4:
			return False

		for part in parts:
			try:
				number = int(part)
			except ValueError:
				return False

			if number > 255:
				return False

		return True

	@property
	def receive_count(self):
		"""
			The number of received packets.
		"""
		return len(self.times)

	@property
	def total_time(self):
		"""
			The total time of all roundtrips.
		"""
		try:
			return sum(self.times)
		except ValueError:
			return

	@property
	def min_time(self):
		"""
			The smallest roundtrip time.
		"""
		try:
			return min(self.times)
		except ValueError:
			return

	@property
	def max_time(self):
		"""
			The biggest roundtrip time.
		"""
		try:
			return max(self.times)
		except ValueError:
			return

	@property
	def avg_time(self):
		"""
			Calculate the average response time.
		"""
		try:
			return self.total_time / self.receive_count
		except ZeroDivisionError:
			return

	@property
	def variance(self):
		"""
			Calculate the variance of all roundtrips.
		"""
		if self.avg_time is None:
			return

		var = 0

		for t in self.times:
			var += (t - self.avg_time) ** 2

		var /= self.receive_count
		return var

	@property
	def stddev(self):
		"""
			Standard deviation of all roundtrips.
		"""
		return math.sqrt(self.variance)

	@property
	def loss(self):
		"""
			Outputs the percentage of dropped packets.
		"""
		dropped = self.send_count - self.receive_count

		return dropped / self.send_count


if __name__ == "__main__":
	p = Ping("ping.ipfire.org")
	p.run(count=5)

	print "Min/Avg/Max/Stddev: %.2f/%.2f/%.2f/%.2f" % \
		(p.min_time, p.avg_time, p.max_time, p.stddev)
	print "Sent/Recv/Loss: %d/%d/%.2f" % (p.send_count, p.receive_count, p.loss)
