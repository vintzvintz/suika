
import time
import collections
import pyglet as pg
from constants import *


def now():
    return pg.clock.get_default().time()


SPEEDMETER_BUFSIZE = 200
class Speedmeter(object):
    def __init__(self):
        self._history = collections.deque( [0] * SPEEDMETER_BUFSIZE, maxlen=SPEEDMETER_BUFSIZE )
        self.value = 0.0
        self._ticks = 0
        self._last_tick = None

    def tick_rel(self, dt):
        self._ticks += 1
        self._history.append(dt)
        # self._history.pop()    # inutile avec maxlen
        if( (self._ticks % 20)==0 ):
            self.value = len(self._history) / sum(self._history)

    def tick(self):
        current = time.perf_counter()
        if( self._last_tick ):
            last = self._last_tick
            self.tick_rel( current-last )
        self._last_tick = current


class CountDown(object):
    def __init__(self):
        self._start_time = None

    def update(self, deborde):
        if( deborde and not self._start_time ):
            #print( "countdown start")
            self._start_time = now()  # ne remet pas à zero si déja en cours
        elif( not deborde ):
            #debug
            #if( self._start_time ):
            #    print( "countdown stop")
            self._start_time = None

    def status(self):
        """ Renvoie un tuple (t, texte)
            val: valeur du compte à rebours au moment de l'appel de status()
            txt : message d'info sur le compte à rebours
        """
        if (not self._start_time):
            return (0, "")

        t = self._start_time + GAMEOVER_DELAY - now()
        text = ""
        if( t <  COUNTDOWN_DISPLAY_LIMIT ):
            text = f"Defaite dans {t:.01f}s"
        return (t, text)


class RessourceCounter(object):
    """Pour vérifier que toutes les ressources sont bien libérées
    """
    def __init__(self, nom):
        self._cnt = 0
        self.nom = nom

    @property
    def cnt(self):  return self._cnt

    def __del__(self): print( f"{self}" )
    def __repr__(self): return( f"{self.nom}={self._cnt}")
    def inc(self):  self._cnt += 1
    def dec(self):  self._cnt -=1



g_fruit_sprite_cnt = RessourceCounter("FruitSprites")
g_preview_sprite_cnt = RessourceCounter("PreviewSprites")
g_fruit_cnt = RessourceCounter("Fruit")

def print_counters():
    print(f"Fruit={g_fruit_cnt.cnt} FruitsSprite={g_fruit_sprite_cnt.cnt} PreviewSprite={g_preview_sprite_cnt.cnt}")
