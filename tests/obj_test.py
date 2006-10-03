#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import ctypes
import pyglet.window
from pyglet.window.event import *

from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
from pyglet import clock
from pyglet.model import obj

factory = pyglet.window.WindowFactory()
factory.config._attributes['doublebuffer'] = 1
w1 = factory.create(width=200, height=200)

class ExitHandler(object):
    running = True
    def on_close(self):
        self.running = False
    def on_keypress(self, symbol, modifiers):
        if symbol == pyglet.window.key.K_ESCAPE:
            self.running = False
        return EVENT_UNHANDLED
exit_handler = ExitHandler()
w1.push_handlers(exit_handler)

c = clock.Clock()

fourfv = ctypes.c_float * 4
c_float_p = ctypes.POINTER(ctypes.c_float)
glLightfv(GL_LIGHT0, GL_POSITION,
    ctypes.cast(fourfv(100, 200, 100, 0), c_float_p))
glLightfv(GL_LIGHT0, GL_AMBIENT,
    ctypes.cast(fourfv(0.2, 0.2, 0.2, 1.0), c_float_p))
glLightfv(GL_LIGHT0, GL_DIFFUSE,
    ctypes.cast(fourfv(0.5, 0.5, 0.5, 1.0), c_float_p))
glEnable(GL_LIGHT0)
glEnable(GL_LIGHTING)
glEnable(GL_COLOR_MATERIAL)
glEnable(GL_DEPTH_TEST)
glShadeModel(GL_SMOOTH)

glPolygonMode(GL_FRONT, GL_FILL)
glDepthFunc(GL_LESS)
glEnable(GL_CULL_FACE)
glCullFace(GL_BACK)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(60., 1., 1., 100.)

glMatrixMode(GL_MODELVIEW)
glClearColor(0, 0, 0, 0)

bunny = obj.OBJ(os.path.join(os.path.split(__file__)[0], 'rabbit.obj'))

r = 0
while exit_handler.running:
    c.set_fps(60)
    w1.dispatch_events()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    gluLookAt(0, 5, 5, 0, 1, -1, 0, 1, 0)

    r += 1
    if r > 360: r = 0
    glRotatef(r, 0, 1, 0)
    glCallList(bunny.gl_list)

    w1.flip()

