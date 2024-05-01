import pyglet as pg
from constants import *
import sprites

TOP_LEFT = 'label1'
TOP_CENTER = 'label2'
TOP_RIGHT = 'label3'
GAME_OVER = 'gameover'

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
                          batch=sprites.batch(),group=sprites.groupe_gui()),
            TOP_CENTER: pg.text.Label('---',
                          font_name=font_name, font_size=font_size,
                          x=window_width//2, y=window_height - top_margin,
                          anchor_x='center', anchor_y='top',
                          batch=sprites.batch(),group=sprites.groupe_gui()),
            TOP_RIGHT: pg.text.Label('---',
                          font_name=font_name, font_size=font_size,
                          x=window_width - top_margin, y=window_height - top_margin,
                          anchor_x='right', anchor_y='top',
                          batch=sprites.batch(), group=sprites.groupe_gui()),
        }

        # image GAME OVER
        img = pg.resource.image("gameover.png")
        img.anchor_x = img.width // 2                        # ancrage au centre de l'image
        img.anchor_y = img.height // 2
        ratio_x = window_width / img.width
        ratio_y = window_height / img.height
        self._gameover = pg.sprite.Sprite( img=img, batch=sprites.batch(), group=sprites.groupe_gui() )
        self._gameover.visible = False
        self._gameover.update( x = window_width//2, 
                               y = window_height//2,
                               scale = min( 1.0, ratio_x, ratio_y) )

        # intercalaire semi-transparent pour gameover
        self._masque = pg.shapes.Rectangle(
            x=0,y=0,width=window_width, height=window_height,
            color=(40,20,10,150), batch=sprites.batch(), group=sprites.groupe_masque() )
        self._masque.visible = False


    def update(self, label, text):
        self._labels[label].text = text

    def update_dict( self, texts ):
        for lbl, txt in texts:
            self.update( lbl, txt)

    def reset(self):
        for l in self._labels.values():
            l.text=""
        self._gameover.visible=False
        self._masque.visible=False

    def show_gameover(self):
        self._labels[TOP_CENTER].text = "GAME OVER"
        self._gameover.visible=True
        self._masque.visible=True

