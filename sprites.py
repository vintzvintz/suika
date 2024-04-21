
import pyglet as pg
from constants import *

pg.resource.path = ['assets/']

VISI_NORMAL = 'aucun'
VISI_GAMEOVER = 'game_over'
VISI_HIDDEN = 'hidden'

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

def now():
    return pg.clock.get_default().time()


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
        self._blink_start = None
        self._fadein_start = None 
        self._fadeout_start = None
        self._visibility = VISI_NORMAL
    

    @property
    def fadein(self):
        return bool(self._fadein_start)
    
    @fadein.setter
    def fadein(self, activate ):
        if( activate and not self._fadein_start ):
            self._fadein_start = now()
            self._fadeout_start = None
        elif( not activate ):
            self._fadein_start = None


    @property
    def fadeout(self):
        return bool(self._fadeout_start)
    
    @fadeout.setter
    def fadeout(self, activate):
        if( activate and not self._fadeout_start ):
            self._fadein_start = None
            self._fadeout_start = now()
        elif( not activate ):
            self._fadeout_start = None


    @property
    def blink(self):
        return bool(self._blink_start)
    
    @blink.setter
    def blink(self, activate):
        if( activate and not self._blink_start ):
            self._blink_start = now()
        elif( not activate ):
            self._blink_start = None


    @property
    def visibility(self):
        return self._visibility
    
    @visibility.setter
    def visibility(self, visi):
        if (visi == VISI_NORMAL):
            self._opacity_ref = 255
        elif(visi == VISI_GAMEOVER ):
            self._opacity_ref = 64
        elif(visi == VISI_HIDDEN ):
            self.visible = False
        else:
            print(f"warning: visibilité {visi} inconnue")


    # intercepte l'update du pyglet.spite.Sprite pour traiter les animations
    def update(self, x, y, rotation, on_animation_stop):

        # position
        pg.sprite.Sprite.update( self, x=x, y=y, rotation=rotation )

        # gestion des effets animés
        coef_size = 1.0
        coef_opacity = 1.0

        # fadein
        if( self._fadein_start ):
            assert( not self.fadeout )
            t = pg.clock.get_default().time() - self._fadein_start
            a =  t * (1-SIZESTART_FADEIN)/DELAI_FADEIN + SIZESTART_FADEIN
            if( a >= 1.20 ):
                self.fadein = False
                if( on_animation_stop ):
                    on_animation_stop()
            coef_size = min( 1.20, a )
            coef_opacity = min (1, a)

        # effet fadeout
        if( self._fadeout_start ):
            assert( not self.fadein )
            t = pg.clock.get_default().time() - self._fadeout_start
            a =  (DELAI_FADEOUT - t) / DELAI_FADEOUT
            if( a < 0 ):
                #self.fadeout = False   # ne supprime pas l'effst sinon le sprite reapparait
                if( on_animation_stop ):
                    on_animation_stop()
            coef_size = max(0.2, a)
            coef_opacity = max( 0, a )

        # blink modifie l'opacité multiplicativement avec les autres animations
        if( self._blink_start ):
            dt = pg.clock.get_default().time() - self._blink_start
            if( dt > 0 ):
                coef_opacity *= (0.5 + abs((dt % 1)-0.5))

        self.scale_x = self._scale_ref[0] * coef_size
        self.scale_y = self._scale_ref[1] * coef_size
        self.opacity = int(self._opacity_ref  * coef_opacity)


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
