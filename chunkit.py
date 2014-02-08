#!/usr/bin/python

import sys, os, getopt, hashlib, requests, json, collections

def usage ():
	print "Usage: "+ sys.argv[0] +" [-ondVhv] <FILE>\n"
	print "Options:"
	print " -o <FILE>\t\tchange name of output (manifest) file"
	print " -s <BYTES>\t\tchunk size in bytes"
	print " -n <NAME>\t\tset a name"
	print " -d <DESCRIPTION>\tset a description"
	print " -V\t\t\tenable verbose mode"
	print " -h\t\t\tdisplay this help text"
	print " -v\t\t\tdisplay version information"

def version ():
	print sys.argv[0]," v1.0"

def main (argv):
	mf_out = ""
	chunk_size = 3984588
	verbose = False
	
	# Data structure of manifest file
	mf_data = collections.OrderedDict ({
		"name": "",
		"description": "",
		"size": 0,
		"checksum": "",
		"chunks": []
	})

	if (len (argv) - 1) < 1:
		print argv[0]+" no input file specified. See usage '-h'"
		sys.exit (1)
	
	try:
		opts, args = getopt.getopt (argv[1:], "o:s:n:d:Vhv")
	except getopt.GetoptError as err:
		usage ()
		sys.exit (1)
	
	for opt, arg in opts:
		if opt == "-o":
			mf_out = arg
		elif opt == "-s":
			chunk_size = int (arg)
		elif opt == "-n":
			mf_data["name"] = arg
		elif opt == "-d":
			mf_data["description"] = arg
		elif opt == "-h":
			usage ()
			sys.exit (0)
		elif opt == "-v":
			version ()
			sys.exit (0)
		elif opt == "-V":
			verbose = True

	f_in = argv[-1]

	try:
		fd_in = open (f_in, "rb")
	except IOError as err:
		print argv[0] +"cannot open input file '"+ f_in +"': "+ err.strerror
		sys.exit (1)

	if len (mf_data["name"]) == 0:
		mf_data["name"] = os.path.basename (f_in)

	if len (mf_out) == 0:
		mf_out = os.path.basename (f_in)+".mf"

	fd_in.seek (0, 2)
	mf_data["size"] = fd_in.tell ()
	fd_in.seek (0, 0)

	# Calculate checksum
	data = fd_in.read ()
	mf_data["checksum"] = hashlib.md5 (data).hexdigest ()
	data = None
	fd_in.seek (0, 0)

	if verbose:	
		print "Name: "+mf_data["name"]
		print "Description: "+mf_data["description"]
		print "Size: "+ str (mf_data["size"])
		print "Checksum: "+mf_data["checksum"]

	while True:
		data = fd_in.read (chunk_size)
		
		if not data:
			break;

		res = requests.put ("http://chunk.io/", data)

		if res.status_code != 201:
			print argv[0] +"upload failed (HTTP: "+ str (res.status_code) +")"
			break

		mf_data["chunks"].append (res.headers["location"])

	if verbose:
		print "Chunks:"

		for chunk in mf_data["chunks"]:
			print "  "+chunk

	fd_in.close ()

	fd_out = open (mf_out, "w")
	fd_out.write (json.dumps (mf_data, sort_keys = False, indent = 4))
	fd_out.close ();

	sys.exit (0)

if __name__ == "__main__":
	main (sys.argv);

