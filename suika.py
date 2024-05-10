
import pyglet as pg
import pymunk as pm

from constants import *
from bocal import Bocal
from fruit import ActiveFruits
import gui
from collision import CollisionHelper
import utils
from preview import FruitQueue
import sprites

AUTOPLAY_RANDOM ='random'

class SuikaWindow(pg.window.Window):
    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        super().__init__(width=width, height=height, resizable=True, )
        self._space = pm.Space( )
        self._space.gravity = (0, GRAVITY)
        self._bocal = Bocal(space=self._space, **utils.bocal_coords( window_w=width, window_h=height) )
        self._preview = FruitQueue(cnt=PREVIEW_COUNT)
        self._fruits = ActiveFruits( space=self._space, width=width, height=height )
        self._countdown = utils.CountDown()
        self._gui = gui.GUI( window_width=width, window_height=height )
        self._collision_helper = CollisionHelper(self._space)
        #pg.clock.schedule( self.simulation_step )
        pg.clock.schedule_interval( self.simulation_step, interval=PYMUNK_INTERVAL )
        pg.clock.schedule_interval( self.autoplay, interval=AUTOPLAY_INTERVAL)
        self.display_fps = utils.Speedmeter()        
        self.pymunk_fps = utils.Speedmeter(bufsize=500)

        self.set_caption("Pastèque")
        self.set_minimum_size( width = 2 * BOCAL_MARGIN_SIDE + BOCAL_MIN_WIDTH,
                               height = BOCAL_MARGIN_TOP + BOCAL_MARGIN_BOTTOM + BOCAL_MIN_HEIGHT )
        self.reset_game()

    def reset_game(self):
        self._is_gameover = False
        self._is_paused = False
        self._autoplay = None
        self._is_mouse_shake = False
        self._is_benchmark_mode = False
        self._left_click_start = None
        self._mouse_drag_x = None
        self._bocal.reset()
        self._preview.reset()
        self._fruits.reset()
        self._collision_helper.reset()
        self._gui.reset()
        self._countdown.update( deborde=False )
        self.prepare_next( )


    def toggle_benchmark_mode( self ):
        pg.clock.unschedule( self.simulation_step )
        self._is_benchmark_mode = not self._is_benchmark_mode
        if( self._is_benchmark_mode ):
            pg.clock.schedule( self.simulation_step )
        else:
            pg.clock.schedule_interval( self.simulation_step, interval=PYMUNK_INTERVAL )

    def prepare_next(self):
        kind = self._preview.get_next_fruit()
        self._fruits.prepare_next( kind=kind )


    def drop(self, x):
        next = self._fruits.peek_next()
        if( not next ):
            return
        margin=next.radius + WALL_THICKNESS/2 + 1

        # position de la souris ou random si x = None 
        if( x is None ):
            pos = self._bocal.drop_point_random( margin=margin )
        else:
            pos = self._bocal.drop_point_from_clic( x, margin=margin )

        # pos==None si clic hors du bocal
        if( not pos ):
            return
        self._fruits.drop_next(pos)
        self.prepare_next()


    def autoplay(self, dt):
        if( self._is_paused or self._is_gameover ):
            return
        
        if( self._mouse_drag_x ):
            t = utils.now() - self._left_click_start 
            if( t > AUTOFIRE_DELAY ):
                self.drop(x=self._mouse_drag_x)
        elif( self._autoplay == AUTOPLAY_RANDOM ):
            self.drop(x=None)


    def gameover(self):
        """ Actions en cas de partie perdue
        """
        print("GAMEOVER")
        self._is_gameover = True    # inhibe les actions de jeu
        self._fruits.gameover()
        self._gui.show_gameover()


    def toggle_autoplay(self):
        assert( not self._is_gameover )
        if( not self._autoplay ):
            self._autoplay = AUTOPLAY_RANDOM
        elif( self._autoplay == AUTOPLAY_RANDOM):
            self._autoplay = None


    def toggle_pause(self):
        assert( not self._is_gameover )
        self._is_paused = not self._is_paused


    def set_mouse_shake( self, activate ):
        self._is_mouse_shake = bool(activate)


    def shoot_fruit(self, x, y):
        print(f"right click x={x} y={y}")
        qi = self._space.point_query( (x, y), max_distance=0, shape_filter=pm.ShapeFilter() )
        if( len(qi)==0 ):
            return
        if( len(qi) > 1):
            print("WARNING: pluiseurs fruits superposés ??")
        if( not hasattr( qi[0].shape, 'fruit' )):
           return
        f = qi[0].shape.fruit
        if( not self._is_gameover ):
            f.explose()


    def spawn_in_bocal(self, kind, bocal_coords):
        position = self._bocal.to_world( bocal_coords )
        self._fruits.spawn( kind, position )


    def simulation_step(self, dt):
        """Avance d'un pas la simulation physique
        appelé par un timer de window.on_draw()
        """
        self.pymunk_fps.tick_rel(dt)
        if( self._is_paused ):
            return

        fps = self.pymunk_fps.value
        if( fps>0 ):
            dt = 1.0 / fps

        # met à jour la position des éléments du bocal
        self._bocal.step(dt)
        # prepare le gestionnaire de collisions
        self._collision_helper.reset()
        # execute 1 pas de simulation physique
        #self._space.step( PYMUNK_INTERVAL )  
        self._space.step( dt )  

        # modifie les fruits selon les collisions détectées
        self._collision_helper.process( 
            spawn_func=self.spawn_in_bocal, 
            world_to_bocal_func=self._bocal.to_bocal )
        # menage 
        self._fruits.cleanup()


    def update(self):
        # gere le countdown en cas de débordement
        if( not self._bocal.is_tumbling):
            ids = self._bocal.fruits_sur_maxline()
            self._countdown.update( ids )

        # met à jour l'affichage et détecte la fin de partie
        countdown_val, countdown_txt = self._countdown.status()
        if( countdown_val < 0 and not self._is_gameover ):
            self.gameover()

        # l'ordre des conditions définit la priorité des messages
        game_status = ""
        if( self._autoplay ):     game_status = "AUTOPLAY"
        if( countdown_txt ):      game_status = countdown_txt
        if( self._is_paused ):    game_status = "PAUSE"
        if( self._is_gameover ):  game_status = "GAME OVER"

        self._gui.update_dict( {
            gui.TOP_LEFT: f"score {self._fruits._score}",
            gui.TOP_RIGHT: f"FPS {self.pymunk_fps.value:.0f} / {self.display_fps.value:.0f}",
            gui.TOP_CENTER: game_status } )


    def end_application(self):
        # self._bocal.delete()
        # self._preview.delete()
        # self._fruits.delete()
        # self._countdown.delete()
        # self._gui.delete()
        # self._collision_helper.delete()
        # self.display_fps.delete()
        # self.pymunk_fps.delete()
        self.close()


    def on_draw(self):

        # met a jour les positions des fruits et les widgets du GUI
        self._fruits.update()
        self._preview.update()
        self._bocal.update()
        self.update()

        # met à jour l'affichage
        self.clear()
        sprites.batch().draw()
        self.display_fps.tick()


    def on_key_press(self, symbol, modifiers):
        #print(f"key {symbol} was pressed")
        if(symbol == pg.window.key.D):        # DEBUG
            utils.print_counters()

        if(symbol == pg.window.key.ESCAPE):        # ESC ferme le jeu dans tous les cas
            self.end_application()
        elif(self._is_gameover or symbol==pg.window.key.R):    # n'importe quelle touche relance une partie apres un gameover
            self.reset_game()
        elif(symbol == pg.window.key.A):           # A controle l'autoplay
            self.toggle_autoplay()
        elif(symbol == pg.window.key.T):           # Mode machine à laver
            self._countdown.update( deborde=False )
            self._bocal.tumble_once()
        elif(symbol == pg.window.key.S):        # S secoue le bocal automatiquement
            self._bocal.shake_auto()
        elif(symbol == pg.window.key.SPACE):        # SPACE met en mode MOUSE_SHAKE
            self._bocal.shake_mouse()
            self.push_handlers( self._bocal.on_mouse_motion )
        elif(symbol == pg.window.key.P):        # P met le jeu en pause
            self.toggle_pause()
        elif(symbol == pg.window.key.G):        # G force un gameover en cours de partie
            self.gameover()
        elif(symbol == pg.window.key.B):        # Mode benchmark
            self.toggle_benchmark_mode()
        else:
            return pg.event.EVENT_UNHANDLED
        return pg.event.EVENT_HANDLED


    def on_key_release(self, symbol, modifiers):
        if(symbol == pg.window.key.SPACE):       # arrete de secouee le bocal automatiquement
            self._bocal.shake_stop()
            self.pop_handlers()
        if(symbol == pg.window.key.S):       # arrete de secouee le bocal automatiquement
            self._bocal.shake_stop()

    def on_mouse_press(self, x, y, button, modifiers):
        # relance une partie si la précédente est terminée
        if( self._is_gameover ):
            self.reset_game()
        elif( (button & pg.window.mouse.LEFT) ):
            self._left_click_start = utils.now()
            self._mouse_drag_x = x
            self.drop(x)
        elif( (button & pg.window.mouse.RIGHT) ):
            self.shoot_fruit(x, y)


    def on_mouse_release(self, x, y, button, modifiers):
        # relance une partie si la précédente est terminée
        if( (button & pg.window.mouse.LEFT) ):
            self._left_click_start = None
            self._mouse_drag_x = None


    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if( (buttons & pg.window.mouse.LEFT) ):
            #print( f"on_mouse_drag(x={x}, y={y}, dx={dx} dy={dy})")
            self._mouse_drag_x = x


    # def on_mouse_motion(self, x, y, dx, dy):
    #     print( f"on_mouse_motion(x={x}, y={y}, dx={dx} dy={dy})")

    # def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
    #     print(f"on_mouse_scroll(x={x} y={y} scroll_x={scroll_x} scroll_y={scroll_y}")


    def on_resize(self, width, height):
        """ met a jour les dimensions des objets
        """
        #print(f'The window was resized to {width}x{height}')
        self._bocal.on_resize( **utils.bocal_coords( window_w=width, window_h=height ) )
        self._fruits.on_resize(width, height)
        self._preview.on_resize(width, height)
        self._gui.on_resize(width, height)

        # nécessaire pour mettre à jour l'affichage
        super().on_resize(width, height)

def main():
    pg.resource.path = ['assets/']
    pg.resource.reindex()
    window = SuikaWindow()
    pg.app.run()

if __name__ == '__main__':
    main()

