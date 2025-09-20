"""Main game module containing the SuikaWindow class and game logic."""

import pyglet as pg
import pymunk as pm

from .core.constants import *
from .physics.bocal import Bocal
from .physics.fruit import ActiveFruits
from .ui import gui
from .physics.collision import CollisionHelper
from .core import utils
from .ui.preview import FruitQueue
from .graphics import sprites


class Autoplayer(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self._rate = 0
        self.disable()

    def get_rate(self):
        return self._rate

    def enable(self):
        if( not self._enabled ):
            self._enabled = True
            if( self._rate==0 ):
                self._rate = AUTOPLAY_INITIAL_RATE

    def disable(self):
        self._time_debt = 0
        self._enabled = False

    def toggle(self):
        if( not self._enabled ):
             self.enable()
        else:
            self.disable()

    def adjust_rate( self, adj ):
        self._time_debt = 0
        if( adj>0 and self._rate==0 ):
            self._rate = AUTOPLAY_INITIAL_RATE
        else:
            self._rate = max( 0, self._rate+adj )
        print(f"autoplayer rate = {self._rate} fruits/sec")

    def step(self, dt):
        # appelé à chaque frame
        # renvoie le nombre de fruits à lacher sur la frame courante
        if( not self._enabled or self._rate == 0 ):
            return 0
        t = self._time_debt + dt
        nb = int( t * self._rate )
        self._time_debt = t - nb/self._rate
        return nb


class MouseState(object):
    """
    Utilitaire pour suivre l'état de la souris (position, boutons)
    """

    def __init__(self, window):
        # callbacks
        self.on_autofire_stop = None
        self.on_fruit_drag = None

        window.push_handlers(
            self.on_mouse_motion,
            self.on_mouse_drag,
            self.on_mouse_press,
            self.on_mouse_release )
        self.reset()

    def reset(self):
        self._autofire_on = False
        self._left_click_start = None
        self.position = None


    @property
    def autofire(self):
        if( not self._left_click_start ):
            return False
        if( not self._autofire_on ):
            t = utils.now() - self._left_click_start
            if( t > AUTOFIRE_DELAY ):
                self._autofire_on = True
        return self._autofire_on


    def on_mouse_press(self, x, y, button, modifiers):
        ret = pg.event.EVENT_UNHANDLED

        if( self._autofire_on ):                     # arrete l'autofire/autoplay lorsqu'il est actif
            self._autofire_on = False
            if( self.on_autofire_stop ):
                self.on_autofire_stop()
            ret = pg.event.EVENT_HANDLED             # pour eviter de dropper un fruit sur la partie suivante

        if( (button & pg.window.mouse.LEFT) ):      # note le moment du début du clic
            self._left_click_start = utils.now()
            self.position = (x, y)
        return ret


    def on_mouse_release(self, x, y, button, modifiers):
        if( (button & pg.window.mouse.LEFT) ):
            if( not self._autofire_on ):
                self._left_click_start = None


    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if( (buttons & pg.window.mouse.LEFT) ):
            #print( f"on_mouse_drag(x={x}, y={y}, dx={dx} dy={dy})")
            self._set_pos(x, y)


    def on_mouse_motion(self, x, y, dx, dy):
        self._set_pos(x, y)


    def _set_pos(self, x, y):
        self.position = (x, y)
        if( self.on_fruit_drag ):
            self.on_fruit_drag( x, y )


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
        self._autoplayer = Autoplayer()
        pg.clock.schedule_interval( self.simulation_tick, interval=PYMUNK_INTERVAL )
        pg.clock.schedule_interval( self.autoplay_tick, interval=AUTOPLAY_INTERVAL_BASE)
        self.display_fps = utils.Speedmeter()
        self.pymunk_fps = utils.Speedmeter(bufsize= int(3/PYMUNK_INTERVAL) )

        self._mouse_state = MouseState( window=self )
        self._mouse_state.on_autofire_stop = self._autoplayer.disable

        self.set_caption("Pastèque")
        self.set_minimum_size( width = 2 * BOCAL_MARGIN_SIDE + BOCAL_MIN_WIDTH,
                               height = BOCAL_MARGIN_TOP + BOCAL_MARGIN_BOTTOM + BOCAL_MIN_HEIGHT )
        self.reset_game()

    def reset_game(self):
        self._is_gameover = False
        self._is_paused = False
        self._autoplay_txt = ""
        self._is_mouse_shake = False
        self._is_benchmark_mode = False
        self._dragged_fruit = None
        self._bocal.reset()
        self._preview.reset()
        self._fruits.reset()
        self._collision_helper.reset()
        self._countdown.reset()
        self._gui.reset()
        self._autoplayer.reset()
        self._mouse_state.reset()
        self.prepare_next()


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


    def drop(self, cursor_x, nb=1):
        for _ in range(nb):
            next = self._fruits.peek_next()
            if( not next ):
                return
            margin=next.radius + WALL_THICKNESS/2 + 1

            # position de la souris ou random si x = None
            if( cursor_x is None ):
                pos = self._bocal.drop_point_random( margin=margin )
            else:
                pos = self._bocal.drop_point_cursor( cursor_x, margin=margin )

            if( not pos ):            # pos==None si clic hors du bocal
                return
            self._fruits.drop_next(pos)
            self.prepare_next()


    def autoplay_tick(self, dt):
        if( self._is_paused or self._is_gameover ):
            self._autoplay_txt = ""
            return
        msg = []
        nb = self._autoplayer.step(dt)
        # autofire ( = autoplay contrôlé à la souris )
        if( self._mouse_state.autofire ):
            self._autoplayer.enable()   # active l'autoplay
            pos = self._mouse_state.position    # None si le pointeur est en dehors de la fenetre
            if(pos):
                self.drop(cursor_x=self._mouse_state.position[0], nb=nb)
                msg.append(f"AUTOFIRE")
        # autoplay ( drop sur emplacement random )
        elif( self._autoplayer._enabled):
            self.drop(nb=nb, cursor_x=None)
            msg.append(f"AUTOPLAY")

        # ajoute le débit de l'autoplay/autofire seulement si actif.
        if(len(msg)):
            msg.append(f"{self._autoplayer.get_rate()} fruits/sec")
        self._autoplay_txt = ' '.join(msg)


    def gameover(self):
        """ Actions en cas de partie perdue
        """
        print("GAMEOVER")
        self._is_gameover = True    # inhibe les actions de jeu
        self._autofire_on = False
        self._fruits.gameover()
        self._gui.show_gameover()


    def toggle_pause(self):
        assert( not self._is_gameover )
        self._is_paused = not self._is_paused


    def set_mouse_shake( self, activate ):
        self._is_mouse_shake = bool(activate)


    def fruit_drag_start(self):
        # passe le fruit sous la souris en mode DRAG
        cursor = self._mouse_state.position
        self._dragged_fruit = self.find_fruit_at( *cursor )
        if( self._dragged_fruit) :
            self._dragged_fruit.drag_mode( cursor )   # set_mode


    def fruit_drag_stop(self):
        if( self._dragged_fruit ):
            self._dragged_fruit.drag_mode( None )   # set_mode
            self._dragged_fruit = None


    def find_fruit_at(self, x, y):
        qi = self._space.point_query( (x, y), max_distance=0, shape_filter=pm.ShapeFilter() )
        if( len(qi)==0 ):
            return None
        if( len(qi) > 1):
            print("WARNING: pluisieurs fruits superposés ??")
        if( not hasattr( qi[0].shape, 'fruit' )):
           return None     # la forme n'est pas un fruit (ex: bocal)
        return qi[0].shape.fruit


    def shoot_fruit(self, x, y):
        print(f"right click x={x} y={y}")
        f = self.find_fruit_at(x, y)
        if( not self._is_gameover and f ):
            f.explose()


    def spawn_in_bocal(self, kind, bocal_coords):
        position = self._bocal.to_world( bocal_coords )
        self._fruits.spawn( kind, position )


    def simulation_tick(self, dt):
        """Avance d'un pas la simulation physique
        appelé par un timer de window.on_draw()
        """
        self.pymunk_fps.tick_rel(dt)
        if( self._is_paused ):
            return

        # met à jour la position des éléments du bocal
        self._bocal.step(dt)
        # met à jour le fruit en DRAG_MODE
        if( self._dragged_fruit ):
            self._dragged_fruit.drag_to( self._mouse_state.position, dt)
        # prepare le gestionnaire de collisions
        self._collision_helper.reset()
        # execute 1 pas de simulation physique
        self._space.step( PYMUNK_INTERVAL )

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

        # met à jour l'affichage et détecte la fin de partie
        countdown_val, countdown_txt = self._countdown.status()
        if( countdown_val < 0 and not self._is_gameover ):
            self.gameover()

        # l'ordre des conditions définit la priorité des messages
        game_status = ""
        if( True ):               game_status = self._autoplay_txt
        if( countdown_txt ):      game_status = countdown_txt
        if( self._is_paused ):    game_status = "PAUSE"
        if( self._is_gameover ):  game_status = "GAME OVER"

        self._gui.update_dict( {
            #gui.TOP_LEFT: f"Fruits {len(self._fruits._fruits)}",
            gui.TOP_LEFT: f"score {self._fruits._score}",
            gui.TOP_RIGHT: f"FPS {self.pymunk_fps.value:.0f} / {self.display_fps.value:.0f}",
            gui.TOP_CENTER: game_status } )


    def end_application(self):
        # TODO : liberer plus proprement toutes les autres ressources
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
        if(symbol == pg.window.key.D):              # DEBUG
            print(f"autoplayer enabled={self._autoplayer._enabled} autofire_on={self._autofire_on} rate={self._autoplayer.get_rate()}")
        if(symbol == pg.window.key.ESCAPE):         # ESC ferme le jeu dans tous les cas
            self.end_application()
        elif(self._is_gameover or symbol==pg.window.key.R):    # relance une partie apres un gameover
            self.reset_game()
        elif(symbol == pg.window.key.A):            # A controle l'autoplay
            self._autoplayer.toggle()
        elif(symbol == pg.window.key.T):            # Mode machine à laver
            self._countdown.reset( )
            self._bocal.tumble_once()
        elif(symbol == pg.window.key.S):            # S secoue le bocal automatiquement
            self._bocal.shake_auto()
        elif(symbol == pg.window.key.SPACE):        # SPACE met en mode MOUSE_SHAKE
            self._bocal.shake_mouse()
            self.push_handlers( self._bocal.on_mouse_motion )
        elif(symbol == pg.window.key.M):            # deplace un fruit à la souris
            self.fruit_drag_start()
        elif(symbol == pg.window.key.P):            # P met le jeu en pause
            self.toggle_pause()
        elif(symbol == pg.window.key.G):            # G force un gameover en cours de partie
            self.gameover()
        elif(symbol == pg.window.key.B):            # Mode benchmark
            self.toggle_benchmark_mode()


    def on_key_release(self, symbol, modifiers):
        if(symbol == pg.window.key.SPACE):          # arrete la secousse manuelle
            self._bocal.shake_stop()
            self.pop_handlers()
        elif(symbol == pg.window.key.S):            # arrete la secousse automatique
            self._bocal.shake_stop()
        elif(symbol == pg.window.key.M):            # relache le fruit après un deplacement à la souris
            self.fruit_drag_stop()


    def on_mouse_press(self, x, y, button, modifiers):
        if( self._is_gameover ):
            self.reset_game()
        elif( (button & pg.window.mouse.LEFT) ):
            self.drop(x)
        elif( (button & pg.window.mouse.RIGHT) ):
            self.shoot_fruit(x, y)


    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        #print(f"on_mouse_scroll(x={x} y={y} scroll_x={scroll_x} scroll_y={scroll_y}    => lvl={self._autoplay_level}")
        self._autoplayer.adjust_rate(scroll_y)


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