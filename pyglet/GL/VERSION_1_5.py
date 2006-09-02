
"""VERSION_1_5
http://www.opengl.org/documentation/specs/version1.5/glspec15.pdf
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
from pyglet.GL.VERSION_1_4 import *
GL_BUFFER_SIZE = 0x8764
GL_BUFFER_USAGE = 0x8765
GL_QUERY_COUNTER_BITS = 0x8864
GL_CURRENT_QUERY = 0x8865
GL_QUERY_RESULT = 0x8866
GL_QUERY_RESULT_AVAILABLE = 0x8867
GL_ARRAY_BUFFER = 0x8892
GL_ELEMENT_ARRAY_BUFFER = 0x8893
GL_ARRAY_BUFFER_BINDING = 0x8894
GL_ELEMENT_ARRAY_BUFFER_BINDING = 0x8895
GL_VERTEX_ARRAY_BUFFER_BINDING = 0x8896
GL_NORMAL_ARRAY_BUFFER_BINDING = 0x8897
GL_COLOR_ARRAY_BUFFER_BINDING = 0x8898
GL_INDEX_ARRAY_BUFFER_BINDING = 0x8899
GL_TEXTURE_COORD_ARRAY_BUFFER_BINDING = 0x889A
GL_EDGE_FLAG_ARRAY_BUFFER_BINDING = 0x889B
GL_SECONDARY_COLOR_ARRAY_BUFFER_BINDING = 0x889C
GL_FOG_COORDINATE_ARRAY_BUFFER_BINDING = 0x889D
GL_WEIGHT_ARRAY_BUFFER_BINDING = 0x889E
GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING = 0x889F
GL_READ_ONLY = 0x88B8
GL_WRITE_ONLY = 0x88B9
GL_READ_WRITE = 0x88BA
GL_BUFFER_ACCESS = 0x88BB
GL_BUFFER_MAPPED = 0x88BC
GL_BUFFER_MAP_POINTER = 0x88BD
GL_STREAM_DRAW = 0x88E0
GL_STREAM_READ = 0x88E1
GL_STREAM_COPY = 0x88E2
GL_STATIC_DRAW = 0x88E4
GL_STATIC_READ = 0x88E5
GL_STATIC_COPY = 0x88E6
GL_DYNAMIC_DRAW = 0x88E8
GL_DYNAMIC_READ = 0x88E9
GL_DYNAMIC_COPY = 0x88EA
GL_SAMPLES_PASSED = 0x8914
GL_FOG_COORD_SRC = GL_FOG_COORDINATE_SOURCE
GL_FOG_COORD = GL_FOG_COORDINATE
GL_CURRENT_FOG_COORD = GL_CURRENT_FOG_COORDINATE
GL_FOG_COORD_ARRAY_TYPE = GL_FOG_COORDINATE_ARRAY_TYPE
GL_FOG_COORD_ARRAY_STRIDE = GL_FOG_COORDINATE_ARRAY_STRIDE
GL_FOG_COORD_ARRAY_POINTER = GL_FOG_COORDINATE_ARRAY_POINTER
GL_FOG_COORD_ARRAY = GL_FOG_COORDINATE_ARRAY
GL_FOG_COORD_ARRAY_BUFFER_BINDING = GL_FOG_COORDINATE_ARRAY_BUFFER_BINDING
GL_SRC0_RGB = GL_SOURCE0_RGB
GL_SRC1_RGB = GL_SOURCE1_RGB
GL_SRC2_RGB = GL_SOURCE2_RGB
GL_SRC0_ALPHA = GL_SOURCE0_ALPHA
GL_SRC1_ALPHA = GL_SOURCE1_ALPHA
GL_SRC2_ALPHA = GL_SOURCE2_ALPHA
GLsizeiptr = _c_ptrdiff_t
GLintptr = _c_ptrdiff_t
glGenQueries = _get_function('glGenQueries', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glDeleteQueries = _get_function('glDeleteQueries', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glIsQuery = _get_function('glIsQuery', [_ctypes.c_uint], _ctypes.c_ubyte)
glBeginQuery = _get_function('glBeginQuery', [_ctypes.c_uint, _ctypes.c_uint], None)
glEndQuery = _get_function('glEndQuery', [_ctypes.c_uint], None)
glGetQueryiv = _get_function('glGetQueryiv', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetQueryObjectiv = _get_function('glGetQueryObjectiv', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetQueryObjectuiv = _get_function('glGetQueryObjectuiv', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_uint)], None)
glBindBuffer = _get_function('glBindBuffer', [_ctypes.c_uint, _ctypes.c_uint], None)
glDeleteBuffers = _get_function('glDeleteBuffers', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glGenBuffers = _get_function('glGenBuffers', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glIsBuffer = _get_function('glIsBuffer', [_ctypes.c_uint], _ctypes.c_ubyte)
glBufferData = _get_function('glBufferData', [_ctypes.c_uint, GLsizeiptr, _ctypes.c_void_p, _ctypes.c_uint], None)
glBufferSubData = _get_function('glBufferSubData', [_ctypes.c_uint, GLintptr, GLsizeiptr, _ctypes.c_void_p], None)
glGetBufferSubData = _get_function('glGetBufferSubData', [_ctypes.c_uint, GLintptr, GLsizeiptr, _ctypes.c_void_p], None)
glMapBuffer = _get_function('glMapBuffer', [_ctypes.c_uint, _ctypes.c_uint], _ctypes.c_void_p)
glUnmapBuffer = _get_function('glUnmapBuffer', [_ctypes.c_uint], _ctypes.c_ubyte)
glGetBufferParameteriv = _get_function('glGetBufferParameteriv', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetBufferPointerv = _get_function('glGetBufferPointerv', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_void_p)], None)
