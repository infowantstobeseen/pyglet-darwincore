
"""VERSION_10_0

AGL functions for OS X 10.0 and later.
"""

import ctypes as _ctypes
from ctypes.util import find_library as _find_library

_path = _find_library('AGL')
if not _path:
    raise ImportError('AGL framework not found')
_agl = _ctypes.cdll.LoadLibrary(_path)

def _get_function(name, argtypes, rtype):
    try:
        func = getattr(_agl, name)
        func.argtypes = argtypes
        func.restype = rtype
        return func
    except AttributeError, e:
        raise ImportError(e)

AGL_ALL_RENDERERS = 1
AGL_BUFFER_SIZE = 2
AGL_LEVEL = 3
AGL_RGBA = 4
AGL_DOUBLEBUFFER = 5
AGL_STEREO = 6
AGL_AUX_BUFFERS = 7
AGL_RED_SIZE = 8
AGL_GREEN_SIZE = 9
AGL_BLUE_SIZE = 10
AGL_ALPHA_SIZE = 11
AGL_DEPTH_SIZE = 12
AGL_STENCIL_SIZE = 13
AGL_ACCUM_RED_SIZE = 14
AGL_ACCUM_GREEN_SIZE = 15
AGL_ACCUM_BLUE_SIZE = 16
AGL_ACCUM_ALPHA_SIZE = 17
AGL_PIXEL_SIZE = 50
AGL_MINIMUM_POLICY = 51
AGL_MAXIMUM_POLICY = 52
AGL_OFFSCREEN = 53
AGL_FULLSCREEN = 54
AGL_SAMPLE_BUFFERS_ARB = 55
AGL_SAMPLES_ARB = 56
AGL_AUX_DEPTH_STENCIL = 57
AGL_RENDERER_ID = 70
AGL_SINGLE_RENDERER = 71
AGL_NO_RECOVERY = 72
AGL_ACCELERATED = 73
AGL_CLOSEST_POLICY = 74
AGL_ROBUST = 75
AGL_BACKING_STORE = 76
AGL_MP_SAFE = 78
AGL_WINDOW = 80
AGL_MULTISCREEN = 81
AGL_VIRTUAL_SCREEN = 82
AGL_COMPLIANT = 83
AGL_SWAP_RECT = 200
AGL_BUFFER_RECT = 202
AGL_SWAP_LIMIT = 203
AGL_COLORMAP_TRACKING = 210
AGL_COLORMAP_ENTRY = 212
AGL_RASTERIZATION = 220
AGL_SWAP_INTERVAL = 222
AGL_STATE_VALIDATION = 230
AGL_BUFFER_NAME = 231
AGL_ORDER_CONTEXT_TO_FRONT = 232
AGL_CONTEXT_SURFACE_ID = 233
AGL_CONTEXT_DISPLAY_ID = 234
AGL_SURFACE_ORDER = 235
AGL_SURFACE_OPACITY = 236
AGL_CLIP_REGION = 254
AGL_FS_CAPTURE_SINGLE = 255
AGL_FORMAT_CACHE_SIZE = 501
AGL_CLEAR_FORMAT_CACHE = 502
AGL_RETAIN_RENDERERS = 503
AGL_RGB8_BIT = 0x00000001
AGL_RGB8_A8_BIT = 0x00000002
AGL_BGR233_BIT = 0x00000004
AGL_BGR233_A8_BIT = 0x00000008
AGL_RGB332_BIT = 0x00000010
AGL_RGB332_A8_BIT = 0x00000020
AGL_RGB444_BIT = 0x00000040
AGL_ARGB4444_BIT = 0x00000080
AGL_RGB444_A8_BIT = 0x00000100
AGL_RGB555_BIT = 0x00000200
AGL_ARGB1555_BIT = 0x00000400
AGL_RGB555_A8_BIT = 0x00000800
AGL_RGB565_BIT = 0x00001000
AGL_RGB565_A8_BIT = 0x00002000
AGL_RGB888_BIT = 0x00004000
AGL_ARGB8888_BIT = 0x00008000
AGL_RGB888_A8_BIT = 0x00010000
AGL_RGB101010_BIT = 0x00020000
AGL_ARGB2101010_BIT = 0x00040000
AGL_RGB101010_A8_BIT = 0x00080000
AGL_RGB121212_BIT = 0x00100000
AGL_ARGB12121212_BIT = 0x00200000
AGL_RGB161616_BIT = 0x00400000
AGL_ARGB16161616_BIT = 0x00800000
AGL_INDEX8_BIT = 0x20000000
AGL_INDEX16_BIT = 0x40000000
AGL_NO_ERROR = 0
AGL_BAD_ATTRIBUTE = 10000
AGL_BAD_PROPERTY = 10001
AGL_BAD_PIXELFMT = 10002
AGL_BAD_RENDINFO = 10003
AGL_BAD_CONTEXT = 10004
AGL_BAD_DRAWABLE = 10005
AGL_BAD_GDEV = 10006
AGL_BAD_STATE = 10007
AGL_BAD_VALUE = 10008
AGL_BAD_MATCH = 10009
AGL_BAD_ENUM = 10010
AGL_BAD_OFFSCREEN = 10011
AGL_BAD_FULLSCREEN = 10012
AGL_BAD_WINDOW = 10013
AGL_BAD_POINTER = 10014
AGL_BAD_MODULE = 10015
AGL_BAD_ALLOC = 10016
aglChoosePixelFormat = _get_function('aglChoosePixelFormat', [_ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_void_p)
aglDestroyPixelFormat = _get_function('aglDestroyPixelFormat', [_ctypes.c_void_p], None)
aglNextPixelFormat = _get_function('aglNextPixelFormat', [_ctypes.c_void_p], _ctypes.c_void_p)
aglDescribePixelFormat = _get_function('aglDescribePixelFormat', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_ubyte)
aglQueryRendererInfo = _get_function('aglQueryRendererInfo', [_ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int], _ctypes.c_void_p)
aglDestroyRendererInfo = _get_function('aglDestroyRendererInfo', [_ctypes.c_void_p], None)
aglNextRendererInfo = _get_function('aglNextRendererInfo', [_ctypes.c_void_p], _ctypes.c_void_p)
aglDescribeRenderer = _get_function('aglDescribeRenderer', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_ubyte)
aglCreateContext = _get_function('aglCreateContext', [_ctypes.c_void_p, _ctypes.c_void_p], _ctypes.c_void_p)
aglDestroyContext = _get_function('aglDestroyContext', [_ctypes.c_void_p], _ctypes.c_ubyte)
aglCopyContext = _get_function('aglCopyContext', [_ctypes.c_void_p, _ctypes.c_void_p, _ctypes.c_uint], _ctypes.c_ubyte)
aglUpdateContext = _get_function('aglUpdateContext', [_ctypes.c_void_p], _ctypes.c_ubyte)
aglSetCurrentContext = _get_function('aglSetCurrentContext', [_ctypes.c_void_p], _ctypes.c_ubyte)
aglGetCurrentContext = _get_function('aglGetCurrentContext', [], _ctypes.c_void_p)
aglSetDrawable = _get_function('aglSetDrawable', [_ctypes.c_void_p, _ctypes.c_void_p], _ctypes.c_ubyte)
aglSetOffScreen = _get_function('aglSetOffScreen', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_void_p], _ctypes.c_ubyte)
aglSetFullScreen = _get_function('aglSetFullScreen', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], _ctypes.c_ubyte)
aglGetDrawable = _get_function('aglGetDrawable', [_ctypes.c_void_p], _ctypes.c_void_p)
aglSetVirtualScreen = _get_function('aglSetVirtualScreen', [_ctypes.c_void_p, _ctypes.c_int], _ctypes.c_ubyte)
aglGetVirtualScreen = _get_function('aglGetVirtualScreen', [_ctypes.c_void_p], _ctypes.c_int)
aglGetVersion = _get_function('aglGetVersion', [_ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int)], None)
aglConfigure = _get_function('aglConfigure', [_ctypes.c_uint, _ctypes.c_uint], _ctypes.c_ubyte)
aglSwapBuffers = _get_function('aglSwapBuffers', [_ctypes.c_void_p], None)
aglEnable = _get_function('aglEnable', [_ctypes.c_void_p, _ctypes.c_uint], _ctypes.c_ubyte)
aglDisable = _get_function('aglDisable', [_ctypes.c_void_p, _ctypes.c_uint], _ctypes.c_ubyte)
aglIsEnabled = _get_function('aglIsEnabled', [_ctypes.c_void_p, _ctypes.c_uint], _ctypes.c_ubyte)
aglSetInteger = _get_function('aglSetInteger', [_ctypes.c_void_p, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_ubyte)
aglGetInteger = _get_function('aglGetInteger', [_ctypes.c_void_p, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_ubyte)
aglUseFont = _get_function('aglUseFont', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.c_ubyte, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], _ctypes.c_ubyte)
aglGetError = _get_function('aglGetError', [], _ctypes.c_uint)
aglResetLibrary = _get_function('aglResetLibrary', [], None)
aglChoosePixelFormat = _get_function('aglChoosePixelFormat', [_ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_void_p)
aglDestroyPixelFormat = _get_function('aglDestroyPixelFormat', [_ctypes.c_void_p], None)
aglNextPixelFormat = _get_function('aglNextPixelFormat', [_ctypes.c_void_p], _ctypes.c_void_p)
aglDescribePixelFormat = _get_function('aglDescribePixelFormat', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_ubyte)
aglQueryRendererInfo = _get_function('aglQueryRendererInfo', [_ctypes.POINTER(_ctypes.c_void_p), _ctypes.c_int], _ctypes.c_void_p)
aglDestroyRendererInfo = _get_function('aglDestroyRendererInfo', [_ctypes.c_void_p], None)
aglNextRendererInfo = _get_function('aglNextRendererInfo', [_ctypes.c_void_p], _ctypes.c_void_p)
aglDescribeRenderer = _get_function('aglDescribeRenderer', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_ubyte)
aglCreateContext = _get_function('aglCreateContext', [_ctypes.c_void_p, _ctypes.c_void_p], _ctypes.c_void_p)
aglDestroyContext = _get_function('aglDestroyContext', [_ctypes.c_void_p], _ctypes.c_ubyte)
aglCopyContext = _get_function('aglCopyContext', [_ctypes.c_void_p, _ctypes.c_void_p, _ctypes.c_uint], _ctypes.c_ubyte)
aglUpdateContext = _get_function('aglUpdateContext', [_ctypes.c_void_p], _ctypes.c_ubyte)
aglSetCurrentContext = _get_function('aglSetCurrentContext', [_ctypes.c_void_p], _ctypes.c_ubyte)
aglGetCurrentContext = _get_function('aglGetCurrentContext', [], _ctypes.c_void_p)
aglSetDrawable = _get_function('aglSetDrawable', [_ctypes.c_void_p, _ctypes.c_void_p], _ctypes.c_ubyte)
aglSetOffScreen = _get_function('aglSetOffScreen', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_void_p], _ctypes.c_ubyte)
aglSetFullScreen = _get_function('aglSetFullScreen', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], _ctypes.c_ubyte)
aglGetDrawable = _get_function('aglGetDrawable', [_ctypes.c_void_p], _ctypes.c_void_p)
aglSetVirtualScreen = _get_function('aglSetVirtualScreen', [_ctypes.c_void_p, _ctypes.c_int], _ctypes.c_ubyte)
aglGetVirtualScreen = _get_function('aglGetVirtualScreen', [_ctypes.c_void_p], _ctypes.c_int)
aglGetVersion = _get_function('aglGetVersion', [_ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_int)], None)
aglConfigure = _get_function('aglConfigure', [_ctypes.c_uint, _ctypes.c_uint], _ctypes.c_ubyte)
aglSwapBuffers = _get_function('aglSwapBuffers', [_ctypes.c_void_p], None)
aglEnable = _get_function('aglEnable', [_ctypes.c_void_p, _ctypes.c_uint], _ctypes.c_ubyte)
aglDisable = _get_function('aglDisable', [_ctypes.c_void_p, _ctypes.c_uint], _ctypes.c_ubyte)
aglIsEnabled = _get_function('aglIsEnabled', [_ctypes.c_void_p, _ctypes.c_uint], _ctypes.c_ubyte)
aglSetInteger = _get_function('aglSetInteger', [_ctypes.c_void_p, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_ubyte)
aglGetInteger = _get_function('aglGetInteger', [_ctypes.c_void_p, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_ubyte)
aglUseFont = _get_function('aglUseFont', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.c_ubyte, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int], _ctypes.c_ubyte)
aglGetError = _get_function('aglGetError', [], _ctypes.c_uint)
aglResetLibrary = _get_function('aglResetLibrary', [], None)
