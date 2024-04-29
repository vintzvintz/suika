import random

import pyglet as pg
import pymunk as pm

from constants import *
from walls import Walls
from fruit import ActiveFruits
import gui
from collision import CollisionHelper
import utils
from preview import FruitQueue
import sprites



class SuikaWindow(pg.window.Window):
    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        super().__init__(width, height)
        self._space = pm.Space( )
        self._space.gravity = (0, -100*GRAVITY)
        self._walls = Walls(space=self._space, width=width, height=height)
        self._preview = FruitQueue(cnt=PREVIEW_COUNT)
        self._fruits = ActiveFruits( space=self._space )

        self._countdown = utils.CountDown()
        self._labels = gui.Labels( window_width=width, window_height=height )
        self._collision_helper = CollisionHelper(self._space)
        self.reset_game()
        pg.clock.schedule_interval( self.update_pymunk, interval=PYMUNK_INTERVAL )
        pg.clock.schedule_interval( self.autoplay, interval=AUTOPLAY_INTERVAL)
        self.display_fps = utils.Speedmeter()
        self.pymunk_fps = utils.Speedmeter()


    def reset_game(self):
        self._is_gameover = False
        self._is_paused = False
        self._is_autoplay = False
        self._preview.reset()
        self._fruits.reset()
        self._collision_helper.reset()
        self._labels.reset()
        self._countdown.update( deborde=False )
        self.prepare_next( )


    def prepare_next(self):
        kind = self._preview.get_next_fruit()
        self._fruits.prepare_next( kind=kind )


    def autoplay(self, dt):
        if( not self._is_autoplay or self._is_paused or self._is_gameover ):
            return
        self._fruits.autoplay_once(nb=AUTOPLAY_FLOW)


    def gameover(self):
        """ Actions en cas de partie perdue
        """
        print("GAMEOVER")
        self._is_gameover = True    # inhibe les actions de jeu
        self._fruits.gameover()
        self._labels.show_gameover()


    def toggle_autoplay(self):
        assert( not self._is_gameover )
        self._is_autoplay = not self._is_autoplay
        if( self._is_autoplay ):
            self._fruits.remove_next()
        if( not self._is_autoplay ):
            self.prepare_next()


    def toggle_pause(self):
        assert( not self._is_gameover )
        self._is_paused = not self._is_paused


    def shoot_fruit(self, x, y):
        qi = self._space.point_query( (x, y), max_distance=0, shape_filter=pm.ShapeFilter() )
        if( len(qi)>0 ):
            f = qi[0].shape.fruit
            self._fruits.remove(f.id)
            print(f"shooted {f} at x={x} y={y}")


    def update_pymunk(self, dt):
        """Avance d'un pas la simulation physique
        appelé par un timer dedié indépendant et plus rapide que window.on_draw()
        """
        self.pymunk_fps.tick_rel(dt)
        if( self._is_paused ):
            return
        # prepare le gestionnaire de collisions
        self._collision_helper.reset()
        # execute 1 pas de simulation physique
        self._space.step( PYMUNK_INTERVAL )  
        # modifie les fruits selon les collisions détectées
        self._collision_helper.process( spawn_func=self._fruits.spawn )
        # menage 
        self._fruits.cleanup()


    def update_gui(self):
        # gere le countdown en cas de débordement
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
        self._labels.update( gui.TOP_LEFT, f"score {self._fruits._score}" )
        self._labels.update( gui.TOP_RIGHT, f"FPS {self.pymunk_fps.value:.0f} / {self.display_fps.value:.0f}" )
        self._labels.update( gui.TOP_CENTER, game_status )


    def on_draw(self):
        if( utils.g_fruit_cnt.cnt - len(self._fruits) > 5 ):
            print( f"Ressource leak {utils.print_counters()}" )

        # met a jour les positions des fruits et les widgets du GUI
        self._fruits.update()
        self.update_gui()

        # met à jour l'affichage
        self.clear()
        sprites.batch().draw()
        self.display_fps.tick()


    def on_key_press(self, symbol, modifiers):
        #print(f"key {symbol} was pressed")
        if(symbol == pg.window.key.S):        # DEBUG
            utils.print_counters()

        if(symbol == pg.window.key.ESCAPE):        # ESC ferme le jeu dans tous les cas
            self.close()
        elif(self._is_gameover or symbol==pg.window.key.R):    # n'importe quelle touche relance une partie apres un gameover
            self.reset_game()
        elif(symbol == pg.window.key.A):           # A controle l'autoplay
            self.toggle_autoplay()
        elif(symbol == pg.window.key.SPACE):        # SPACE met le jeu en pause
            self.toggle_pause()
        else:
            return pg.event.EVENT_UNHANDLED
        return pg.event.EVENT_HANDLED


    def on_mouse_press(self, x, y, button, modifiers):
        # relance une partie si la précédente est terminée
        if( self._is_gameover ):
            self.reset_game()
            return

        # laĉhe le next_fruit
        if( (button & pg.window.mouse.LEFT) and not self._is_gameover ):
            self._fruits.play_next(x=x)
            if( not self._is_autoplay ):
                pg.clock.schedule_once( lambda dt: self.prepare_next(), delay=NEXT_FRUIT_INTERVAL)

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

