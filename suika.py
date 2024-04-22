import random

import pyglet as pg
import pymunk as pm

from constants import *
import fruit, sprites, walls, gui
from fruit import Fruit
import utils


AUTOPLAY_FLOW = 1 + WINDOW_WIDTH // 750

class SuikaWindow(pg.window.Window):
    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        super().__init__(width, height)
        self._space = pm.Space( )
        self._space.gravity = (0, -100*GRAVITY)
        self._walls = walls.Walls(space=self._space, width=width, height=height)
        self._fruits = dict()
        self._next_fruit = None
        self._countdown = utils.CountDown()
        self._labels = gui.Labels( window_width=width, window_height=height )
        self._collision_helper = fruit.CollisionHelper(self._space)
        self.reset_game()
        pg.clock.schedule_interval( self.update, interval=PYMUNK_INTERVAL )
        pg.clock.schedule_interval( self.autoplay_spawn, interval=AUTOPLAY_INTERVAL)
        pg.clock.schedule_interval( self.cleanup_fruit_list, interval= 10*PYMUNK_INTERVAL )
        self.fps_display = pg.window.FPSDisplay(self)
        self.pymunk_speedmeter = utils.Speedmeter()


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


    def autoplay_spawn(self, dt):
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

    def autoplay_toggle(self):
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


    def check_offscreen(self):
        """ Supprime les fruits éventuellement sortis du jeu
        """
        for f in self._fruits.values():
            if f.is_offscreen():
                print( "WARNING {f} sorti du jeu." )
                f.remove()


    def update(self, dt):
        """Avance d'un pas la simulation physique
        """
        self.pymunk_speedmeter.tick_rel(dt)
        if( self._is_paused ):
            return

        # menage prealable
        self.check_offscreen()
        # prepare le gestionnaire de collisions
        self._collision_helper.reset()
        # execute 1 pas de simulation physique
        self._space.step( PYMUNK_INTERVAL )  
        # modifie les fruits selon les collisions détectées
        self._collision_helper.process_collisions( self._fruits, self._is_gameover )


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

        if(symbol == pg.window.key.ESCAPE):        # ESC ferme le jeu dans tous les cas
            self.close()
        elif(self._is_gameover):    # n'importe quelle touche relance une partie apres un gameover
            self.reset_game()
        elif(symbol == pg.window.key.A):           # A controle l'autoplay
            self.autoplay_toggle()
        elif(symbol == pg.window.key.SPACE):        # SPACE met le jeu en pause
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

