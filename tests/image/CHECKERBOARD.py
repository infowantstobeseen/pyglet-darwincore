#!/usr/bin/env python

'''Test that the checkerboard pattern looks correct.

One window will open, it should show one instance of the checkerboard
pattern in two levels of grey.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet.GL.VERSION_1_1 import *
from pyglet.image import *
from pyglet.window import *
from pyglet.window.event import *

from tests.regression import ImageRegressionTestCase

class TEST_CHECKERBOARD(ImageRegressionTestCase):
    def on_resize(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def on_expose(self):
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        self.texture.draw()
        self.window.flip()

        if self.capture_regression_image():
            self.exit_handler.exit = True

    def test_main(self):
        width, height = 200, 200
        self.window = w = Window(width, height, visible=False)
        self.exit_handler = ExitHandler()
        w.push_handlers(self.exit_handler)
        w.push_handlers(self)

        self.texture = Image.create_checkerboard(width).texture()

        w.set_visible()
        while not self.exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
