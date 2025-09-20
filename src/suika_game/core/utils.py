
import time, collections
import pyglet as pg
from .constants import *

def now():
    return pg.clock.get_default().time()

DEFAULT_BUFSIZE = 200
SPEEDMETER_UPDATE_RATE = 0.2   #  seconds

class Speedmeter(object):
    def __init__(self, bufsize=DEFAULT_BUFSIZE ):
        self._deltas = collections.deque( maxlen=bufsize )
        self._value = 0.0
        self._last_tick = None
        self._last_refresh = 0

    def tick_rel(self, dt):
        self._deltas.append(dt)

    def tick(self):
        current = time.perf_counter()
        if( self._last_tick ):
            last = self._last_tick
            self._deltas.append( current-last )
        self._last_tick = current

    @property
    def value(self):
        if( len(self._deltas) == 0 ):
            return 0
        if( now() - self._last_refresh >= SPEEDMETER_UPDATE_RATE ):
            s = sum(self._deltas)
            if( s>0 ):
                self._value = len(self._deltas) / s
                self._last_refresh = now()
        return self._value


class CountDown(object):
    def __init__(self):
        self._start_time = None

    def update(self, deborde):
        if( deborde and not self._start_time ):
            #print( "countdown start")
            self._start_time = now()  # ne remet pas à zero si déja en cours
        elif( not deborde ):
            #if( self._start_time ):
            #    print( "countdown stop")
            self._start_time = None

    def reset(self):
        self.update( False )

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
            text = f"Défaite dans {t:.01f}s"
        return (t, text)


# class RessourceCounter(object):
#     """Pour vérifier que toutes les ressources sont bien libérées
#     """
#     def __init__(self, nom):
#         self._cnt = 0
#         self.nom = nom

#     @property
#     def cnt(self):  return self._cnt

#     def __del__(self): print( f"{self}" )
#     def __repr__(self): return( f"{self.nom}={self._cnt}")
#     def inc(self):  self._cnt += 1
#    def dec(self):  self._cnt -=1

# g_fruit_sprite_cnt = RessourceCounter("FruitSprites")
# g_preview_sprite_cnt = RessourceCounter("PreviewSprites")
# g_fruit_cnt = RessourceCounter("Fruit")

# def print_counters():
#     print(f"Fruit={g_fruit_cnt.cnt} FruitsSprite={g_fruit_sprite_cnt.cnt} PreviewSprite={g_preview_sprite_cnt.cnt}")


def bocal_coords(window_w, window_h ):
    margin_left = BOCAL_MARGIN_SIDE
    margin_right = BOCAL_MARGIN_SIDE
    margin_top = BOCAL_MARGIN_TOP
    margin_bottom = BOCAL_MARGIN_BOTTOM
    bocal_w = window_w - margin_left - margin_right
    bocal_h = window_h - margin_top - margin_bottom
    center = ( margin_left + bocal_w/2, margin_bottom + bocal_h/2 )
    return { 'center':center, 'bocal_w':bocal_w, 'bocal_h':bocal_h }


