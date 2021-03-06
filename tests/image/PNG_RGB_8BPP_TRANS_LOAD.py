#!/usr/bin/env python

'''Test load using the Python PNG loader.  You should see the rgb_8bpp_trans.png
image with a hole on it on a checkboard background.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
import base_load

from pyglet.image.codecs.png import PNGImageDecoder

class TEST_SUITE(base_load.TestLoad):
    texture_file = 'rgb_8bpp_trans.png'
    decoder = PNGImageDecoder()

if __name__ == '__main__':
    unittest.main()
