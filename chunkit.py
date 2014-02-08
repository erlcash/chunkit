#!/usr/bin/python

import sys, os, getopt, hashlib, requests, json, collections

def usage ():
	print "Usage:"
	print " "+ sys.argv[0] +" -u [-ncso] <FILE>"
	print " "+ sys.argv[0] +" -d [-o] <FILE>"
	print " "+ sys.argv[0] +" -e [-nc] <FILE>\n"
	print "Options:"
	print " -u\t\t\ttoggle upload mode"
	print " -d\t\t\ttoggle download mode"
	print " -e\t\t\ttoggle edit mode"
	print " -n=NAME\t\tset a name"
	print " -c=COMMENT\t\tset a comment"
	print " -s=N_BYTES\t\tchange a chunk size"
	print " -o=FILE\t\tchange an output file"
	print " -V\t\t\tenable verbose mode"
	print " -h\t\t\tdisplay this help text"
	print " -v\t\t\tdisplay version information"

def version ():
	print sys.argv[0]+" v1.1"

def mode_upload (opts_data, manifest_data):
	
	try:
		fd_in = open (opts_data["input_file"], "rb")
	except IOError as err:
		print opts_data["p"] +" cannot open input file '"+ opts_data["input_file"] +"': "+ err.strerror
		sys.exit (1)

	# Set default value for name in a manifest file
	if manifest_data["name"] == None:
		manifest_data["name"] = os.path.basename (opts_data["input_file"])

	if opts_data["output_file"] == None:
		opts_data["output_file"] = os.path.basename (opts_data["input_file"])+".mf"

	fd_in.seek (0, 2)
	manifest_data["size"] = fd_in.tell ()
	fd_in.seek (0, 0)

	# Calculate checksum
	data = fd_in.read ()
	manifest_data["checksum"] = hashlib.md5 (data).hexdigest ()
	data = None
	fd_in.seek (0, 0)

	if opts_data["verbose"]:
		print "Name: "+manifest_data["name"]
		print "Comment: "+ str (manifest_data["comment"])
		print "Size: "+ str (manifest_data["size"])
		print "Checksum: "+ str (manifest_data["checksum"])

	while True:
		data = fd_in.read (opts_data["chunk_size"])
		
		if not data:
			break;

		res = requests.put ("http://chunk.io/", data)

		if res.status_code != 201:
			print opts_data["p"] +"upload failed (HTTP: "+ str (res.status_code) +")"
			break

		manifest_data["chunks"].append (res.headers["location"])

	if opts_data["verbose"]:
		print "Chunks:"

		for chunk in manifest_data["chunks"]:
			print "  "+chunk

	fd_in.close ()

	fd_out = open (opts_data["output_file"], "w")
	fd_out.write (json.dumps (manifest_data, sort_keys = False, indent = 4))
	fd_out.close ();

def mode_download (opts_data, manifest_data):
	print "downloading..."

def mode_edit (opts_data, manifest_data):
	print "editing..."

def main (argv):
	opts_data = {
		"p": argv[0],
		"mode": None,
		"name": None,
		"comment": None,
		"chunk_size": 3984588,
		"output_file": None,
		"input_file": None,
		"verbose": False
	}

	manifest_data = {
		"name": None,
		"comment": None,
		"size": 0,
		"checksum": None,
		"chunks": []
	}

	if (len (argv) - 1) < 1:
		print argv[0]+" no input file specified. See usage '-h'"
		sys.exit (1)
	
	try:
		opts, args = getopt.getopt (argv[1:], "uden:c:s:o:Vhv")
	except getopt.GetoptError as err:
		usage ()
		sys.exit (1)
	
	for opt, arg in opts:
		if opt == "-u":
			opts_data["mode"] = "upload"
		elif opt == "-d":
			opts_data["mode"] = "download"
		elif opt == "-e":
			opts_data["mode"] = "edit"
		elif opt == "-n":
			opts_data["name"] = arg
		elif opt == "-c":
			opts_data["comment"] = arg
		elif opt == "-s":
			opts_data["chunk_size"] = int (arg)
		elif opt == "-o":
			opts_data["output_file"] = arg
		elif opt == "-V":
			opts_data["verbose"] = True
		elif opt == "-h":
			usage ()
			sys.exit (0)
		elif opt == "-v":
			version ()
			sys.exit (0)
		else:
			print "unknown: "+opt+"-"+arg

	opts_data["input_file"] = argv[-1]

	# Decide what to do based on the mode enabled
	# UPLOAD
	if opts_data["mode"] == "upload":
		mode_upload (opts_data, manifest_data)
	elif opts_data["mode"] == "download":
		mode_download (opts_data, manifest_data)
	elif opts_data["mode"] == "edit":
		mode_edit (opts_data, manifest_data)

	sys.exit (0)

if __name__ == "__main__":
	main (sys.argv);

