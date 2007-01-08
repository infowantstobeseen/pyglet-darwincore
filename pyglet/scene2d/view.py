#!/usr/bin/env python

'''
View code for displaying 2d scenes of maps and sprites
======================================================

---------------
Getting Started
---------------

Creating a simple scene and displaying it:

    >>> import pyglet.window
    >>> import pyglet.scene2d
    >>> m = pyglet.scene2d.RectMap(32, 32, cells=gen_rect_map([[0]*4]*4, 32, 32)
    >>> w = pyglet.window.Window(width=m.pxw, height=m.pxh)
    >>> s = pyglet.scene2d.Scene(maps=[m])
    >>> v = pyglet.scene2d.FlatView.from_window(s, w)
    >>> v.debug((0,0))
    >>> w.flip()

------------------
Events and Picking
------------------


'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import operator

from pyglet.scene2d.camera import FlatCamera
from pyglet.GL.VERSION_1_1 import *

class View(object):

    def get(self, x, y):
        ''' Pick whatever is on the top at the pixel position x, y. '''
        raise NotImplemented()

    def tile_at(self, (x, y)):
        ' query for tile at given screen pixel position '
        raise NotImplemented()
 
    def sprite_at(self, (x, y)):
        ' query for sprite at given screen pixel position '
        raise NotImplemented()


class FlatView(View):
    '''Render a flat view of a pyglet.scene2d.Scene.

    Attributes:

        scene           -- a pyglet.scene2d.Scene instance
        camera          -- a pyglet.scene2d.FlatCamera instance
        allow_oob       -- indicates whether the viewport will allow
                           viewing of out-of-bounds tile positions (ie.
                           for which there is no tile image). If set to
                           False then the map will not scroll to attempt
                           to display oob tiles.
        scale, rotation -- scale to apply to the map (rotation in degrees)
        fx, fy          -- pixel point to center in the viewport, subject
                           to OOB checks
    '''
    # XXX nuke scale? belongs in camera?
    def __init__(self, scene, x, y, width, height, allow_oob=True,
            scale=1, rotation=0, fx=0, fy=0):
        super(View, self).__init__()
        self.scene = scene
        self.camera = FlatCamera(x, y, width, height)
        self.allow_oob = allow_oob
        self.scale = scale
        self.rotation = rotation
        self.fx, self.fy = fx, fy

    @classmethod
    def from_window(cls, scene, window, **kw):
        '''Create a view which is the same dimensions as the supplied
        window.'''
        return cls(scene, 0, 0, window.width, window.height, **kw)

    def __repr__(self):
        return '<%s object at 0x%x focus=(%d,%d) oob=%s>'%(
            self.__class__.__name__, id(self), self.fx, self.fy,
            self.allow_oob)

    def translate_position(self, x, y):
        '''Translate the on-screen pixel position to a Scene pixel
        position.'''
        fx, fy = self._determine_focus()
        ox, oy = self.camera.width/2-fx, self.camera.height/2-fy
        return (x - ox, y - oy)

    def get(self, x, y):
        ''' Pick whatever is on the top at the position x, y. '''
        raise NotImplemented()

    def tile_at(self, (x, y)):
        ' query for tile at given screen pixel position '
        raise NotImplemented()
 
    def sprite_at(self, (x, y)):
        ' query for sprite at given screen pixel position '
        raise NotImplemented()

    def _determine_focus(self):
        '''Determine the focal point of the view based on foxus (fx, fy),
        allow_oob and maps.

        Note that this method does not actually change the focus attributes
        fx and fy.
        '''
        if not self.scene.maps or self.allow_oob: return (self.fx, self.fy)

        # figure the bounds min/max
        m = self.scene.maps[0]
        b_min_x = m.x
        b_min_y = m.y
        b_max_x = m.x + m.pxw
        b_max_y = m.y + m.pxh
        for m in self.scene.maps[1:]:
            b_min_x = min(b_min_x, m.x)
            b_min_y = min(b_min_y, m.y)
            b_max_x = min(b_max_x, m.x + m.pxw)
            b_max_y = min(b_max_y, m.y + m.pxh)

        # figure the view min/max based on focus
        w2 = self.camera.width/2
        h2 = self.camera.height/2

        fx, fy = self.fx, self.fy
        v_min_x = fx - w2
        v_min_y = fy - h2
        x_moved = y_moved = False
        if v_min_x < b_min_x:
            fx += b_min_x - v_min_x
            x_moved = True
        if v_min_y < b_min_y:
            fy += b_min_y - v_min_y
            y_moved = True

        v_max_x = fx + w2
        v_max_y = fy + h2
        if not x_moved and v_max_x > b_max_x:
            fx -= v_max_x - b_max_x
        if not y_moved and v_max_y > b_max_y:
            fy -= v_max_y - b_max_y

        return map(int, (fx, fy))

    def clear(self, colour=None, is_window=True):
        '''Clear the view.

        If colour is None then the current glColor (is_window == False)
        or glClearColor (is_window == True) is used.

        If the view is not the whole window then you should pass
        is_window=False otherwise the whole window will be cleared.
        '''
        if is_window:
            if colour is not None:
                glClearColor(*colour)
            glClear(GL_COLOR_BUFFER_BIT)
        else:
            if colour is not None:
                glColor(*colour)
            glBegin(GL_QUADS)
            glVertex2f(0, 0)
            glVertex2f(0, self.camera.height)
            glVertex2f(self.camera.width, self.camera.height)
            glVertex2f(self.camera.width, 0)
            glEnd()


    def draw(self):
        '''Draw the scene centered (or closest, depending on allow_oob)
        on position which is (x, y). '''
        self.camera.project()

        # sort by depth
        self.scene.maps.sort(key=operator.attrgetter('z'))

        # determine the focus point
        fx, fy = self._determine_focus()

        # XXX push state?
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

        # now draw
        glPushMatrix()
        glTranslatef(self.camera.width/2-fx, self.camera.height/2-fy, 0)
        for smap in self.scene.maps:
            glPushMatrix()
            glTranslatef(smap.x, smap.y, smap.z)

            # XXX use smap.get_cells_in_region(bottomleft, topright)
            for column in smap.cells:
                for cell in column:
                    if not cell.tile: continue
                    x, y = cell.origin
                    glPushMatrix()
                    glTranslatef(x, y, -1)
                    if cell.tile:
                        cell.tile.image.draw()
                    glPopMatrix()
            glPopMatrix()

        for sprite in self.scene.sprites:
            glPushMatrix()
            glTranslatef(sprite.x, sprite.y, sprite.z)
            if sprite.angle:
                glTranslatef(sprite.cog[0], sprite.cog[1], 0)
                glRotatef(sprite.angle, 0, 0, 1)
                glTranslatef(-sprite.cog[0], -sprite.cog[1], 0)
            sprite.image.draw()
            glPopMatrix()

        glPopMatrix()
 

class ViewScrollHandler(object):
    '''Scroll the view in response to the mouse scroll wheel.
    '''
    def __init__(self, view):
        self.view = view

    def on_mouse_scroll(self, dx, dy):
        fx, fy = self.view._determine_focus()
        self.view.fx = fx + dx * 30
        self.view.fy = fy + dy * 30

