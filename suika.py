import random
import collections

import pyglet as pg
import pymunk as pm

from constants import *
import fruit, sprites, walls, gui
from fruit import Fruit


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


    def tick_abs(self, new_val ):
        raise NotImplementedError
        self._ticks += 1
        prev_val = self._history[-1]
        self._history.append( new_val-prev_val)


class CountDown(object):
    def __init__(self):
        self.reset()

    def start(self):
        if( not self._start_time ):
            self._start_time = pg.clock.get_default().time()

    def reset(self):
        self._start_time = None

    def status(self):
        """ Renvoie un tuple (gameover, texte)
            gameover : booleen vrai si la partie est perdue
            text : message d'info sur le compte à rebours
        """
        if (not self._start_time):
            return (False, "")

        t = pg.clock.get_default().time() - self._start_time 
        etat = t > DELAI_DEBORDEMENT
        text = ""
        if( t>DELAI_CLIGNOTEMENT ):
            text = f"defaite dans {DELAI_DEBORDEMENT-t:.02f}s"
        return (etat, text)
    

def get_fruit_shape(arbiter):
    # détecte le fruit et la maxline dans la collision

    def is_fruit_shape(shape):
        return shape.collision_type > 0 and shape.collision_type<=fruit.nb_fruits()

    if( is_fruit_shape( arbiter.shapes[0]) ):
        return arbiter.shapes[0]
    elif ( is_fruit_shape( arbiter.shapes[1])):
        return arbiter.shapes[1]
    else:
        raise RuntimeError( "Collision sans fruit")


AUTOPLAY_FLOW = 1 + WINDOW_WIDTH // 750

class SuikaWindow(pg.window.Window):
    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        super().__init__(width, height)
        self._space = pm.Space( )
        self._space.gravity = (0, -100*GRAVITY)
        self._walls = walls.Walls(space=self._space, width=width, height=height)
        self._fruits = dict()
        self._next_fruit = None
        self._countdown = CountDown()
        self._labels = gui.Labels( window_width=width, window_height=height )
        self._collision_resolver = fruit.CollisionResolver(self._space)
        self.setup_maxline_collision_handlers()
        self.reset_game()
        pg.clock.schedule_interval( self.update, interval=PYMUNK_INTERVAL )
        pg.clock.schedule_interval( self.autoplay, interval=AUTOPLAY_INTERVAL)
        self.fps_display = pg.window.FPSDisplay(self)
        self.pymunk_speedmeter = Speedmeter()


    def reset_game(self):
        # libere les ressources de la partie précédente
        self._fruits = dict()
        self._score = 0
        self._is_gameover = False
        self._collision_resolver.reset()
        self._countdown.reset()
        self._labels.reset()
        self._is_paused = False
        self._is_autoplay = False
        self._next_fruit = None
        self.add_next_fruit()
        self.fps_display = pg.window.FPSDisplay(self)


    def setup_maxline_collision_handlers(self):
        """ gere les collisions avec maxline
        """
        coll_handler = self._space.add_wildcard_collision_handler( COLLISION_TYPE_MAXLINE )
        coll_handler.begin = lambda arbiter, space, data : self.collision_maxline_begin(arbiter)
        coll_handler.separate = lambda arbiter, space, data : self.collision_maxline_separate(arbiter)


    def collision_maxline_begin(self, arbiter):
        id = get_fruit_shape(arbiter).fruit_id
        # met le fruit en mode débordement
        self._fruits[id].set_deborde(True)
        # ignore la collision pour la simulation physique
        return False   


    def collision_maxline_separate(self, arbiter):
        id = get_fruit_shape(arbiter).fruit_id
        # annule le mode débordement et remet le fruit en mode normal
        if( id in self._fruits.keys() ):
            self._fruits[id].set_deborde(False)
        # ignore la collision pour la simulation physique
        return False  


    def add_next_fruit(self, dt=None):
        """Cree un fruit en attente de largage
        """
        if( self._is_gameover):
            return
        if( self._next_fruit ):
            print("next_fruit deja present")
            return
        self._next_fruit = Fruit( self._space )
        self._fruits[ self._next_fruit.id ] = self._next_fruit


    def explose_fruit( self, id ):
        self._fruits[id].explose()


    def remove_fruit_by_id( self, id ):
        if( id in self._fruits ):
            self._score += self._fruits[id].points
            del self._fruits[id]       # remove from list of active fruits


    def autoplay(self, dt):
        if( not self._is_autoplay or self._is_paused or self._is_gameover ):
            return
        for i in range(AUTOPLAY_FLOW):
            f = Fruit( self._space, kind= random.randint(1,4)  )
            f.set_x( random.randint(0, WINDOW_WIDTH))
            f.drop()
            self._fruits[f.id] = f


    def gameover(self):
        """ Actions en cas de partie perdue
        """
        self._is_gameover = True    # inhibe les actions de jeu
        if( self._next_fruit ):
            self.remove_fruit_by_id( self._next_fruit.id )
            self._next_fruit = None
        for f in self._fruits.values():
            f.blink = False
            f.gameover()
        self._labels.show_gameover()


    def shoot_fruit(self, x, y):
        print(f"Shoot x={x} y={y}")
        qi = self._space.point_query( (x, y), max_distance=0, shape_filter=pm.ShapeFilter() )
        try:
            if( len(qi)==0 ):
                print("clic-droit dans le vide")
            else:
                if( len(qi)>1 ):
                    print("Warning: plusieurs formes superposées")
                id = qi[0].shape.fruit_id
                fruit = self._fruits[id]
                print(f"shooted {fruit}")
                self.remove_fruit_by_id( id )
        except KeyError:
            pass    # aucune erreur fatale avec les shoots de fruits


    def traite_contacts(self):
        """ fusionne et supprime les fruits en contact
        """
        created, to_remove = self._collision_resolver.resolve(self._fruits)
        for f in created:
             self._fruits[ f.id ] = f
        for id in to_remove:
            self.explose_fruit(id)


    def retire_fruits(self):
        """ Supprime les fruits retirés du jeu
        """
        ids_to_remove = [ id for (id, f) in self._fruits.items() if f.removed ]
        for id in ids_to_remove:
            self.remove_fruit_by_id( id )


    def update(self, dt):
        """Avance d'un pas la simulation physique
        """
        self.pymunk_speedmeter.tick_rel(dt)
        if( self._is_paused or self._is_gameover ):
            return

        # calcule les positions des objets
        self._collision_resolver.reset()
        self._space.step( PYMUNK_INTERVAL )

        offscreen = {f for f in self._fruits.values() if f.is_offscreen() }
        if( offscreen ):
            self.gameover()
            print( "WARNING balles en dehors du jeu !" )

        self.traite_contacts()
        self.retire_fruits()


    def on_draw(self):
        assert fruit.active_count() == len(self._fruits), "Ressource leak"

        # met a jour les positions des fruits 
        for f in self._fruits.values():
            f.update()

        # gere le countdown en cas  de débordement
        ids = self._walls.fruits_sur_maxline()
        if( ids ):
            self._countdown.start()  # ne remet pas à zero si déja en cours
        else:
            self._countdown.reset()

        # met à jour l'affichage et détecte la fin de partie
        gameover, countdown_txt = self._countdown.status()
        self._labels.update( gui.TOP_LEFT, f"fruits {len(self._fruits)}" )
        #self._labels.update( gui.TOP_RIGHT, f"score {self._score}" )
        self._labels.update( gui.TOP_RIGHT, f"FPS {self.pymunk_speedmeter.value:.0f}" )
        self._labels.update( gui.TOP_CENTER, countdown_txt )

        if( gameover or self._is_gameover ):
            self.gameover()

        # met à jour l'affichage
        self.clear()
        sprites.batch().draw()
        self.fps_display.draw()


    def on_key_press(self, symbol, modifiers):
        print(f"key {symbol} was pressed")

        # ESC ferme le jeu dans tous les cas
        if(symbol == pg.window.key.ESCAPE):
            self.close()
            return pg.event.EVENT_HANDLED
        
        # n'importe quelle autre touche que ESC relance une partie si gameover
        if(self._is_gameover):
            self.reset_game()
            return pg.event.EVENT_HANDLED

        # A controle l'autoplay
        if(symbol == pg.window.key.A):
            self._is_autoplay = not self._is_autoplay
            return pg.event.EVENT_HANDLED

        # SPACE met le jeu en pause
        if(symbol == pg.window.key.SPACE):
            self._is_paused = not self._is_paused
            return pg.event.EVENT_HANDLED
        
        return pg.event.EVENT_UNHANDLED


    def on_mouse_press(self, x, y, button, modifiers):
        # laĉhe le next_fruit
        if( (button & pg.window.mouse.LEFT) and self._next_fruit and not self._is_gameover ):
            self._next_fruit.set_x( x )
            self._next_fruit.drop()
            self._next_fruit = None
            pg.clock.schedule_once( self.add_next_fruit, delay=0.5)

        # Supprime un fruit sur clic droit
        if( (button & pg.window.mouse.RIGHT) and not self._is_gameover ):
            self.shoot_fruit(x, y)

def main():
    pg.resource.path = ['assets/']
    pg.resource.reindex()
    window = SuikaWindow()
    pg.app.run()

if __name__ == '__main__':

    main()

