#!/usr/bin/python
#
#  chunkit.py
#  
#  Copyright 2014 Earl Cash <erl@codeward.org>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

import sys, os, getopt, hashlib, requests, json, math, re, random

def usage ():
	print "Usage:"
	print " "+ os.path.basename (sys.argv[0]) +" --upload [-ncso] <FILE>"
	print " "+ os.path.basename (sys.argv[0]) +" --download [-o] <URI>"
	print " "+ os.path.basename (sys.argv[0]) +" --edit [-nc] <FILE>\n"
	print "Options:"
	print " -u, --upload\t\ttoggle upload mode"
	print " -d, --download\t\ttoggle download mode"
	print " -e, --edit\t\ttoggle edit mode"
	print " -n=NAME\t\tset a name"
	print " -c=COMMENT\t\tset a comment"
	print " -S=BYTES\t\tchange a chunk size"
	print " -o=FILE\t\tchange an output file"
	print " -f\t\t\tforce overwrite if output file already exists"
	print " -V\t\t\tenable verbose mode"
	print " -h, --help\t\tdisplay this help text"
	print " -v, --version\t\tdisplay version information"

def version ():
	print os.path.basename (sys.argv[0])+" v1.3-1"

def md5sum (fd):
	if fd.closed:
		return None

	# FIXME: check a mode which was used to open a file descriptor

	current_pos = fd.tell ()
	fd.seek (0, 0)
	data = fd.read ()

	md5sum = hashlib.md5 (data).hexdigest ()
	data = None	

	fd.seek (current_pos, 0)

	return md5sum

#
# Upload mode
#
def mode_upload (opts_data):

	manifest_data = {
		"name": opts_data["name"],
		"comment": opts_data["comment"],
		"size": 0,
		"checksum": None,
		"chunks": []
	}

	try:
		fd_in = open (opts_data["input_file"], "rb")
	except IOError as err:
		print opts_data["p"] +": cannot open input file '"+ opts_data["input_file"] +"': "+ err.strerror
		sys.exit (1)

	# Set default value for name in a manifest file
	if manifest_data["name"] == None:
		manifest_data["name"] = os.path.basename (opts_data["input_file"])

	if opts_data["output_file"] == None:
		opts_data["output_file"] = os.path.basename (opts_data["input_file"])+".mf"

	if os.path.exists (opts_data["output_file"]) and opts_data["dont_overwrite"]:
		print opts_data["p"] +": output file '"+ opts_data["output_file"] +"' already exists. Use '-f' to force overwrite."
		sys.exit (1)

	fd_in.seek (0, 2)
	manifest_data["size"] = fd_in.tell ()
	fd_in.seek (0, 0)

	if opts_data["verbose"]:
		print "Calculating a checksum..."

	# Calculate checksum
	manifest_data["checksum"] = md5sum (fd_in)

	chunks = range (int (math.ceil (float (manifest_data["size"]) / float (opts_data["chunk_size"]))))
	random.shuffle (chunks)

	manifest_data["chunks"] = range (len (chunks)) # initialize an array with dummy values

	chunk_counter = 0
	for chunk_index in chunks:
		fd_in.seek (opts_data["chunk_size"] * chunk_index, 0)

		data = fd_in.read (opts_data["chunk_size"])

		if opts_data["verbose"]:
			print "Uploading a chunk "+ str (chunk_counter + 1) +"/"+ str (len (chunks)) +"..."

		try:
			res = requests.put (opts_data["server"], data)
		except requests.exceptions.ConnectionError:
			print opts_data["p"] +": upload failed (Connection error)"
			sys.exit (1)

		if res.status_code != 201:
			print opts_data["p"] +": upload failed (HTTP: "+ str (res.status_code) +")"
			sys.exit (1)

		manifest_data["chunks"][chunk_index] = res.headers["location"]
		chunk_counter += 1

	fd_in.close ()

	if opts_data["verbose"]:
		print "Done!\n"
		print "Name: "+manifest_data["name"]
		print "Comment: "+ str (manifest_data["comment"])
		print "Size: "+ str (manifest_data["size"])
		print "Checksum: "+ str (manifest_data["checksum"])
		print "Chunks:"

		chunk_counter = 1
		for chunk in manifest_data["chunks"]:
			print "  ["+ str (chunk_counter) +"] "+ chunk
			chunk_counter += 1

	try:
		fd_out = open (opts_data["output_file"], "w")
	except IOError as err:
		print opts_data["p"] +": cannot open output file '"+opts_data["output_file"]+"': "+err.strerror
		sys.exit (1)

	fd_out.write (json.dumps (manifest_data, sort_keys = False, indent = 4))
	fd_out.close ();

	if opts_data["verbose"]:
		print "\nManifest file '"+ opts_data["output_file"] +"' created."

#
# Download mode
#
def mode_download (opts_data):

	is_remote = re.match ("^(http|https)://", opts_data["input_file"])

	if is_remote:

		if opts_data["verbose"]:
			print "Downloading a remote Manifest file '"+ opts_data["input_file"] +"'..."

		try:
			res = requests.get (opts_data["input_file"])
		except requests.exceptions.ConnectionError:
			print opts_data["p"] +": cannot obtain a remote Manifest file '"+ opts_data["input_file"] +"' (Connection failed)"
			sys.exit (1)

		if opts_data["verbose"]:
			print "Done!"

		if res.status_code != 200:
			print opts_data["p"] +": cannot fetch a remote Manifest file '"+ opts_data["input_file"] +"' (HTTP: "+ str (res.status_code) +")"
			sys.exit (1)

		try:
			manifest_data = json.loads (res.content)
		except ValueError:
			print opts_data["p"] +": invalid data in Manifest file: not a JSON string"
			sys.exit (1)
	else:
		# open as regular (local) file
		try:
			fd_in = open (opts_data["input_file"], "rb")
		except IOError as err:
			print opts_data["p"] +": cannot open Manifest file '"+ opts_data["input_file"] +"': "+ err.strerror
			sys.exit (1)

		try:
			manifest_data = json.load (fd_in)
		except ValueError:
			print opts_data["p"] +": invalid data in Manifest file: not a JSON string"
			sys.exit (1)

		fd_in.close ()

	# Perform check of mandatory fields
	if "name" not in manifest_data:
		print opts_data["p"] +": missing data in Manifest file: 'name' not found"
		sys.exit (1)

	if "checksum" not in manifest_data:
		print opts_data["p"] +": missing data in Manifest file: 'checksum' not found"
		sys.exit (1)

	if "chunks" not in manifest_data:
		print opts_data["p"] +": missing data in Manifest file: 'chunks' not found"
		sys.exit (1)

	if opts_data["output_file"] == None:
		opts_data["output_file"] = manifest_data["name"]

	if os.path.exists (opts_data["output_file"]) and opts_data["dont_overwrite"]:
		print opts_data["p"] +": output file '"+ opts_data["output_file"] +"' already exists. Use '-f' to force overwrite."
		sys.exit (1)

	try:
		fd_out = open (opts_data["output_file"], "wb+")
	except IOError as err:
		print opts_data["p"] +": cannot open output file '"+ opts_data["output_file"] +"': "+err.strerror
		sys.exit (1)

	chunk_counter = 0
	for chunk in manifest_data["chunks"]:

		if opts_data["verbose"]:
			print "Downloading a chunk "+ str (chunk_counter + 1) +"/"+ str (len (manifest_data["chunks"])) +"..."

		try:
			res = requests.get (chunk)
		except requests.exceptions.ConnectionError:
			print opts_data["p"] +": cannot obtain a chunk '"+ chunk +"' (Connection error)"
			sys.exit (1)

		if res.status_code != 200:
			print opts_data["p"] +": download failed for '"+ chunk +"' (HTTP: "+ str (res.status_code) +")"
			sys.exit (1)

		fd_out.write (res.content)
		chunk_counter += 1

	if opts_data["verbose"]:
		print "Done!"
		print "Calculating a checksum..."
	
	# Check checksum
	checksum = md5sum (fd_out)
	fd_out.close ()

	if checksum != manifest_data["checksum"]:
		print opts_data["p"] +": invalid checksum"
		sys.exit (1)

	if opts_data["verbose"]:
		print "Checksum matches.\n"
		print "Output file '"+ opts_data["output_file"] +"' created."

#
# Edit mode
#
def mode_edit (opts_data):

	if (opts_data["name"] == None) and (opts_data["comment"] == None):
		print opts_data["p"] +": nothing to edit. Input data not specified."
		sys.exit (1);

	try:
		fd_in = open (opts_data["input_file"], "r+")
	except IOError as err:
		print opts_data["p"] +": cannot open Manifest file '"+ opts_data["input_file"] +"': "+ err.strerror
		sys.exit (1)

	try:
		manifest_data = json.load (fd_in)
	except ValueError:
		print opts_data["p"] +": invalid data in Manifest file: not a JSON string"
		sys.exit (1)

	fd_in.seek (0, 0)

	manifest_data["name"] = opts_data["name"]
	manifest_data["comment"] = opts_data["comment"]

	fd_in.truncate ()
	fd_in.write (json.dumps (manifest_data, sort_keys = False, indent = 4))	
	fd_in.close ()

#
# ... Main ...
#
def main (argv):
	opts_data = {
		"p": os.path.basename (argv[0]),
		"server": "http://chunk.io",
		"mode": None,
		"name": None,
		"comment": None,
		"chunk_size": 31457280,
		"output_file": None,
		"input_file": None,
		"verbose": False,
		"dont_overwrite": True
	}

	try:
		opts, args = getopt.gnu_getopt (argv[1:], "uden:c:s:o:fVhv", ["upload", "download", "edit", "help", "version"])
	except getopt.GetoptError as err:
		usage ()
		sys.exit (1)
	
	for opt, arg in opts:
		if opt in ("-u", "--upload"):
			opts_data["mode"] = "upload"
		elif opt in ("-d", "--download"):
			opts_data["mode"] = "download"
		elif opt in ("-e", "--edit"):
			opts_data["mode"] = "edit"
		elif opt == "-n":
			opts_data["name"] = arg
		elif opt == "-c":
			opts_data["comment"] = arg
		elif opt == "-S":
			opts_data["chunk_size"] = int (arg)
		elif opt == "-o":
			opts_data["output_file"] = arg
		elif opt == "-f":
			opts_data["dont_overwrite"] = False
		elif opt == "-V":
			opts_data["verbose"] = True
		elif opt in ("-h", "--help"):
			usage ()
			sys.exit (0)
		elif opt in ("-v", "--version"):
			version ()
			sys.exit (0)

	if len (args) == 0:
		print opts_data["p"]+": input file not specified. See usage '-h'."
		sys.exit (1)

	opts_data["input_file"] = args[-1]

	# Decide what to do based on the mode enabled
	if opts_data["mode"] == "upload":
		mode_upload (opts_data)
	elif opts_data["mode"] == "download":
		mode_download (opts_data)
	elif opts_data["mode"] == "edit":
		mode_edit (opts_data)
	else:
		print opts_data["p"]+": run mode not specified. See usage '-h'."

	sys.exit (0)

if __name__ == "__main__":
	main (sys.argv);

