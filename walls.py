import pymunk as pm
from constants import *
import sprites


class MaxLine( object ):

    def __init__(self, space, height, width ):
        self._space = space
        self._body, self._shape = self.make_shape( height, width )
        space.add(self._body, self._shape)
        self._line = sprites.MaxLineSprite( height, width )


    def __del__(self):
        self._space.remove( self._body, self._shape )


    def make_shape(self, height, width):
        # pymunk body - pour la simulation
        body = pm.Body(body_type = pm.Body.STATIC)
        body.position = (0, height)
        # pymunk shape - pour la simulation
        shape = pm.Segment(body, (0, 0), (width,0), radius=5 )
        shape.filter = pm.ShapeFilter( 
            categories=CAT_MAXLINE,
            mask= pm.ShapeFilter.ALL_MASKS() ^ CAT_WALLS )
        shape.collision_type = COLLISION_TYPE_MAXLINE
        return body, shape
    
    def fruits_en_contact(self):
        sqi = self._space.shape_query( self._shape )
        fruit = [ s.shape.fruit for s in sqi ]
        return fruit


class Walls(object):
    """ utilitaire pour creer les parois de l'espace de jeu (space)
    """
    def __init__(self, space, width, height):
        body = pm.Body(body_type=pm.Body.STATIC)
        body.position = (0, 0)
        walls = [
            pm.Segment(body, (0, 0), (0, height+500), 1),          # left
            pm.Segment(body, (0, 0), (width, 0), 1),              # bottom
            pm.Segment(body, (width, 0), (width, height+500), 1)   # right
        ]
        for s in walls:
            s.friction = FRICTION
            s.filter = pm.ShapeFilter( 
                categories=CAT_WALLS,
                mask=pm.ShapeFilter.ALL_MASKS() )
        space.add( body, *walls )
        maxline = MaxLine( space, height=height-WINDOW_MAXLINE_MARGIN, width=width )

        self._space = space
        self._body = body
        self._walls = walls
        self._maxline = maxline


    def fruits_sur_maxline(self):
        """ Id des fruits en contact avec maxline
        """
        return self._maxline.fruits_en_contact()
    

    def __del__(self):
        self._space.remove( self._body, *self._walls)
        #self._maxline deletes itself



