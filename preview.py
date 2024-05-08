
from constants import *
from sprites import PreviewSprite
import fruit 
import utils

class QueueItem(object):
    def __init__(self, kind, sprite_size ):
        self.kind = kind
        self._sprite = PreviewSprite( nom=fruit.name_from_kind(kind), width=sprite_size )
        self.y_pos = 0

    def update(self, slot, y):
        x = PREVIEW_SLOT_SIZE * (slot + 0.5)
        self._sprite.position = (x,y,0)
        self._sprite.update(x, y)


class FruitQueue( object ):
    def __init__( self, cnt):
        self._cnt = cnt
        self.y_pos = 0
        self.reset()

    def reset(self):
        self._queue = []
        for _ in range(PREVIEW_COUNT):
            self._add_item()
        self._shift_end_time = None
        self.update()

    def on_resize(self, width, height):
        self.y_pos = height - PREVIEW_Y_POS

    def _add_item(self):
        s = QueueItem( kind = fruit.random_kind(), sprite_size=PREVIEW_SPRITE_SIZE )
        self._queue.insert(0, s)

    def get_next_fruit(self):
        kind = self._queue.pop().kind
        self._add_item()
        if( not self._shift_end_time ):
            self._shift_end_time = utils.now()
        self._shift_end_time += PREVIEW_SHIFT_DELAY

        assert( len(self._queue)==self._cnt )
        return kind

    def update(self):
        """update preview sprites positions
        """
        # animation de défilement vers la droite
        if( self._shift_end_time ):
            offset = (utils.now() - self._shift_end_time) / PREVIEW_SHIFT_DELAY
            if( offset > 0):
                self._shift_end_time = None

        # condition de fin d'animation
        if( not self._shift_end_time ):
            offset = 0
        
        for idx, item in enumerate(self._queue):
            item.update(slot=(idx + offset), y=self.y_pos)
