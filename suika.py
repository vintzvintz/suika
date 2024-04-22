import random
import collections

import pyglet as pg
import pymunk as pm

from constants import *
import fruit, sprites, walls, gui
from fruit import Fruit
import utils


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

    # def tick_abs(self, new_val ):
    #     raise NotImplementedError
    #     self._ticks += 1
    #     prev_val = self._history[-1]
    #     self._history.append( new_val-prev_val)


class CountDown(object):
    def __init__(self):
        self._start_time = None


    def update(self, deborde):
        if( deborde and not self._start_time ):
            print( "countdown start")
            self._start_time = utils.now()  # ne remet pas à zero si déja en cours
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

        t = self._start_time + GAMEOVER_DELAY - utils.now()
        text = ""
        if( t <  COUNTDOWN_DISPLAY_LIMIT ):
            text = f"Defaite dans {t:.02f}s"
        return (t, text)


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
        self._collision_helper = fruit.CollisionHelper(self._space)
        self.reset_game()
        pg.clock.schedule_interval( self.update, interval=PYMUNK_INTERVAL )
        pg.clock.schedule_interval( self.autoplay, interval=AUTOPLAY_INTERVAL)
        pg.clock.schedule_interval( self.cleanup_fruit_list, interval= 10*PYMUNK_INTERVAL )
        self.fps_display = pg.window.FPSDisplay(self)
        self.pymunk_speedmeter = Speedmeter()


    def reset_game(self):
        # libere les ressources de la partie précédente
        self._fruits = dict()
        self._score = 0
        self._is_gameover = False
        self._collision_helper.reset()
        self._countdown.update( deborde=False )
        self._labels.reset()
        self._is_paused = False
        self._is_autoplay = False
        self._next_fruit = None
        self.add_next_fruit()
        self.fps_display = pg.window.FPSDisplay(self)


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


    def remove_fruit_by_id( self, id ):
        if( id in self._fruits ):
            self._score += self._fruits[id].points
            del self._fruits[id]       # remove from list of active fruits


    def cleanup_fruit_list(self, dt):
        to_remove = [f.id for f in self._fruits.values() if f.removed]
        for id in to_remove:
            self.remove_fruit_by_id(id)


    def autoplay(self, dt):
        if( not self._is_autoplay or self._is_paused or self._is_gameover ):
            return
        for _ in range(AUTOPLAY_FLOW):
            f = Fruit( self._space, kind= random.randint(1,4)  )
            f.set_x( random.randint(0, WINDOW_WIDTH))
            f.normal()
            self._fruits[f.id] = f


    def gameover(self):
        """ Actions en cas de partie perdue
        """
        print("GAMEOVER")
        self._is_gameover = True    # inhibe les actions de jeu
        for f in self._fruits.values():
            f.gameover()
        if( self._next_fruit ):
            self._next_fruit.remove()
            self._next_fruit = None
        self._labels.show_gameover()

    def toggle_autoplay(self):
            self._is_autoplay = not self._is_autoplay
            if( self._is_autoplay and self._next_fruit):
                self._next_fruit.remove()
                self._next_fruit = None
            if( not self._is_autoplay and not self._next_fruit ):
                self.add_next_fruit()


    def shoot_fruit(self, x, y):
        qi = self._space.point_query( (x, y), max_distance=0, shape_filter=pm.ShapeFilter() )
        if( len(qi)>0 ):
            id = qi[0].shape.fruit_id
            f = self._fruits[id]
            if( f.is_mode_normal ):
                f.remove()
                print(f"shooted {f}")


    def update(self, dt):
        """Avance d'un pas la simulation physique
        """
        self.pymunk_speedmeter.tick_rel(dt)
        if( self._is_paused ):
            return

        # calcule les positions des objets
        self._collision_helper.reset()
        self._space.step( PYMUNK_INTERVAL )

        # modifie les fruits selon les collisions détectées
        self._collision_helper.process_collisions( self._fruits, self._is_gameover )

        # check
        offscreen = {f for f in self._fruits.values() if f.is_offscreen() }
        if( offscreen ):
            self.gameover()
            print( "WARNING balles en dehors du jeu !" )



    def on_draw(self):
        assert fruit.active_count() - len(self._fruits) < 20 , "Ressource leak"

        # met a jour les positions des fruits 
        for f in self._fruits.values():
            f.update()

        # gere le countdown en cas  de débordement
        ids = self._walls.fruits_sur_maxline()
        self._countdown.update( ids )

        # met à jour l'affichage et détecte la fin de partie
        countdown_val, countdown_txt = self._countdown.status()

        if( countdown_val < 0 and not self._is_gameover ):
            self.gameover()

        # l'ordre des conditions définit la priorité des messages
        game_status = ""
        if( self._is_autoplay ):  game_status = "AUTOPLAY"
        if( countdown_txt ):      game_status = countdown_txt
        if( self._is_paused ):    game_status = "PAUSE"
        if( self._is_gameover ):  game_status = "GAME OVER"

        #self._labels.update( gui.TOP_LEFT, f"fruits {len(self._fruits)}" )
        self._labels.update( gui.TOP_LEFT, f"score {self._score}" )
        self._labels.update( gui.TOP_RIGHT, f"FPS {self.pymunk_speedmeter.value:.0f}" )
        self._labels.update( gui.TOP_CENTER, game_status )

        # met à jour l'affichage
        self.clear()
        sprites.batch().draw()
        self.fps_display.draw()


    def on_key_press(self, symbol, modifiers):
        #print(f"key {symbol} was pressed")

        # ESC ferme le jeu dans tous les cas
        if(symbol == pg.window.key.ESCAPE):
            self.close()
        # n'importe quelle autre touche que ESC relance une partie si gameover
        elif(self._is_gameover):
            self.reset_game()
        # A controle l'autoplay
        elif(symbol == pg.window.key.A):
            self.toggle_autoplay()
        # SPACE met le jeu en pause
        elif(symbol == pg.window.key.SPACE):
            self._is_paused = not self._is_paused
        else:
            return pg.event.EVENT_UNHANDLED
        
        return pg.event.EVENT_HANDLED


    def on_mouse_press(self, x, y, button, modifiers):
        # relance une partie si la précédente est terminée
        if( self._is_gameover ):
            self.reset_game()

        # laĉhe le next_fruit
        if( (button & pg.window.mouse.LEFT) and self._next_fruit and not self._is_gameover ):
            self._next_fruit.set_x( x )
            self._next_fruit.normal()
            self._next_fruit = None
            if( not self._is_autoplay ):
                pg.clock.schedule_once( self.add_next_fruit, delay=NEXT_FRUIT_INTERVAL)

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

