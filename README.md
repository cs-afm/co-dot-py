# co-dot-py
### A little cli tool for moving things around

## Installation

git clone https://github.com/cs-afm/co-dot-py

## Usage

co.py -s SRC -d DST [-x]

-s    path/to/sourceFile
-d    path/to/destinationFile. Careful, it'll overwrite existing files!
-x    optional: switch for xxHash instead of md5

## Dependencies

* Python 3
* xxhash (pip install xxhash/pip3 install xxhash)

## TODO

* Preserve mtime of src
