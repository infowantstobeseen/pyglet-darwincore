#!/usr/bin/env python

'''Base class for rendering tests.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet.GL.VERSION_1_1 import *
import pyglet.window
from pyglet.window.event import *
from pyglet.window.key import *
import pyglet.clock
from pyglet.scene2d import *


class Marker:
    def draw(self):
        glColor4f(1, 0, 0, 1)
        glPointSize(5)
        glBegin(GL_POINTS)
        glVertex2f(0, 0)
        glEnd()


class RenderBase(unittest.TestCase):
    w = None
    def init_window(self, vx, vy):
        self.w = pyglet.window.Window(width=vx, height=vy)

    def set_map(self, m):
        if self.w is None:
            vx, vy = m.pxw, m.pxh
            self.init_window(vx, vy)
        else:
            vx = self.w.width
            vy = self.w.height

        self.scene = pyglet.scene2d.Scene(maps=[m])
        self.view = pyglet.scene2d.FlatView(self.scene, 0, 0, vx, vy)

        self.w.push_handlers(self.view.camera)

        self.keyboard = KeyboardStateHandler()
        self.w.push_handlers(self.keyboard)

    marker = None
    def show_focus(self):
        # add in a "sprite"
        self.marker = Sprite(0, 0, 5, 5, Marker())
        self.scene.sprites.append(self.marker)

    def run_test(self):
        clock = pyglet.clock.Clock(fps_limit=30)
        while not self.w.has_exit:
            clock.tick()
            self.w.dispatch_events()
            self.view.fx += (self.keyboard[K_RIGHT] - self.keyboard[K_LEFT]) * 5
            self.view.fy += (self.keyboard[K_UP] - self.keyboard[K_DOWN]) * 5
            if self.marker is not None:
                self.marker.x = self.view.fx
                self.marker.y = self.view.fy
            self.view.clear()
            glColor4f(1, 1, 1, 1)
            self.view.draw()
            self.w.flip()
        self.w.close()


