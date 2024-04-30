import random

import pyglet as pg
import pymunk as pm

from constants import *
import utils

from sprites import VISI_NORMAL, VISI_HIDDEN
from sprites import FruitSprite, ExplosionSprite


_FRUITS_DEF = [
    # le rang dans cette liste sert de kind/points/collision_type;
    # valeur 0 réservée aux types sans handlers.
    None,       
    {'mass':5,  'radius':30,  'name':'cerise' },
    {'mass':7,  'radius':40,  'name':'fraise' },
    {'mass':10, 'radius':55,  'name':'prune' },
    {'mass':12, 'radius':70,  'name':'abricot' },
    {'mass':15, 'radius':90,  'name':'orange' },
    {'mass':20, 'radius':120, 'name':'tomate' },
    {'mass':25, 'radius':130, 'name':'pamplemousse' },
    {'mass':30, 'radius':150, 'name':'pomme' },
    {'mass':37, 'radius':190, 'name':'ananas' },
    {'mass':40, 'radius':230, 'name':'melon' },
    {'mass':50, 'radius':200, 'name':'pasteque' },
]

_FRUITS_RANDOM = [ 1,2,3,4 ]

def nb_fruits():
    return len(_FRUITS_DEF) - 1

MODE_WAIT = 'wait'
MODE_FIRST_DROP = 'first_drop'
MODE_NORMAL = 'normal'
MODE_MERGE = 'merge'
MODE_REMOVED = 'removed'

SPRITE_MAIN = "sprite_main"
SPRITE_EXPLOSION = "sprite_explosion"

COLLISION_CAT = 'coll_cat'
COLLISION_MASK = 'coll_mask'
BODY_TYPE = 'body_type'
VISI = 'visi'

_FRUIT_MODES = {
    MODE_WAIT: {
        COLLISION_CAT: CAT_FRUIT_WAIT,
        COLLISION_MASK: 0x00, # collision avec les murs uniqement
        VISI: VISI_NORMAL,
        BODY_TYPE: pm.Body.KINEMATIC
    },
    MODE_FIRST_DROP: {
        COLLISION_CAT: CAT_FRUIT_DROP,
        COLLISION_MASK: CAT_FRUIT, # collision avec les fruits et les murs, mais pas avec MAXLINE ni autres fruits FIRST_DROP
        VISI: VISI_NORMAL,
        BODY_TYPE: pm.Body.KINEMATIC
    },
    MODE_NORMAL: {
        COLLISION_CAT: CAT_FRUIT,
        COLLISION_MASK: CAT_FRUIT_DROP | CAT_FRUIT | CAT_MAXLINE,
        VISI: VISI_NORMAL,
        BODY_TYPE: pm.Body.DYNAMIC
    },
    MODE_MERGE: {
        COLLISION_CAT: CAT_FRUIT_MERGE,
        COLLISION_MASK: 0x00,   # collision avec les murs uniqement
        VISI: VISI_NORMAL,
        BODY_TYPE: pm.Body.KINEMATIC
    },
    MODE_REMOVED: {
        COLLISION_CAT: CAT_FRUIT_REMOVED,
        COLLISION_MASK: 0x00,   # collision avec les murs uniqement
        VISI: VISI_HIDDEN,
        BODY_TYPE: pm.Body.KINEMATIC
    }
}


_g_fruit_id = 0
def _get_new_id():
    global _g_fruit_id
    _g_fruit_id +=1
    return _g_fruit_id


# POUR DEBUG transitions old-> new valides
g_valid_transitions = {
    MODE_WAIT : ( MODE_FIRST_DROP, MODE_NORMAL, MODE_MERGE, MODE_REMOVED ),    # mode initial à la creation
    MODE_FIRST_DROP : (MODE_NORMAL, MODE_MERGE, MODE_REMOVED),
    MODE_NORMAL : (MODE_MERGE, MODE_REMOVED),
    MODE_MERGE : ( MODE_REMOVED,),
    MODE_REMOVED : ( MODE_REMOVED,)
}


def random_kind():
    return random.choice( _FRUITS_RANDOM )

def name_from_kind(kind):
    return _FRUITS_DEF[kind]["name"]


class AnimatedCircle( pm.Circle ):
    def __init__(self, **kwargs ):
        super().__init__(**kwargs)
        self._grow_start = None
        self._radius_ref = self.radius
    
    def grow_start( self ):
        """lance une animation qui fait varier le rayon en fonction du temps
        """
        if( self._grow_start is None ):
            self._grow_start = utils.now()

    def update_animation(self):
        """modifie le rayon du cercle
        """
        if( not self._grow_start ):
            return
        t = utils.now()-self._grow_start
        x = t * (1-FADE_SIZE)/ FADEIN_DELAY + FADE_SIZE
        self.unsafe_set_radius( self._radius_ref * min(1, x) )
        if( x > 1 ):
            self._grow_start = None


class Fruit( object ):
    def __init__(self, space, on_remove=None, kind=0, position=None, mode=MODE_WAIT, refcnt=None):
        self._refcnt_f = utils.g_fruit_cnt
        self._refcnt_f.inc()

        # espece aléatoire si non spécifiée
        assert kind<=nb_fruits(), "type de fruit inconnu"
        if( kind<=0 ):
            kind = random_kind()
        fruit_def = _FRUITS_DEF[kind]

        # position par défaut
        if( not position ):
            x = WINDOW_WIDTH//2
            y = WINDOW_HEIGHT-WINDOW_MAXLINE_MARGIN +  fruit_def['radius'] + 5
            position = pm.Vec2d(x,y)

        self._id = _get_new_id()
        self._kind = kind
        self._space = space
        self._on_remove = on_remove
        self._body, self._shape = self._make_shape(
            radius=fruit_def['radius'],
            mass=fruit_def['mass'], 
            position=position)
        self._shape.collision_type = kind
        space.add(self._body, self._shape)

        self._sprites = { 
            SPRITE_MAIN : FruitSprite( 
                nom=fruit_def['name'], 
                r=fruit_def['radius'] )
        }
        self._fruit_mode = None
        self._dash_start_time = None
        self._set_mode( mode )
        #print( f"{self}.__init__()" )
        print( f"{self} created" )


    def __del__(self):
        self._refcnt_f.dec()
        #print( f"__del__({self})")
        assert(    self._body is None 
               and self._shape is None 
               and len(self._sprites)==0
               and self._fruit_mode == MODE_REMOVED), "ressources non libérées"


    def __repr__(self):
        return f"{_FRUITS_DEF[self._kind]['name']}#{self._id}"


    def _make_shape(self, radius, mass, position):
        """ cree le body/shape pymunk pour la simulation physique
        """
        body = pm.Body(body_type = pm.Body.KINEMATIC)
        body.position = position
        shape = AnimatedCircle(body=body, radius=radius)
        shape.mass = mass
        shape.friction = FRICTION
        shape.elasticity = ELASTICITY_FRUIT
        #  ajoute fruit_id comme attribut custom de l'objet pymunk 
        shape.fruit = self
        return body, shape


    def release_ressources(self):
        if( not self.removed ):
            print( f"WARNING: {self} delete() avec mode différent de MODE_REMOVED ({self._fruit_mode})" )
        # remove pymunk objects and local references
        if( self._body or self._shape):
            #print( f"{self}.delete()")
            self._space.remove( self._body, self._shape )
            self._body = self._shape = None
        # should call sprite.delete()
        self._sprites = {}   


    @property
    def id(self):
        return self._id

    @property
    def kind(self):
        return self._kind

    @property
    def scalar_velocity(self):
        return self._body.velocity.length

    @property
    def points(self):
        return self._kind

    @property
    def removed(self):
        return self._fruit_mode == MODE_REMOVED
    
    @property
    def position(self):
        return self._body.position

    def _is_deleted(self):
        return (self._body==None 
            and self._shape==None
            and self._sprites==None )


    def _set_mode(self, mode):
        # debug
        # old = self._fruit_mode
        # log = f"{self} mode {self._fruit_mode}->{mode}"
        # if( old and mode not in g_valid_transitions[old] ):
        #     log += " INVALIDE"
        # print(log)
        if(self.removed):
            return

        self._fruit_mode = mode
        attrs = _FRUIT_MODES[self._fruit_mode]

        # DYNAMIC ou KINEMATIC
        self._body.body_type = attrs[BODY_TYPE]

        # sprites visibility
        for s in self._sprites.values( ):
            s.visibility = attrs[VISI]

        # modifie les règkes de collision
        self._shape.filter = pm.ShapeFilter(
            categories= attrs[COLLISION_CAT],
            mask = attrs[COLLISION_MASK] | CAT_WALLS )  # collision systematique avec les murs


    def update(self):
        """met à jour le sprite du fruit à partir de la simulation physique et autres
        """
        if( self.removed or self._is_deleted() ):
            return
        (x, y) = self._body.position
        degres = -180/3.1416 * self._body.angle  # pymunk et pyglet ont un sens de rotation opposé
        for s in self._sprites.values():
            s.update( x=x, y=y, rotation=degres, on_animation_stop=None )
        self._shape.update_animation()
        

    def set_position(self, x, y):
        assert( self._body.body_type == pm.Body.KINEMATIC ), "disponible seulement sur le fruit en attente"
        assert( not y or (y>0 and y<WINDOW_HEIGHT))
        # contrainte à l'interieur du jeu
        x = max(x, self._shape.radius )
        x = min(x, WINDOW_WIDTH - self._shape.radius)
        (x0, y0) = self._body.position
        if y is None:
            y = y0
        self._body.position = ( x, y )


    def blink(self, activate, delay=0):
        if(not activate):
            self._sprites[SPRITE_MAIN].blink = False
        elif( not self._sprites[SPRITE_MAIN].blink ):
            self._sprites[SPRITE_MAIN].blink = True


    def drop(self,x):
        """met l'objet en mode dynamique pour qu'il tombe et active les collisions"""
        self.set_position(x=x, y=None)
        self._body.velocity = (0, -INITIAL_VELOCITY)
        self._set_mode( MODE_FIRST_DROP )
        self._shape.collision_type = COLLISION_TYPE_FIRST_DROP


    def normal(self):
        """met l'objet en mode dynamique pour qu'il tombe et active les collisions"""
        self._set_mode( MODE_NORMAL )
        self._shape.collision_type = self._kind


    def fade_in(self):
        """ fait apparaitre le sprite avec un effet d'agrandissement et de transparence
        """
        if(self.removed):
            return
        #print( f"{self}.fade_in()")
        self.normal()
        self._sprites[SPRITE_MAIN].fadein = True
        self._shape.grow_start()


    def fade_out(self):
        assert( self._body.body_type == pm.Body.KINEMATIC )
        self.normal()
        self._sprite[SPRITE_MAIN].fadeout = True


    def merge_to(self, dest):
        if( self._fruit_mode==MODE_MERGE):
            return
        self._set_mode( MODE_MERGE )  # plus de collisions avec les fruits
        (x0, y0) = self._body.position
        (x1, y1) = dest
        v = ((x1-x0)/MERGE_DELAY, (y1-y0)/MERGE_DELAY)
        self._body.velocity = v
        pg.clock.schedule_once(lambda dt : self.remove(), delay=MERGE_DELAY )
    

    def explose(self):
        if( self._fruit_mode in [MODE_MERGE, MODE_REMOVED] ):
            return
        self._set_mode(MODE_MERGE)
        explo = ExplosionSprite( 
            r=self._shape.radius, 
            on_explosion_end=self.remove)
        explo.position = ( *self._body.position, 1)
        self._sprites[SPRITE_EXPLOSION] = explo
        self._sprites[SPRITE_MAIN].fadeout = True

    def is_offscreen(self) -> bool :
        if self._is_deleted():
            return False
        x, y = self._body.position
        return   (x < 0) or (y < 0) or (x>WINDOW_WIDTH) or (y>WINDOW_HEIGHT)
    
    # retire le fruit du jeu. l'objet ne doit plus être utilisé ensuite.
    def remove(self):
        # callback optionnel ( ex: gestion du score )
        if(self._on_remove ):
            self._on_remove( self )
        self._set_mode(MODE_REMOVED)
        self.release_ressources()


class ActiveFruits(object):

    def __init__(self, space):
        self._space = space
        self._fruits = dict()
        self._score = 0
        self._next_fruit = None
        self._is_gameover = False

    def __len__(self):
        return len(self._fruits)


    def reset(self):
        self._is_gameover = False
        self.remove_all()
        self.remove_next()
        self._score = 0
        pg.clock.unschedule( self.explose_seq )

    def update(self):
        if( self._next_fruit ):
            self._next_fruit.update()
        for f in self._fruits.values():
            f.update()

    def prepare_next(self, kind):
        """Cree un fruit en attente de largage
        """
        assert( not self._is_gameover )
        if( self._next_fruit ):
            print("next_fruit deja present")
            return
        self._next_fruit = Fruit(space=self._space, kind=kind, on_remove=self.on_remove)
        # self.add() appelé dans play_next()

    def play_next(self, x):
        if( (not self._next_fruit) or self._is_gameover ):
            return
        self._next_fruit.drop(x=x)
        self.add( self._next_fruit )
        self._next_fruit = None

    def remove(self, id):
        points = 0
        if id in self._fruits:
            points = self._fruits[id].points
            self._fruits[id].remove()
        return points

    def remove_all(self):
        points = 0
        for id in self._fruits:
            points += self.remove(id)
        self.cleanup()
        return points

    def remove_next(self):
        if( self._next_fruit ):
            self._next_fruit.remove()
            self._next_fruit = None

    def autoplay_once(self, nb):
        assert( not self._is_gameover )
        for _ in range(nb):
            f = Fruit( self._space, on_remove=self.on_remove )
            self.add(f)
            f.drop(x=random.randint(0, WINDOW_WIDTH))

    def spawn(self, kind, position):
        f =  Fruit( space = self._space,
                     kind=kind,
                     position=position,
                     on_remove=self.on_remove)
        self.add(f)
        f.fade_in()
        return f

    def on_remove(self, f):
        self._score += f.points

    def explose_seq(self, dt):
        """fait exploser les fruits en commençant par le plus récent
        """
        # cherche le fruit non explosé le plus ancien
        explosables = [ i for i,f in self._fruits.items() if f._fruit_mode in [MODE_NORMAL, MODE_FIRST_DROP] ]
        #print( f'reste {len(self._fruits)} fruits actifs dont {len(explosables)} explosables')
        if( explosables ):
            explosables.sort(reverse=True )
            self._fruits[explosables[0]].explose()
        # continue tant qu'il reste des fruits
        if( self._fruits ):
            pg.clock.schedule_once( self.explose_seq, GAMEOVER_ANIMATION_INTERVAL )

    def gameover(self):
        self._is_gameover = True
        self.remove_next()
        # programme l'explosion des fruits restants
        print( f'programme explosion finale pour {len(self._fruits)} fruits actifs')
        pg.clock.schedule_once( self.explose_seq, GAMEOVER_ANIMATION_START)

    def add(self, newfruit):
        self._fruits[ newfruit.id ] = newfruit

    def cleanup(self, all_fruits=False):
        """ garbage collection 
        """
        # retire les fruits sortis du jeu
        for f in self._fruits.values():
            if not f.removed and f.is_offscreen():
                print( f"WARNING {f} est sorti du jeu" )
                f.remove()

        # libere les ressources associées aux fruits retirés du jeu
        removed = [f.id for f in self._fruits.values() if (all_fruits or f.removed) ]
        for id in removed:
            self._fruits[id].release_ressources()
            del self._fruits[id]        # should trigger fruit.__del__()

