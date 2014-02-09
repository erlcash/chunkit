# chunkit

## 1. Description

*chunkit* is a console client interfacing a file hosting service chunk.io
aka 'File upload for hackers'.

## 2. Features

- File upload directly from darkness of your console
- Automatic chunking of large files (chunk.io allows only files up to 50 MB atm)
- Manifest files (*.mf) to easily share data with fellow hackers 

## 3. Usage

*chunkit* supports three run modes: upload, download, edit.

### 3.1 Upload mode

This mode is used to upload a new file on chunk.io. If a file is larger than currently
supported maximum size, the file is automatically chunked and uploaded separately.
When upload is successfull a Manifest file is produced containing metadata (name, comment,
size, checksum) and information how to merge the chunks together.

Upload mode is invoked using an option '-u' followed by a path to a file which ought to be uploaded.
Optionally other options can be specified.

`chunkit -u	[-ncso]	<FILE>`

### 3.2 Download mode

This mode is used to download all chunks and merge them together to create the original file.
In order to do so a Manifest file must be passed to *chunkit* where required metadata are available.
A Manifest file can either be a local file (i.e. /home/johndoe/old_data.mf) or a remote file accessible
via HTTP/HTTPS (i.e. http://example.org/data.mf).

Download mode is invoked using an option '-d' followed by a URI of a Manifest file. 

`chunkit -d	[-o]	<URI>`

### 3.3 Edit mode

This mode is used to update metadata (name, comment) in a Manifest file.

Edit mode is invoked using an option '-e' followed by a path to a Manifest file that ought to be updated.

`chunkit -e	[-nc]	<FILE>`

### 3.4 Options

``` -u			toggle upload mode
 -d			toggle download mode
 -e			toggle edit mode
 -n=NAME	set a name
 -c=COMMENT	set a comment
 -s=BYTES	change a chunk size
 -o=FILE	change an output file
 -f			force overwrite if output file already exists
 -V			enable verbose mode
 -h			display this help text
 -v			display version information

## 4. Installation

Download, unpack, make, run...


