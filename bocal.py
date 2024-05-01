import math, random
import pymunk as pm
from constants import *
from sprites import LineSprite
import utils



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

DROP_MARGIN = 0.02  # pourcentage de la largeur du bocal

LEFT = "left"
RIGHT = "right"
BOTTOM = "bottom"
MAXLINE = "maxline"

SHAKE_OFF='off'
SHAKE_ON='on'
SHAKE_STOPPING='stopping'

def _make_walls( body, width, height):
    left = Wall( body, a=(0, 0), b=(0, height), collision_type=COLLISION_TYPE_WALL_SIDE )
    bottom = Wall( body, a=(0, 0), b=(width, 0), collision_type=COLLISION_TYPE_WALL_BOTTOM )
    right = Wall( body, a=(width, 0), b=(width, height), collision_type=COLLISION_TYPE_WALL_SIDE )
    maxline = MaxLine( body, length=width, height=height-WINDOW_MAXLINE_MARGIN)
    return {LEFT: left, BOTTOM: bottom, RIGHT: right, MAXLINE: maxline }



class DropZone(object):
    """calculs de l'emplacement de lâcher des fruits à l'intérieur du bocal
    """
    def __init__(self, body, height, length):
        self._body = body
        self._left = pm.Vec2d(0, height)
        self._right = pm.Vec2d(length, height)


    def _drop_point_interpolate(self, r):
        assert( r >= DROP_MARGIN and r <= 1-DROP_MARGIN ), "tentative de lâcher un fruit hors du bocal"
        point = self._left + (self._right - self._left) * r
        return  self._body.local_to_world( point )


    def drop_point_from_clic(self, x_clic, force_inside ):
        """ Renvoie 
        soit le point de lacher d'un fruit en fonction du point cliqué
        soit None si le point est hors du bocal
        """
        (x_left, y_left) = self._body.local_to_world( self._left )
        (x_right, y_right) = self._body.local_to_world( self._right )

        # position relative sur la dropline
        if( abs(x_right - x_left) > 1 ):
            r = (x_clic - x_left)  / ( x_right - x_left )
        else:
            r = 0.5    # cas particulier du bocal horizontal, sinon division par 0

        if( force_inside ):
            r = max( DROP_MARGIN, r)
            r = min( 1-DROP_MARGIN, r)

        if( r < DROP_MARGIN or r > 1-DROP_MARGIN ):
            print("clic hors du bocal")
            return None

        return self._drop_point_interpolate( r )


    def drop_point_random(self, margin):
        """ Renvoie une position  
        soit le point de lacher d'un fruit en fonction du point cliqué
        soit None si le point est hors du bocal
        """
        return self._drop_point_interpolate( margin + (1 - 2*margin) * random.random() )



class Bocal(object):
    """ utilitaire pour creer les parois de l'espace de jeu (space)
    """
    def __init__(self, space, x0, y0, width, height):

        b0 = pm.Body(body_type=pm.Body.KINEMATIC)
        self._position_ref = (x0, y0)
        b0.position = (x0, y0)
        space.add( b0 )
 
        self._walls = _make_walls(b0, width=width, height=height)
        for w in self._walls.values():
            space.add( w.segment )
        self._space = space
        self._body = b0
        self._maxline = self._walls[MAXLINE]
        self._dropzone = DropZone(body=b0, height=height-100, length=width)
        self._shake = SHAKE_OFF
        self._shake_start_time = None

    def __del__(self):
        self._space.remove( self._body )
        #les elements de self._walls se suppriment eux-mêmes

    @property
    def shake(self):
        return self._shake != SHAKE_OFF

    @shake.setter
    def shake(self, val):
        if( val ):
            self._shake = SHAKE_ON
            self._shake_start_time = utils.now()
            print( f"shake started" )

        else:
            self._shake = SHAKE_STOPPING
            self._shake_start_time = None


    @property
    def width(self):
        bot = self._walls[BOTTOM].segment
        return (bot.b - bot.a).length

    def fruits_sur_maxline(self):
        """ Id des fruits en contact avec maxline
        """
        sqi = self._space.shape_query( self._maxline.segment )
        fruit = [ s.shape.fruit for s in sqi ]
        return fruit

    def update_walls(self, dt):
        """ secoue le bocal
        """
        if(self._shake==SHAKE_OFF):
            return

        # oscillation sinusoidale accelerée
        elif( self._shake == SHAKE_ON ):
            (x_ref, y_ref) =  self._position_ref
            t = utils.now() - self._shake_start_time
            freq = min(
                WALLS_SHAKE_FREQ_MAX, 
                (WALLS_SHAKE_FREQ_MIN + t/WALLS_SHAKE_ACCEL_DELAY * (WALLS_SHAKE_FREQ_MAX-WALLS_SHAKE_FREQ_MIN)))
            #print(f"shake freq={freq}Hz  t={t}s")
            p  =  ( x_ref + 30 * math.sin( 2 * math.pi * freq * t), y_ref ) 
            # vitesse pour atteindre la position au prochain step
            velocity = (p - self._body.position)/dt

        # retour amorti  à la position de reference
        elif( self._shake == SHAKE_STOPPING ):
            dist = self._position_ref - self._body.position 
            velocity =  dist / (dt *10) 

            # condition d'arret de l'amorti
            dist_from_position_ref = (self._body.position - self._position_ref)
            #print( f"shake stopping v={velocity.length}, dist={dist_from_position_ref.length}" )
            if ( dist_from_position_ref.length < 1 ):
                print( f"shake stopped" )
                velocity = (0,0)
                self._body.position = self._position_ref
                self._shake = SHAKE_OFF

        self._body.velocity = velocity


    def update_sprites(self):
        """ Met à jour les position des objets graphiques depuis la simulation physique
        """
        for w in self._walls.values():
            w.update()


    def drop_point_from_clic(self, x_clic, force_inside=False ):
        return self._dropzone.drop_point_from_clic(x_clic, force_inside)

    def drop_point_random(self, margin):
        return self._dropzone.drop_point_random(margin / self.width)


