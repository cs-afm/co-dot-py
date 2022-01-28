# co-dot-py
A little cli tool for moving things around.
## Installation
```git clone https://github.com/cs-afm/co-dot-py```
### Dependencies
* Python 3
* xxhash (```pip[3] install xxhash```)
## Usage
```[python/python3] co.py [OPTIONS] -s $SOURCE -d $DESTINATION```
### Options
option | value | required
------------ | ------------- | -------------
-s| path/to/source (can be a file or a directory) | yes
-d | path/to/destination (must be a directory). In case of filename clash co.py will prepend the label "co.py_" to the copy | yes
-x | switch for xxHash instead of md5 | no
-m | stores the hashcodes in a sidecar .json file | no
-r | copies all the files/folders in the source path (if used, the source path must be a directory) | no
-hib | uses a higher buffer size (64 MiB instead of the default 16 Kib) | no
## License
There ain't any. Do with this code whatever you want.
