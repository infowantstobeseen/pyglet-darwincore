
"""EXT_Cg_shader
http://download.nvidia.com/developer/GLSL/GLSL%20Release%20Notes%20for%20Release%2060.pdf
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_CG_VERTEX_SHADER_EXT = 0x890E
GL_CG_FRAGMENT_SHADER_EXT = 0x890F
