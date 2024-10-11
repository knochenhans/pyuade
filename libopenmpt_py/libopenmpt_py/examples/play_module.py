import os

from libopenmpt_py import libopenmpt
from io import BytesIO
import ctypes
import warnings
import os
import pyaudio


def log_callback(user_data, level, message):
    pass


def error_callback(user_data, message):
    pass


def libopenmpt_example_print_error(
    func_name: ctypes.c_char, mod_err: int, mod_err_str: ctypes.c_char | None
):
    if not func_name:
        func_name = ctypes.c_char(b"unknown function")

    if mod_err == libopenmpt.OPENMPT_ERROR_OUT_OF_MEMORY:
        mod_err_str = libopenmpt.openmpt_error_string(mod_err)
        if not mod_err_str:
            warnings.warn("Error: OPENMPT_ERROR_OUT_OF_MEMORY")
        else:
            warnings.warn(f"Error: {mod_err_str}")
            mod_err_str = None
    else:
        if not mod_err_str:
            mod_err_str = libopenmpt.openmpt_error_string(mod_err)
            if not mod_err_str:
                warnings.warn(f"Error: {func_name} failed.")
            else:
                warnings.warn(f"Error: {func_name} failed: {mod_err_str}")
            libopenmpt.openmpt_free_string(mod_err_str)
            mod_err_str = None


openmpt_log_func = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
)
openmpt_error_func = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
)
load_mod = libopenmpt.openmpt_module_create_from_memory2

SAMPLERATE = 48000
BUFFERSIZE = 480

buffer = (ctypes.c_int16 * (BUFFERSIZE * 2))()

filename = os.path.join(os.path.dirname(__file__), "xrtd_-_osc.xm")

with open(filename, "rb") as f:
    module_data = f.read()
    module_size = len(module_data)

ctls = ctypes.c_void_p()
error = ctypes.c_int()
error_message = ctypes.c_char_p()

mod = load_mod(
    module_data,  # const void * filedata
    module_size,  # size_t filesize
    openmpt_log_func(log_callback),  # openmpt_log_func logfunc
    None,  # void * loguser
    openmpt_error_func(error_callback),  # openmpt_error_func errfunc
    None,  # void * erruser
    ctypes.byref(error),  # int * error
    ctypes.byref(error_message),  # const char ** error_message
    ctls,  # const openmpt_module_initial_ctl * ctls
)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=2, rate=SAMPLERATE, output=True)

while True:
    libopenmpt.openmpt_module_error_clear(mod)
    count = libopenmpt.openmpt_module_read_interleaved_stereo(
        mod, SAMPLERATE, BUFFERSIZE, buffer
    )
    mod_err = libopenmpt.openmpt_module_error_get_last(mod)
    mod_err_str = libopenmpt.openmpt_module_error_get_last_message(mod)
    if mod_err != libopenmpt.OPENMPT_ERROR_OK:
        libopenmpt_example_print_error(
            ctypes.c_char(b"openmpt_module_read_interleaved_stereo()"),
            mod_err,
            mod_err_str,
        )
        libopenmpt.openmpt_free_string(mod_err_str)
        mod_err_str = None
    if count == 0:
        break
    stream.write(bytes(buffer))

stream.stop_stream()
stream.close()
p.terminate()
