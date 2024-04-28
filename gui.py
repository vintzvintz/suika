import pyglet as pg
from constants import *
import sprites

TOP_LEFT = 'label1'
TOP_CENTER = 'label2'
TOP_RIGHT = 'label3'
GAME_OVER = 'gameover'

_sprite_group = sprites.sprite_group(SPRITE_GROUP_GUI)

class Labels(object):

    def __init__( self, window_width, window_height, 
                 top_margin=GUI_TOP_MARGIN, font_size=GUI_FONT_SIZE, 
                 font_name="Arial" ):

        # textes en haut 
        self._labels = {
            TOP_LEFT: pg.text.Label('---',
                          font_name=font_name, font_size=font_size,
                          x=top_margin, y=window_height - top_margin,
                          anchor_x='left', anchor_y='top',
                          batch=sprites.batch(),group=_sprite_group),
            TOP_CENTER: pg.text.Label('---',
                          font_name=font_name, font_size=font_size,
                          x=window_width//2, y=window_height - top_margin,
                          anchor_x='center', anchor_y='top',
                          batch=sprites.batch(),group=_sprite_group),
            TOP_RIGHT: pg.text.Label('---',
                          font_name=font_name, font_size=font_size,
                          x=window_width - top_margin, y=window_height - top_margin,
                          anchor_x='right', anchor_y='top',
                          batch=sprites.batch(), group=_sprite_group),
        }

        # image GAME OVER
        img = pg.resource.image("gameover.png")
        img.anchor_x = img.width // 2                        # ancrage au centre de l'image
        img.anchor_y = img.height // 2
        ratio_x = window_width / img.width
        ratio_y = window_height / img.height
        self._gameover = pg.sprite.Sprite( img=img, batch=sprites.batch(), group=_sprite_group )
        self._gameover.visible = False
        self._gameover.update( x = window_width//2, 
                               y = window_height//2,
                               scale = min( 1.0, ratio_x, ratio_y) )

    def update(self, label, text):
        self._labels[label].text = text

    def update_dict( self, texts ):
        for lbl, txt in texts:
            self.update( lbl, txt)

    def reset(self):
        for l in self._labels.values():
            l.text=""
        self._gameover.visible=False

    def show_gameover(self):
        self._labels[TOP_CENTER].text = "GAME OVER"
        self._gameover.visible=True

