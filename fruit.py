import random

import pyglet as pg
import pymunk as pm

from constants import *
import sprites
from sprites import EFFET_VISIBLE, EFFET_HIDDEN, EFFET_BLINK, EFFET_FADEOUT, EFFET_GAMEOVER


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
MODE_FALL = 'fall'
MODE_DEBORDE = 'deborde'
MODE_EXPLOSE = 'explose'
MODE_REMOVED = 'removed'
MODE_GAMEOVER = 'gameover'

COLLISION_CAT = 'coll_cat'
COLLISION_MASK = 'coll_mask'

EFFET = 'effect'

_FRUIT_MODES = {
    MODE_WAIT: {
        COLLISION_CAT: CAT_FRUIT_WAIT,
        COLLISION_MASK: 0x00, # collision avec les murs uniqement
        EFFET: EFFET_VISIBLE,
    },
    MODE_FALL: {
        COLLISION_CAT: CAT_FRUIT_FALL,
        COLLISION_MASK: CAT_FRUIT_FALL | CAT_MAXLINE,
        EFFET: EFFET_VISIBLE ,
    },
    MODE_DEBORDE: {
        COLLISION_CAT: CAT_FRUIT_FALL,
        COLLISION_MASK: CAT_FRUIT_FALL | CAT_MAXLINE,
        EFFET: EFFET_BLINK,
    },
    MODE_GAMEOVER: {
        COLLISION_CAT: CAT_FRUIT_FALL,
        COLLISION_MASK: CAT_FRUIT_FALL,
        EFFET: EFFET_GAMEOVER ,
    },
    MODE_EXPLOSE: {
        COLLISION_CAT: CAT_FRUIT_EXPLOSE,
        COLLISION_MASK: 0x00,   # collision avec les murs uniqement
        EFFET:  EFFET_FADEOUT,
    },
    MODE_REMOVED: {
        COLLISION_CAT: CAT_FRUIT_REMOVED,
        COLLISION_MASK: 0x00,   # collision avec les murs uniqement
        EFFET: EFFET_HIDDEN ,
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


class Fruit( object ):
    def __init__(self, space, kind=0, position=None):
        _new_fruit()
        # espece aléatoire si non spécifiée
        assert kind< nb_fruits(), "type de balle invalide"
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
            radius=fruit_def['radius'] )
        self._sprite_explosion = None
        self._set_mode( MODE_WAIT )


    def _delete(self):
        #print( f"{self}.delete()")
        if( self._fruit_mode != MODE_REMOVED):
            print( f"WARNING: {self} delete() avec mode différent de MODE_REMOVED" )
        # remove pymunk objects and local references
        if( self._body or self._shape):
            print( f"{self}.delete()")
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
        print( f"__del__({self})")
        self._delete()


    def explode(self):
        self.fruit_mode = MODE_EXPLOSE
        s = sprites.ExplosionSprite( self._shape.radius, self.on_explosion_end)
        s.position = (*self._body.position, 1)
        self._sprite_explosion = s

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
    def removed(self):
        return self._fruit_mode == MODE_REMOVED
    

    def _is_deleted(self):
        return (self._body==None 
            and self._sprite==None 
            and self._shape==None
            and self._sprite_explosion==None)

    def _set_mode(self, value):
        print( f"{self}._setmode({value})")
        self._fruit_mode = value
        mode = _FRUIT_MODES[value]
        self._sprite.set_effet( mode[EFFET] )
        
        # modifie les règkes de collision
        self._shape.filter = pm.ShapeFilter(
            categories= mode[COLLISION_CAT],
            mask = mode[COLLISION_MASK] | CAT_WALLS )  # collision systematique avec les murs


    def __repr__(self):
        return f"{_FRUITS_DEF[self._kind]['name']}#{self._id}"


    def _make_shape(self, radius, mass, position):
        """ cree le body/shape pymunk pour la simulation physique
        """
        body = pm.Body(body_type = pm.Body.KINEMATIC)
        body.position = position
        shape = pm.Circle(body, radius)
        shape.mass = mass
        shape.friction = FRICTION
        #  ajoute fruit_id comme attribut custom de l'objet pymunk 
        shape.fruit_id = self._id
        return body, shape


    def create_larger( self, levelup, drop=True ):
        kind = min( self._kind + levelup, nb_fruits() )
        fruit =  Fruit( space = self._space,
                     kind=kind,
                     position = self._body.position)
        if( drop ):
            fruit.drop()   # pour passer en mode Body.DYNAMIC
        return fruit


    def update(self):
        """met à jour le sprite du fruit à partir de la simulation physique et autres
        """
        if( self._is_deleted() ):
            return
        (x, y) = self._body.position
        degres = -180/3.1416 * self._body.angle  # pymunk et pyglet ont un sens de rotation opposé
        self._sprite.update( x=x, y=y, rotation=degres)


    def set_x(self, x):
        assert( self._body.body_type == pm.Body.KINEMATIC ), "disponible seulement sur le fruit en attente"
        # contrainte à l'interieur du jeu
        x = max(x, self._shape.radius )
        x = min(x, WINDOW_WIDTH - self._shape.radius)
        (x0, y0) = self._body.position
        self._body.position = ( x, y0 )


    def drop(self):
        """met l'objet en mode dynamique pour qu'il tombe"""
        assert( self._body.body_type == pm.Body.KINEMATIC )
        self._body.body_type = pm.Body.DYNAMIC
        assert not (self._kind is None)
        self._set_mode( MODE_FALL )

    def set_deborde(self, val):
        """Mode débordement -> clignote"""
        if(val):
            self._set_mode(MODE_DEBORDE)
        else:
            self._set_mode(MODE_FALL)

    def gameover(self):
        self._set_mode(MODE_GAMEOVER)

    def explose(self):
        self._set_mode(MODE_EXPLOSE)
        sprite = sprites.ExplosionSprite( 
            radius=self._shape.radius, 
            on_explosion_end=self.on_explosition_end)
        sprite.position = ( *self._body.position, 0)
        self._sprite_explosion = sprite

    def is_offscreen(self) -> bool :
        if self._is_deleted():
            return False
        x, y = self._body.position
        return   (x < 0) or (y < 0) or (x>WINDOW_WIDTH) or (y>WINDOW_HEIGHT)
    
    def on_explosition_end(self):
        print( f"{self} on_explosion_end()")
        self._set_mode(MODE_REMOVED)
        self._delete()


class CollisionResolver(object):
    """ Contient lecallback appelé par pymunk pour chaque collision 
    et les algorithmes de choix des fruits à fusionner et créer
    """
    def __init__(self, space):
        self.reset()
        self._space = space
        self.setup_handlers()


    def reset( self ):
        self._collisions = []


    def collision_fruit( self, arbiter ):
        """ Callback pour pymunk collision_handler
        """
        shapes = arbiter.shapes
        assert( len(shapes)==2 ), " WTF ???"
        self._collisions.append( (shapes[0].fruit_id, shapes[1].fruit_id) )
        return True   # ne pas ignorer la collision dans la suite


    def _eliminations(self):
        """ recherche les composantes connexes dans le graphe des collisions
        Le graphe est défini par une liste d'adjacence
        """
        # ensemble des boules concernées par les collisions à résoudre
        fruit_ids = set([  pair[0] for pair in self._collisions] + [pair[1] for pair in self._collisions ])

        # construit le graphe des boules en contact
        g = { ball:set() for ball in fruit_ids }
        for (a, b) in self._collisions :
            g[a].add(b)
            g[b].add(a)

        # recherche les composantes connexes dans le graphe 
        # https://francoisbrucker.github.io/cours_informatique/cours/graphes/chemins-cycles-connexite/
        composantes = []
        already_found = []

        for origine in fruit_ids:
            if origine in already_found:
                continue

            already_found.append(origine)
            composante = {origine}
            suivant = [origine]
            while suivant:
                x = suivant.pop()
                already_found.append(x)
                for y in g[x]:
                    if y not in composante:
                        composante.add(y)
                        suivant.append(y)
            composantes.append(composante)
        return composantes


    def resolve(self, fruits):
        """ renvoie un tuple
            liste des fruits créés par fusion des fruits en contact
            liste des id des fruits fusionnés ( pour suppression )        
        """
        created = [] 
        to_remove = []

        for groupe in self._eliminations():
            print( f"Elimination de {groupe}" )

            # on garde l'objet le plus lent
            slowest = None
            for id in groupe:
                f = fruits[id]
                if(not slowest):
                    slowest = f
                if( f.scalar_velocity < slowest.scalar_velocity ):
                    slowest = f

            # remplace les boules par une seule de la taille supérieure
            new_fruit = slowest.create_larger(levelup = len(groupe)-1 )
            created.append(new_fruit)
            # marque les fruits à supprimer
            to_remove += groupe

        return created, to_remove


    def setup_handlers(self):
        # collisions entre fruits
        for id in range(1, nb_fruits()+1):
            h = self._space.add_collision_handler(id, id)
            h.begin = lambda arbiter, space, data : self.collision_fruit(arbiter)

