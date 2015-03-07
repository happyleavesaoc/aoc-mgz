from collections import deque
from construct import Adapter, Subconstruct, Construct
import struct
import zlib

class ZlibCompressor():
	"""Decompress via zlib"""
	def decode(self, d):
		return zlib.decompressobj().decompress('x\x9c' + d)

class TimeSecAdapter(Adapter):
	"""Conversion to readable time"""
	def _decode(self, time, ctx):
		time *= 1000
		hour = time/1000/3600
		minute = (time/1000/60) % 60
		second = (time/1000) % 60
		return str(hour).zfill(2)+":"+str(minute).zfill(2)+":"+str(second).zfill(2)

class BoolAdapter(Adapter):
	"""Bools of with potential padding"""
	def _decode(self, val, ctx):
		return val == 1

class Find(Construct):
	"""Find bytes, and read past them"""
	__slots__ = ["find", "maxLength"]

	def __init__(self, name, find, maxLength):
		Construct.__init__(self, name)
		self.find = find
		self.maxLength = maxLength

	def _parse(self, stream, context):
		start = stream.tell()
		bytes = ""
		if self.maxLength:
			bytes = stream.read(self.maxLength)
		else:
			bytes = stream.read()
		skip = bytes.find(self.find) + len(self.find)
		stream.seek(start + skip)
		return skip

class RepeatUpTo(Subconstruct):
	"""Like RepeatUntil, but doesn't include the last element in the return value"""
	__slots__ = ["find"]

	def __init__(self, find, subcon):
		Subconstruct.__init__(self, subcon)
		self.find = find
		self._clear_flag(self.FLAG_COPY_CONTEXT)
		self._set_flag(self.FLAG_DYNAMIC)

	def _parse(self, stream, context):
		objs = []
		while True:
			start = stream.tell()
			test = stream.read(len(self.find))
			stream.seek(start)
			if test == self.find:
				break
			else:
				subobj = self.subcon._parse(stream, context)
				objs.append(subobj)
		return objs

class GotoObjectsEnd(Construct):
	"""Find the end of a player's objects list

	Necessary since we can't parse objects from a resume game (yet)
	"""
	def __init__(self, name):
		Construct.__init__(self, name)

	def _parse(self, stream, context):
		num_players = context._._.replay.num_players
		start = stream.tell()
		# Have to read everything to be able to use find()
		bytes = stream.read()
		# Try to find the first marker, a portion of the next player structure
		marker = bytes.find(b"\x16\xc6\x00\x00\x00\x21")
		# If it exists, we're not on the last player yet
		if marker > 0:
			# Backtrack through the player name
			c = 0
			while struct.unpack("<H", bytes[marker-2:marker])[0] != c:
				marker -= 1
				c += 1
			# Backtrack through the rest of the next player structure
			backtrack = 43 + num_players
		# Otherwise, this is the last player
		else:
			# Search for the scenario header
			marker = bytes.find(b"\xf6\x28\x9c\x3f")
			# Backtrack through the achievements and initial structure footer
			backtrack = ((1817 * (num_players - 1)) + 4 + 19)
		# Seek to the position we found
		end = start + marker - backtrack
		stream.seek(end)
		return end