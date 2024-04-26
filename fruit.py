import random

import pyglet as pg
import pymunk as pm

from constants import *
import utils
import sprites
from sprites import VISI_NORMAL, VISI_GAMEOVER, VISI_HIDDEN


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

def nb_fruits():
    return len(_FRUITS_DEF) - 1

MODE_WAIT = 'wait'
MODE_NORMAL = 'normal'
MODE_EXPLOSE = 'explose'
MODE_GAMEOVER = 'gameover'
MODE_REMOVED = 'removed'

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
    MODE_NORMAL: {
        COLLISION_CAT: CAT_FRUIT,
        COLLISION_MASK: CAT_FRUIT | CAT_MAXLINE,
        VISI: VISI_NORMAL,
        BODY_TYPE: pm.Body.DYNAMIC
    },
    MODE_GAMEOVER: {
        COLLISION_CAT: CAT_FRUIT,
        COLLISION_MASK: CAT_FRUIT,
        VISI: VISI_GAMEOVER,
        BODY_TYPE: pm.Body.DYNAMIC
    },
    MODE_EXPLOSE: {
        COLLISION_CAT: CAT_FRUIT_EXPLOSE,
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

_g_fruit_cnt = 0
def _new_fruit():
    global _g_fruit_cnt
    _g_fruit_cnt += 1

def _del_fruit():
    global _g_fruit_cnt
    _g_fruit_cnt -= 1

def active_count():
    global _g_fruit_cnt
    return _g_fruit_cnt


# POUR DEBUG transitions old-> new valides
# g_valid_transitions = {
#     MODE_WAIT : ( MODE_NORMAL,MODE_REMOVED ),
#     MODE_NORMAL : (MODE_EXPLOSE, MODE_GAMEOVER,),
#     MODE_EXPLOSE : (MODE_GAMEOVER, MODE_REMOVED,),
#     MODE_GAMEOVER : (MODE_REMOVED,),
#     MODE_REMOVED : None
# }


class AnimatedCircle( pm.Circle ):
    def __init__(self, **kwargs ):
        super().__init__(**kwargs)
        self._grow_start = None
        self._radius_ref = self.radius
    
    def grow_start( self, coef_start=FADE_SIZE ):
        """lance une animation qui fait varier le rayon en fonction du temps
        """
        if( not hasattr(self, '_grow_start') or self._grow_start is None ):  # lazy initialisation
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
    def __init__(self, space, kind=0, position=None, mode=MODE_WAIT):
        _new_fruit()
        # espece aléatoire si non spécifiée
        assert kind<=nb_fruits(), "type de balle invalide"
        if( kind<=0 ):
            kind = random.randint(1,4)   
        fruit_def = _FRUITS_DEF[kind]

        # position par défaut
        if( not position ):
            x = WINDOW_WIDTH//2
            y = WINDOW_HEIGHT-WINDOW_MAXLINE_MARGIN -  fruit_def['radius'] - 5
            position = pm.Vec2d(x,y)

        self._id = _get_new_id()
        self._kind = kind
        self._space = space
        self._body, self._shape = self._make_shape(
            radius=fruit_def['radius'],
            mass=fruit_def['mass'], 
            position=position)
        self._shape.collision_type = kind
        space.add(self._body, self._shape)

        self._sprite = sprites.FruitSprite( 
            nom=fruit_def['name'], 
            r=fruit_def['radius'] )
        self._sprite_visi = VISI_NORMAL
        self._sprite_explosion = None
        self._fruit_mode = None
        self._dash_start_time = None
        self._set_mode( mode )
        print( f"{self}" )


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
        #  ajoute fruit_id comme attribut custom de l'objet pymunk 
        shape.fruit = self
        return body, shape


    def _delete(self):
        if( not self.removed ):
            print( f"WARNING: {self} delete() avec mode différent de MODE_REMOVED ({self._fruit_mode})" )
        # remove pymunk objects and local references
        if( self._body or self._shape):
            #print( f"{self}.delete()")
            self._space.remove( self._body, self._shape )
            self._body = self._shape = None
        
        # remove sprite from pyglet graphics batch
        if( self._sprite ):
            self._sprite.delete()
            self._sprite = None

        if( self._sprite_explosion ):
            self._sprite_explosion.delete()
            self._sprite_explosion = None


    def __del__(self):
        _del_fruit()
        #print( f"__del__({self})")
        self._delete()


    @property
    def id(self):
        return self._id

    @property
    def scalar_velocity(self):
        return self._body.velocity.length

    @property
    def points(self):
        return self._kind
    
    @property
    def is_mode_normal(self):
        return self._fruit_mode == MODE_NORMAL

    @property
    def removed(self):
        return self._fruit_mode == MODE_REMOVED
    
    @property
    def position(self):
        return self._body.position

    def _is_deleted(self):
        return (self._body==None 
            and self._sprite==None 
            and self._shape==None
            and self._sprite_explosion==None)


    def _set_mode(self, mode):
        # debug
        # old = self._fruit_mode
        # log = f"{self} mode {self._fruit_mode}->{mode}"
        # if( old and mode not in g_valid_transitions[old] ):
        #     log += " INVALIDE"
        # print(log)
        self._fruit_mode = mode
        attrs = _FRUIT_MODES[self._fruit_mode]

        # DYNAMIC ou KINEMATIC
        self._body.body_type = attrs[BODY_TYPE]
        self._sprite.visibility = attrs[VISI]

        # modifie les règkes de collision
        self._shape.filter = pm.ShapeFilter(
            categories= attrs[COLLISION_CAT],
            mask = attrs[COLLISION_MASK] | CAT_WALLS )  # collision systematique avec les murs


    def create_larger( self, levelup ):
        new_kind = min( self._kind + levelup, nb_fruits() )
        fruit =  Fruit( space = self._space,
                     kind=new_kind,
                     position = self._body.position)
        fruit.fade_in()   # pour passer en mode Body.DYNAMIC
        return fruit


    def update(self):
        """met à jour le sprite du fruit à partir de la simulation physique et autres
        """
        if( self._is_deleted() ):
            return
        (x, y) = self._body.position
        degres = -180/3.1416 * self._body.angle  # pymunk et pyglet ont un sens de rotation opposé
        self._sprite.update( x=x, y=y, rotation=degres,
                             on_animation_stop=None )
        self._shape.update_animation()
        

    def set_x(self, x):
        assert( self._body.body_type == pm.Body.KINEMATIC ), "disponible seulement sur le fruit en attente"
        # contrainte à l'interieur du jeu
        x = max(x, self._shape.radius )
        x = min(x, WINDOW_WIDTH - self._shape.radius)
        (x0, y0) = self._body.position
        self._body.position = ( x, y0 )
        self._sprite.position = ( x, y0, 0 )


    def blink(self, activate, delay=0):
        if(not activate):
            self._sprite._blink_start = None
        elif( not self._sprite.blink ):
            self._sprite._blink_start = pg.clock.get_default().time() + delay


    def normal(self):
        """met l'objet en mode dynamique pour qu'il tombe"""
        assert not (self._kind is None)
        assert( self._body.body_type == pm.Body.KINEMATIC )
        self._set_mode( MODE_NORMAL )


    def fade_in(self):
        """ fait apparaitre le sprite avec un effet d'agrandissement et de transparence
        """
        self.normal()
        self._sprite.fadein = True
        self._shape.grow_start()


    def fade_out(self):
        assert( self._body.body_type == pm.Body.KINEMATIC )
        self.normal()
        self._sprite.fadeout = True


    def gameover(self):
        if( not self.removed ):
            self._set_mode(MODE_GAMEOVER)
            self._sprite.fadein = False
            self._sprite.fadeout = False
            self._sprite.blink = False


    def dash_in(self, dest):
        self._set_mode( MODE_EXPLOSE )  # plus de collisions avec les fruits
        (x0, y0) = self._body.position
        (x1, y1) = dest
        v = ((x1-x0)/DASHIN_DELAY, (y1-y0)/DASHIN_DELAY)
        self._body.velocity = v
        pg.clock.schedule_once(lambda dt : self.remove(), delay=DASHIN_DELAY )
    

    def explose(self):
        self._set_mode(MODE_EXPLOSE)
        explo = sprites.ExplosionSprite( 
            r=self._shape.radius, 
            on_explosion_end=self.remove)
        explo.position = ( *self._body.position, 1)
        self._sprite_explosion = explo
        self._sprite.fadeout = True

    def is_offscreen(self) -> bool :
        if self._is_deleted():
            return False
        x, y = self._body.position
        return   (x < 0) or (y < 0) or (x>WINDOW_WIDTH) or (y>WINDOW_HEIGHT)
    
    # retire le fruit du jeu. l'objet ne doit plus être utilisé ensuite.
    def remove(self):
        self._set_mode(MODE_REMOVED)
        self._delete()


def get_fruit(arbiter):

    # détecte le fruit et la maxline dans la collision
    def is_fruit_shape(shape):
        return shape.collision_type > 0 and shape.collision_type<=nb_fruits()

    if( is_fruit_shape( arbiter.shapes[0]) ):
        return arbiter.shapes[0].fruit
    elif ( is_fruit_shape( arbiter.shapes[1])):
        return arbiter.shapes[1].fruit
    else:
        raise RuntimeError( "Collision sans fruit")


class CollisionHelper(object):
    """ Contient le callback appelé par pymunk pour chaque collision 
    et les algorithmes de choix des fruits à fusionner et créer
    """
    def __init__(self, space):
        self.reset()
        self.setup_handlers( space )


    def reset( self ):
         self._collisions_fruits = []
         self._actions = {}


    def collision_fruit( self, arbiter ):
        """ Callback pour pymunk collision_handler
        """
        shapes = arbiter.shapes
        assert( len(shapes)==2 ), " WTF ???"
        self._collisions_fruits.append( (shapes[0].fruit, shapes[1].fruit) )
        return True   # ignore les collisions avec maxline pour la simu physique

    def collision_maxline_begin(self, arbiter):
        f = get_fruit(arbiter)
        # execution différée, l'action peut changer en cas de collision  avec un autre fruit
        self._actions[id]= lambda : f.blink( activate=True, delay= BLINK_DELAY )
        return False  # ignore les collisions avec maxline pour la simu physique

    def collision_maxline_separate(self, arbiter):
        f = get_fruit(arbiter)
        # execution différée, l'action peut changer en cas de collision ou autre
        self._actions[id]= lambda : f.blink( activate=False )
        return False  # ignore les collisions avec maxline pour la simu physique


    def _collision_sets(self):
        """ recherche les composantes connexes dans le graphe des collisions
        Le graphe est défini par une liste d'adjacence
        """
        if( not self._collisions_fruits ):  # optimisation
            return []

        # ensemble des boules concernées par les collisions à résoudre
        fruits = set( [pair[0] for pair in self._collisions_fruits] 
                     +[pair[1] for pair in self._collisions_fruits] )

        # construit le graphe des boules en contact
        g = { f:set() for f in fruits }
        for (a, b) in self._collisions_fruits :
            g[a].add(b)
            g[b].add(a)

        # recherche les composantes connexes dans le graphe 
        # https://francoisbrucker.github.io/cours_informatique/cours/graphes/chemins-cycles-connexite/
        composantes = []
        already_found = set()

        for origine in fruits:
            if origine in already_found:
                continue
            already_found.add(origine)
            composante = {origine}
            suivant = [origine]
            while suivant:
                x = suivant.pop()
                already_found.add(x)
                for y in g[x]:
                    if y not in composante:
                        composante.add(y)
                        suivant.append(y)
            composantes.append(composante)
        return composantes


    def _process_collisions(self, is_gameover):
        """ modifie les fruits selon collisions apparues pendant pymunk.step()
        """
        new_fruits = set()
        # traite les explosions 
        for collision_set in self._collision_sets():
            # liste de Fruit à partir des ids, trié par altitude
            explose_fruits = sorted( collision_set,  key=lambda f: f.position.y )
            assert len( explose_fruits ) >= 2, "collision à un seul fruit ???"

            # traite uniquement les 2 fruits les plus bas en cas de collision multiple
            f0 = explose_fruits[0]
            f1 = explose_fruits[1]

            self._actions[f0] = f0.explose
            self._actions[f1] = lambda : f1.dash_in( dest=f0.position )

            # remplace les fruits explosés par un seul nouveau fruit de taille supérieure
            new_fruit = f0.create_larger(levelup=1)
            if( is_gameover ):
                new_fruit.gameover()
            new_fruits.add(new_fruit)
            print( f"{new_fruit} <--Fusion {[f0, f1]}" )
        return new_fruits


    def process(self, is_gameover):
        new_fruits = self._process_collisions(is_gameover=is_gameover)

        # exectude les actions sur les fruits existants ( explose(), blink(), etc... )
        for action in self._actions.values():
            action()
        self.reset()
        return new_fruits


    def setup_handlers(self, space):
        # collisions entre fruits
        for id in range(1, nb_fruits()+1):
            h = space.add_collision_handler(id, id)
            h.begin = lambda arbiter, space, data : self.collision_fruit(arbiter)

        # collisions avec maxline
        h = space.add_wildcard_collision_handler( COLLISION_TYPE_MAXLINE )
        h.begin = lambda arbiter, space, data : self.collision_maxline_begin(arbiter)
        h.separate = lambda arbiter, space, data : self.collision_maxline_separate(arbiter)