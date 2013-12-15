#!/usr/bin/env python

DESC_SHORT = 'routing'
DESC_LONG = '\n    Quagga 0.98.6-5\n  '
VER = '\x1bf\t\x02' # 2.9.27

ONINSTALL = '\n    new-libs\n    update-console\n  '
ONUNINSTALL = '\n    dead-libs\n    update-console\n  '

import sys
import zlib
import os
import os.path
import stat

from struct import pack, unpack
from time import time

#BUILD = pack("I", int(time()))
BUILD = '\xf5\xf7\xa8D'

def create_part(type, data):

	if type == 4:
		data = zlib.compress(data)
	dsize = len(data)

	res = ""
	res += pack("H", type)
	res += pack("I", dsize)
	res += data

	return res

def get_contents(directory):
	if not os.path.isdir(directory):
		return
	res = []
	for i in os.listdir(directory):
		ii = os.path.join(directory, i)
		res.append(i)
		if os.path.isdir(ii) and not os.path.islink(ii):
			for j in get_contents(ii):
				res.append(os.path.join(i, j))
	return res

def create_data(directory):
	res = ""
	print directory
	contents = get_contents(directory)
	contents.sort()
	for i in contents:
		ii = os.path.join(directory, i)

		dsize = 0
		if os.path.isdir(ii):
			data = ""
			mode = os.stat(ii)[stat.ST_MODE]
			modestr = pack("H", mode)
			rtype = 65
			perm = 237
		elif os.path.islink(ii):
			data = os.readlink(ii)
			dsize = len(data)
			# type=161(A1), perm=255(FF)
			rtype = 161
			perm = 255
			modestr = '\xFF\xA1'
		else:
			f = open(ii, "r")
			data = f.read()
			f.close()
			dsize = len(data)
			mode = os.stat(ii)[stat.ST_MODE]
			rtype = 129
			if mode & stat.S_IXUSR:
				perm = 237
			else:
				perm = 164

		modestr = pack("BB", perm, rtype)
		
		try:
			tim = os.stat(ii)[stat.ST_MTIME]
		except OSError:
			tim = 0

		header = modestr + '\x00\x00'+ '\x00\x00\x00\x00' + pack("I", tim)
		header += VER + BUILD + '\x00\x00\x00\x00'
		header += pack("I", dsize) + pack("H", len(i))

		res += header + i + data
	return res

# Read files

if len(sys.argv) != 2:
	print "Usage: %s <dir>" % (sys.argv[0])
	sys.exit(2)

data = create_data(sys.argv[1])

# Create parts

parts = ""
parts += create_part(7, ONINSTALL) # Oninstall
parts += create_part(8, ONUNINSTALL) # Onuninstall
parts += create_part(4, data) # Data

# Create header

header = ""
header += '\x1e\xf1\xd0\xba'
header += '\x00\x00\x00\x00' # Size... fill it in later
header += '\x01\x00 \x00\x00\x00'
shortd = DESC_SHORT
while len(shortd) < 16:
	shortd += '\x00'
header += shortd
header += VER
header += BUILD
header += '\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x04\x00\x00\x00i386\x02\x00' # Unknown stuff
header += pack("I", len(DESC_LONG))
header += DESC_LONG
header += '\x03\x00"\x00\x00\x00\x01\x00system\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
header += VER + '\x00\x00\x00\x00'
header += VER + '\x00\x00\x00\x00'

header = header[0:4] + pack("I", len(header) + len(parts) - 8) + header[8:]

f = open(sys.argv[1] + ".npk", "w")
f.write(header)
f.write(parts)
f.close()
