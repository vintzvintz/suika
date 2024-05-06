
from constants import *
from sprites import PreviewSprite
import fruit 
import utils

class QueueItem(object):
    def __init__(self, kind, width=PREVIEW_SPRITE_SIZE ):
        self.kind = kind
        self._sprite = PreviewSprite( nom=fruit.name_from_kind(kind), width=width )

    def update(self, slot):
        x = PREVIEW_SLOT_SIZE * (slot + 0.5)
        y = PREVIEW_Y_POS
        self._sprite.position = (x,y,0)
        self._sprite.update(x, y)


class FruitQueue( object ):
    def __init__( self, cnt):
        self._cnt = cnt
        self.reset()

    def reset(self):
        self._queue = []
        for _ in range(PREVIEW_COUNT):
            self._add_item()
        self._shift_end_time = None
        self.update()

    def _add_item(self):
        s = QueueItem( kind = fruit.random_kind(), width=PREVIEW_SPRITE_SIZE )
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
            item.update(idx + offset)

