#!/usr/bin/env python

# npk format
# ---
# 0-4  : '\x1e\xf1\xd0\xba'
# 4-8  : len(data - 8) ===> The size of the package
# 8-14 : '\x01\x00 \x00\x00\x00'
# 14-30: description ===> 16 chars to put a short name
# 30-34: ?? | ==> version #1 - used in this header again (revision, 'f' (102), minor, major)
# 34-38: ?? | ==> version #2 - used in the data part (epoch time of package build)
#           |  Actualy seems like header[30:42] == each_data_header[12:24]...
#           |  Both appear as integers in /var/pdb/.../version
# 38-42: 0
# 42-46: 0
# 46-48: 16
# 48-50: 4 |
# 50-52: 0 | ==> Maybe int size of the architecture identifier that follows
# 52-56: "i386"
# 56-58: 2
# 58-62: long description size ===> how many chars follow
# 62-x : long description text
#   +24: '\x03\x00"\x00\x00\x00\x01\x00system\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
#   +8 : '2f\t\x02\x00\x00\x00\x00' |
#   +8 : '2f\t\x02\x00\x00\x00\x00' | ==> two same headers (separators?)
#                                         first 4 like header[30:34]
#                                         last 4 always 0
# 
# what follows are headers of 1 short (type) and 1 int (size):
# type 7, 8: some kind of script
# type 4: data
# 
# the content is directly after the header
# 
# in case of data it is commpressed with zlib
# 
# uncompressed data has 30 byte headers:
# 
# 0-1  : permissions: 237 is executable (755), 164 is non executable (644) |
# 1-2  : file type: 65 dir, 129 file                                       | ==> ST_MODE from stat()
# 2-4  : 0 - could be user/group
# 4-8  : 0 - could be user/group
# 8-12 : last modification time (ST_MTIME) as reported by stat()
# 12-24: version stuff and a 0 (see above...)
# 24-28: data size
# 28-30: file name size
# 
# then comes the file name and after that the data

import sys
import zlib
import os

from struct import pack, unpack
from time import ctime

def parse_npk(filename):

	f = open(filename, "r")
	data = f.read()
	f.close()

	if data[10] == "$":
		# Switch to newer npk format
		print "Version 6 npk reader"

		header = data[:66]
		dsize = unpack("I", header[62:66])[0]	# Description size
		header += data[66:66+dsize+40]

		
		print repr(header[38:58])
		print "Magic:", repr(header[0:4]), "should be:", repr('\x1e\xf1\xd0\xba')
		print "Size after this:", unpack("I", header[4:8])[0], "Header size:", len(header), "Data size:", len(data)
		print "Unknown stuff:", repr(header[8:14]), "should be:", repr('\x01\x00 \x00\x00\x00')
		print "Short description:", header[14:30]
		print "Revision, unknown, Minor, Major:", repr(header[30:34]), unpack("BBBB", header[30:34])
		print "Build time:", repr(header[34:38]), ctime(unpack("I", header[34:38])[0])
		print "Another number:", repr(header[38:42])
		print "Some other numbers:", unpack("IIHHH", header[42:56]), "should be: (0, 2, 16, 4, 0)"
		print "Architecture:", header[56:60]
		print "Another number:", unpack("H", header[60:62]), "should be: (2,)"
		print "Long description:", repr(header[66:66+dsize])
#		print "Next 24 chars:", repr(header[62+dsize:62+dsize+24])
#		print "    should be:", repr('\x03\x00"\x00\x00\x00\x01\x00system\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
#		print "Separators:", repr(header[62+dsize+24:62+dsize+32]), repr(header[62+dsize+32:62+dsize+40])
#		print "   first 4:", unpack("BBBB",header[62+dsize+24:62+dsize+28]), unpack("BBBB",header[62+dsize+32:62+dsize+36])
#		print ""

		data = data[66+dsize:]
	else:
		# Older npk format
		print "Version 5 npk reader"
		header = data[:62]
		dsize = unpack("I", header[58:62])[0]	# Description size
		header += data[62:62+dsize+40]

		print repr(header[38:58])
		print "Magic:", repr(header[0:4]), "should be:", repr('\x1e\xf1\xd0\xba')
		print "Size after this:", unpack("I", header[4:8])[0], "Header size:", len(header), "Data size:", len(data)
		print "Unknown stuff:", repr(header[8:14]), "should be:", repr('\x01\x00 \x00\x00\x00')
		print "Short description:", header[14:30]
		print "Revision, unknown, Minor, Major:", repr(header[30:34]), unpack("BBBB", header[30:34])
		print "Build time:", repr(header[34:38]), ctime(unpack("I", header[34:38])[0])
		print "Some other numbers:", unpack("IIHHH", header[38:52]), "should be: (0, 0, 16, 4, 0)"
		print "Architecture:", header[52:56]
		print "Another number:", unpack("H", header[56:58]), "should be: (2,)"
		print "Long description:", repr(header[62:62+dsize])
#		print "Next 24 chars:", repr(header[62+dsize:62+dsize+24])
#		print "    should be:", repr('\x03\x00"\x00\x00\x00\x01\x00system\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
#		print "Separators:", repr(header[62+dsize+24:62+dsize+32]), repr(header[62+dsize+32:62+dsize+40])
#		print "   first 4:", unpack("BBBB",header[62+dsize+24:62+dsize+28]), unpack("BBBB",header[62+dsize+32:62+dsize+36])
#		print ""

	res=[]
	while len(data)>6:
		type = unpack("H", data[:2])[0]
		size = unpack("I", data[2:6])[0]
		print "Found data of type:", type, "size:", size
		contents = data[6:6+size]
		#print contents
		if type == 3:
			print "   Contents (system):", repr(contents)
		if type == 4:
			contents = zlib.decompress(contents)
			print "   Uncompressing data..."
		if type == 7:
			print "   Contents (oninstall):", repr(contents)
		if type == 8:
			print "   Contents (onuninstall):", repr(contents)
		if type == 21:
			print "   Squash File System"
		res.append({"type": type, "size": size, "contents": contents})
		data = data[6+size:]
	print ""

	print "Returning the raw header and the rest of the file (each part in a list)"
	print ""

	return header, res

def parse_data(data):
	res = []
	while len(data)>30:
		header = data[:30]
		dsize = unpack("I", header[24:28])[0]
		fsize = unpack("H", header[28:30])[0]
		if len(data) - 30 - fsize - dsize < 0:
			dsize = len(data) - 30 - fsize
		fstuff = data[30:30+fsize]
		dstuff = data[30+fsize:30+fsize+dsize]
		res.append({"header": header, "file": fstuff, "data": dstuff})
		data = data[30+fsize+dsize:]
	return res

if __name__ == "__main__":
	if len(sys.argv) > 1:
		for i in sys.argv[1:]:
			header, res = parse_npk(i)
			for j in res:
				if j["type"] == 21:
					print "SquashFS found in package, extract 'squashfs' by using unsquashfs."
					f = open("squashfs", "w")
					f.write(j["contents"])
					f.close()
				if j["type"] == 4:
					print "Files in package:"
					data = parse_data(j["contents"])
					for k in data:
						perm, type, z1, z2, tim = unpack("BBHII", k["header"][:12])
						if type == 65:
							type = "dir"
							if not os.access(k["file"], os.F_OK):
								os.makedirs(k["file"])
						if type == 129:
							type = "fil"
							f = open(k["file"], "w")
							f.write(k["data"])
							f.close()
							os.chmod(k["file"], int(perm))
						if type == 161:
							type = "sym"
							os.symlink(k["data"],k["file"])
							# os.chmod(k["file"], int(perm))
						if perm == 164:
							perm = "nx"
						if perm == 237:
							perm = "ex"
						print type, perm, k["file"], tim

