
import pyglet as pg
from constants import *

pg.resource.path = ['assets/']

EFFET_VISIBLE = 'visible'
EFFET_BLINK = 'blink'
EFFET_FADEOUT = 'fadeout'
EFFET_GAMEOVER = 'gameover'
EFFET_HIDDEN = 'hidden'


_groups = {
    SPRITE_GROUP_FOND : pg.graphics.Group( order = 0 ),
    SPRITE_GROUP_FRUITS : pg.graphics.Group( order = 1 ),
    SPRITE_GROUP_EXPLOSIONS : pg.graphics.Group( order = 2 ),
    SPRITE_GROUP_GUI : pg.graphics.Group( order = 3 )
}

_g_batch = pg.graphics.Batch()   # optimisation pour l'affichage

def group(name):
    return _groups[name]

def batch():
    return _g_batch


# Ligne rouge de niveau maxi
class MaxLineSprite( pg.shapes.Line ):
    def __init__(self, height, width):
        super().__init__( 
            x=0, y=height, x2=width, y2=height, width=3, 
            color=(255,20,20), 
            batch=batch(), 
            group=group(SPRITE_GROUP_GUI) )
        
    def __del__(self):
        self.__delete__()


class FruitSprite( pg.sprite.Sprite ):
    #def _make_sprite(self, nom, radius):
    def __init__(self, nom, radius):
        """  sprite pyglet associé à l'objet physique
        """
        img = pg.resource.image( f"{nom}.png" )
        img.anchor_x = img.width // 2                 # ancrage au centre de l'image
        img.anchor_y = img.height // 2
        super().__init__(img=img, 
                         batch=batch(), 
                         group=group(SPRITE_GROUP_FRUITS) )
        super().update( scale_x= 2 * radius / img.width, 
                        scale_y= 2 * radius / img.height )

        self.set_effet( EFFET_VISIBLE )


    def set_effet( self, effet):

        self._effect_start_time = None
        self._opacity_ref = 255
        self._effect = effet

        if(effet == EFFET_VISIBLE):
            pass
        elif(effet== EFFET_BLINK ):
            self._effect_start_time = pg.clock.get_default().time()
        elif(effet== EFFET_FADEOUT):
            self._effect_start_time = pg.clock.get_default().time()
        elif(effet== EFFET_GAMEOVER):
            self._opacity_ref = 64
        elif(effet== EFFET_HIDDEN):
            self.visible = False
        else:
            print(f"warning: effet {effet} inconnu")


    def update(self, x, y, rotation):
        self.x=x
        self.y=y
        self.rotation=rotation
        self.opacity = self._opacity_ref

        # animations
        if( self._effect_start_time ):
            assert( self._effect in [EFFET_BLINK, EFFET_FADEOUT] )

            t =  pg.clock.get_default().time() - self._effect_start_time

            # clignotement des fruit (5 Hz), inhibé avant DELAI_CLIGNOTEMENT
            if( self._effect== EFFET_BLINK ):
                t_blink = int(max( 0, 5*256*(t-DELAI_CLIGNOTEMENT) )) % 256
                self.opacity = 127 + abs(t_blink-128)

            # fadeout immediat
            elif( self._effect== EFFET_FADEOUT ):
                self.opacity = int( max( 0, 255*(DELAI_FADEOUT-t)/DELAI_FADEOUT))
            else:
                print( f"ERREUR: timer inutilement présent avec effet {self._effect}")



## Explosion

ligne1 = [ 
    (206,625),
    (437,625),
    (665,625),
    (904,625),
    (1151,625),
    (1435,625),
    (1712,625),
]
ligne2 = [
    (205,275),
    (456,275),
    (708,275),
    (949,275),
    (1204,275),
    (1456,275),
    (1712,275),
]

EXPLO_CENTRES = ligne1+ligne2
EXPLO_SIZE = 256
EXPLO_PNG = "explosion.png"

class ExplosionSprite( pg.sprite.Sprite ):
    def __init__(self, radius, on_explosion_end):
        img = pg.resource.image("explosion.png")
        seq = []
        for (x,y) in EXPLO_CENTRES:
            region = img.get_region( x=x-EXPLO_SIZE//2, y=y-EXPLO_SIZE//2, 
                                     width=EXPLO_SIZE, height=EXPLO_SIZE )
            region.anchor_x = EXPLO_SIZE//2
            region.anchor_y = EXPLO_SIZE//2
            seq.append(region)
        explo_animation  = pg.image.Animation.from_image_sequence( 
            sequence=seq, 
            loop=False,
            duration=DELAI_FADEOUT / len(seq))
        super().__init__(img=explo_animation, 
                         batch = batch(),
                         group=group(SPRITE_GROUP_EXPLOSIONS))

        scale = 2.5 * radius / EXPLO_SIZE
        self.update( scale=scale )
        self.opacity=192
        self._on_explosion_end = on_explosion_end


    def on_animation_end(self):
        # renvoie l'envènement à l'objet parent Fruit
        self._on_explosion_end()
