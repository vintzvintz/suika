
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

    def tick_rel(self, dt):
        self._ticks += 1
        self._history.append(dt)
        # self._history.pop()    # inutile avec maxlen
        if( (self._ticks % 20)==0 ):
            self.value = len(self._history) / sum(self._history)


class CountDown(object):
    def __init__(self):
        self._start_time = None

    def update(self, deborde):
        if( deborde and not self._start_time ):
            print( "countdown start")
            self._start_time = now()  # ne remet pas à zero si déja en cours
        elif( not deborde ):
            self._start_time = None
            #debug
            if( self._start_time ):
                print( "countdown stop")

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
            text = f"Defaite dans {t:.02f}s"
        return (t, text)