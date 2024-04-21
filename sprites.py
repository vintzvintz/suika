
import pyglet as pg
from constants import *

pg.resource.path = ['assets/']

EFFET_AUCUN = 'aucun'
EFFET_BLINK = 'blink'
EFFET_FADEIN = 'fade_in'
EFFET_FADEOUT = 'fade_out'
EFFET_GAMEOVER = 'game_over'
EFFET_HIDDEN = 'hidden'
EFFET_ANIMATIONS = [EFFET_BLINK, EFFET_FADEIN, EFFET_FADEOUT ]

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
        pg.shapes.Line.delete()


class SuikaSprite ( pg.sprite.Sprite ):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._animation_start_time = None
        self._on_animation_stop = None
        self.update_effet(EFFET_AUCUN)

    # intercepte l'update du pyglet.spite.Sprite pour traiter les animations
    def update(self, x, y, rotation, effet, animation_time, on_animation_stop):
        self.update_sprite(x, y, rotation)
        self.update_effet(effet)
        if( effet in EFFET_ANIMATIONS ):
            return self.update_animation(effet, animation_time, on_animation_stop)

    def update_sprite(self, x, y, rotation):
        # peuvent être modifiés par les animations ensuite
        pg.sprite.Sprite.update( self, x=x, y=y, rotation=rotation,
                                 scale_x=self._scale_ref[0],
                                 scale_y=self._scale_ref[1] )
        self.opacity = self._opacity_ref 

    def update_animation(self, effet, animation_time, on_animation_stop):
        """ t = animation_time (sec)"""
        t =  animation_time

        # apparition avec effet de taille et transparence
        if( effet == EFFET_FADEIN ):
            ratio_size = min(1, ( t * (1-SIZESTART_FADEIN)/DELAI_FADEIN + SIZESTART_FADEIN ))
            self.scale_x = self._scale_ref[0] * ratio_size
            self.scale_y = self._scale_ref[1] * ratio_size
            if( ratio_size >= 1.20 ):
                on_animation_stop()

        # clignotement des fruit (5 Hz), temporisé de DELAI_CLIGNOTEMENT
        elif( effet == EFFET_BLINK ):
            t_blink = int(max( 0, 5*256*(t-DELAI_CLIGNOTEMENT) )) % 256
            self.opacity = 127 + abs(t_blink-128)

        # fadeout
        elif( effet == EFFET_FADEOUT ):
            opacity = int( max( 0, 255*(DELAI_FADEOUT-t)/DELAI_FADEOUT))
            if( opacity <= 0 ):
                on_animation_stop()
            self.opacity = int( max( 0, 255*(DELAI_FADEOUT-t)/DELAI_FADEOUT))
        # fallback
        else:
            print( f"ERREUR: timer d'animation de sprite inutilisé avec effet '{self._effect}'" )


    def update_effet( self, effet ):
        if (effet == EFFET_AUCUN or effet in EFFET_ANIMATIONS ):
            self._opacity_ref = 255
        elif(effet== EFFET_GAMEOVER):
            self._opacity_ref = 64
        elif(effet== EFFET_HIDDEN):
            self.visible = False
        else:
            print(f"warning: effet {effet} inconnu")


class FruitSprite( SuikaSprite ):
    #def _make_sprite(self, nom, radius):
    def __init__(self, nom, r):
        """  sprite pyglet associé à l'objet physique
        """
        img = pg.resource.image( f"{nom}.png" )
        img.anchor_x = img.width // 2                 # ancrage au centre de l'image
        img.anchor_y = img.height // 2
        self._scale_ref = (2 * r / img.width,  2 * r / img.height)

        super().__init__(img=img, batch=batch(), group=group(SPRITE_GROUP_FRUITS),   )


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

class ExplosionSprite( SuikaSprite ):
    def __init__(self, r, on_explosion_end):
        # setup callback
        self._on_explosion_end = on_explosion_end
        # build actual sprite
        self._make_animated_sprite(r)
        scale = 2.5 * r / EXPLO_SIZE
        self._scale_ref = ( scale, scale )

    def _make_animation(self):
        img = pg.resource.image("explosion.png")
        seq = []
        for (x,y) in EXPLO_CENTRES:
            region = img.get_region( x=x-EXPLO_SIZE//2, y=y-EXPLO_SIZE//2, 
                                     width=EXPLO_SIZE, height=EXPLO_SIZE )
            region.anchor_x = EXPLO_SIZE//2
            region.anchor_y = EXPLO_SIZE//2
            seq.append(region)
        return pg.image.Animation.from_image_sequence( 
            sequence=seq, 
            loop=False,
            duration=DELAI_FADEOUT / len(seq))
    

    def _make_animated_sprite(self, r):
        super().__init__(img=self._make_animation(),
                         batch = batch(),
                         group=group(SPRITE_GROUP_EXPLOSIONS))
        self.opacity=128

    # Event envoyé par pyglet automatiquement
    def on_animation_end(self):
        # renvoie l'envènement à l'objet parent Fruit
        self._on_explosion_end()
