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
option | value
------------ | -------------
-s| required: path/to/source
-d | required: path/to/destination. If the destination path exists it will prepend "co.py_" to the copy
-x | optional: switch for xxHash instead of md5
-m | optional: stores the hashcodes in a sidecar .json file
-r | optional: copies all the files/folders in the source path
-hib | optional: uses a higher buffer size (64 MiB)
## License
There ain't any. Do with this code whatever you want.
