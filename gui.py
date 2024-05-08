import pyglet as pg
from constants import *
import sprites


TOP_LEFT = 'label1'
TOP_CENTER = 'label2'
TOP_RIGHT = 'label3'



class Label( pg.text.Label):
    def __init__(self, window_width, window_height):
        coords = self.coords( window_width, window_height, margin=GUI_TOP_MARGIN)
        super().__init__(
            **coords,
            font_name="Arial",
            font_size=GUI_FONT_SIZE,
            batch=sprites.batch(),
            group=sprites.groupe_gui() )

    def coords( window_width, window_height, margin):
        raise NotImplementedError("Implementer coords() dans la sous-classe")
    
    def on_resize(self, width, height):
        coords = dict(self.coords( width, height, margin=GUI_TOP_MARGIN).items())
        self.x = coords['x']
        self.y = coords['y']

class TopLeftLabel( Label ):
    def coords(self, width, height, margin):
        return {
            'x' : margin,
            'y': height - margin,
            'anchor_x' : 'left',
            'anchor_y' : 'top',
        }

class CenterLabel( Label ):
    def coords(self, width, height, margin):
        return {
            'x' : width//2,
            'y': height - margin,
            'anchor_x' : 'center',
            'anchor_y' : 'top',
        }

class TopRightLabel( Label ):
    def coords(self, width, height, margin):
        return {
            'x' : width - margin,
            'y': height - margin,
            'anchor_x' : 'right',
            'anchor_y' : 'top',
        }
    

class GameOverSprite(pg.sprite.Sprite):
    def __init__(self, width, height):

        img = pg.resource.image("gameover.png")
        img.anchor_x = img.width // 2                        # ancrage au centre de l'image
        img.anchor_y = img.height // 2
        self._gameover_img = img
        super().__init__(img, batch=sprites.batch(), group=sprites.groupe_gui() )
        self.on_resize(width=width, height=height)
        self.visible = False

    def on_resize(self, width, height):
        ratio_x = width / self._gameover_img.width
        ratio_y = height / self._gameover_img.height
        self.update( x = width//2, 
                     y = height//2,
                    scale = min( 1.0, ratio_x, ratio_y) )


class GameOverMask(pg.shapes.Rectangle):
    def __init__(self, width, height):
        super().__init__(
            x=0,y=0,
            width=width, height=height,
            color=(40,20,10,150), 
            batch=sprites.batch(), 
            group=sprites.groupe_masque() )
        
    def on_resize(self, width, heigth):
        self.width=width
        self.height=heigth


class GUI(object):
    def __init__( self, window_width, window_height) :

        # textes en haut 
        self._label_topleft = TopLeftLabel(window_width, window_height)
        self._label_center = CenterLabel(window_width, window_height)
        self._label_topright = TopRightLabel(window_width, window_height)
        self._gameover = GameOverSprite( window_width, window_height )
        self._gameover_mask = GameOverMask( window_width, window_height)
        self._resizables = [self._gameover,
                            self._gameover_mask,
                            self._label_topleft,
                            self._label_center,
                            self._label_topright ]

    def on_resize(self, width, height):
        for item in self._resizables:
            item.on_resize(width, height)

    def update_label(self, label, text):
        if(label==TOP_LEFT): self._label_topleft.text = text
        if(label==TOP_CENTER): self._label_center.text = text
        if(label==TOP_RIGHT): self._label_topright.text = text

    def update_dict( self, texts ):
        for lbl, txt in texts.items():
            self.update_label(lbl, txt)

    def reset(self):
        self.update_dict({ label:"" for label in [TOP_LEFT, TOP_CENTER, TOP_RIGHT] } )
        self._gameover.visible=False
        self._gameover_mask.visible=False

    def show_gameover(self):
        self._label_center.text = "GAME OVER"
        self._gameover.visible=True
        self._gameover_mask.visible=True
