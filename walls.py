import pymunk as pm
import pyglet as pg
from constants import *
from sprites import LineSprite


class BoxElement(object):
    """ forme physique pymunk associée à un objet graphique
    a et b sont les extrémités du segment (en coordonnées du body)
    """
    def __init__(self, body, a, b, collision_type, thickness ):
        self.body = body
        # objet graphique pyglet
        l = self.make_sprite(a, b)
        # objet physique pymunk
        s = pm.Segment( body, a, b, radius=thickness )
        s.collision_type = collision_type
        self.segment, self.line = s, l

    def update(self):
        self.line.position = self.body.local_to_world( self.segment.a )
        self.line.rotation = self.body.angle

    def make_sprite(self):
        return NotImplementedError( "Instancier plutot Wall() ou MaxLine()" )
    

class Wall( BoxElement ):
    def __init__(self, body, a, b, collision_type ):
        super().__init__(body, a, b, thickness=WALL_THICKNESS,
                         collision_type=collision_type)
        self.segment.filter= pm.ShapeFilter( categories=CAT_WALLS, 
                                            mask=pm.ShapeFilter.ALL_MASKS() )
        self.segment.elasticity = ELASTICITY_WALLS
        self.segment.friction = FRICTION

    def make_sprite(self, a, b):
        return LineSprite.wall( a, b )


class MaxLine( BoxElement ):
    def __init__(self, body, height, length ):
        a = (0, height)
        b = (length, height)
        super().__init__(body, a, b, thickness=3,
                         collision_type=COLLISION_TYPE_MAXLINE)
        self.segment.filter= pm.ShapeFilter( categories=CAT_MAXLINE, 
                                            mask=pm.ShapeFilter.ALL_MASKS() ^ CAT_WALLS )
        self.segment.sensor = True

    def make_sprite(self, a, b):
        return LineSprite.redline( a, b )


LEFT = "left"
RIGHT = "right"
BOTTOM = "bottom"
MAXLINE = "maxline"

def _make_walls( body, width, height):
    left = Wall( body, a=(0, 0), b=(0, height), collision_type=COLLISION_TYPE_WALL_SIDE )
    bottom = Wall( body, a=(0, 0), b=(width, 0), collision_type=COLLISION_TYPE_WALL_BOTTOM )
    right = Wall( body, a=(width, 0), b=(width, height), collision_type=COLLISION_TYPE_WALL_SIDE )
    maxline = MaxLine( body, length=width, height=height-WINDOW_MAXLINE_MARGIN)
    return {LEFT: left, BOTTOM: bottom, RIGHT: right, MAXLINE: maxline }



class Walls(object):
    """ utilitaire pour creer les parois de l'espace de jeu (space)
    """
    def __init__(self, space, x0, y0, width, height):

        b0 = pm.Body(body_type=pm.Body.STATIC)
        b0.position = ( x0, y0 )
        space.add( b0 )
 
        self._walls = _make_walls(b0, width=width, height=height)
        for w in self._walls.values():
            space.add( w.segment )
        self._space = space
        self._body = b0
        self._maxline = self._walls[MAXLINE]

    def fruits_sur_maxline(self):
        """ Id des fruits en contact avec maxline
        """
        sqi = self._space.shape_query( self._maxline.segment )
        fruit = [ s.shape.fruit for s in sqi ]
        return fruit

    def update(self):
        """ Met à jour les position des objets graphiques depuis la simulation physique
        """
        for w in self._walls.values():
            w.update()

    def __del__(self):
        self._space.remove( self._body )
        #les elements de self._walls se suppriment eux-mêmes



