# libopenmpt_py

Python bindings for libopenmpt. Libopenmpt is a "cross-platform C/C++ library to decode tracked music files".
The docs can be found here: <https://lib.openmpt.org/doc/>
The bindings are based on the documentation here specifically: <https://lib.openmpt.org/doc/group__libopenmpt__c.html>.

`xrtd_-_osc.xm`, the XM file used in the examples, can be found at <https://modarchive.org/index.php?request=view_by_moduleid&query=199249>.

NOTE: Line 20 of libopenmpt.py says `LIBOPENMPT = ctypes.cdll.LoadLibrary("libopenmpt_binaries/bin/x86/libopenmpt.dll")`. You should change the library location to fit the binary for your CPU architecture.
