#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes
import ctypes.util
import sys

if sys.platform == 'windows':
    import OpenGL.WGL
    def get_function(name, argtypes, rtype):
        try:
            fargs = (rtype,) + tuple(argtypes)
            ftype = FUNCTYPE(*fargs)
            address = OpenGL.WGL.wglGetEntryPoint(name)
            return ftype.from_address(address)
        except AttributeError, e:
            raise ImportError(e)

elif sys.platform == 'darwin':
    path = ctypes.util.find_library('OpenGL')
    if not path:
        raise ImportError('OpenGL framework not found')
    _gl = ctypes.cdll.LoadLibrary(path)
    def get_function(name, argtypes, rtype):
        try:
            func = getattr(_gl, name)
            func.argtypes = argtypes
            func.restype = rtype
            return func
        except AttributeError, e:
            raise ImportError(e)

else:
    try:
        # For OpenGL-ctypes
        from OpenGL import platform
        _gl = _platform.OpenGL
    except ImportError:
        # For PyOpenGL
        _gl = ctypes.cdll.LoadLibrary('libGL.so')
    def get_function(name, argtypes, rtype):
        try:
            func = getattr(_gl, name)
            func.argtypes = argtypes
            func.restype = rtype
            return func
        except AttributeError, e:
            raise ImportError(e)
 
# No ptrdiff_t in ctypes, discover it
for t in (ctypes.c_int16, ctypes.c_int32, ctypes.c_int64):
    if ctypes.sizeof(t) == ctypes.sizeof(ctypes.c_size_t):
        c_ptrdiff_t = t
