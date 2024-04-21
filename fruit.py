import random

import pyglet as pg
import pymunk as pm

from constants import *
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
        BODY_TYPE: pm.Body.KINEMATIC
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

# DEBUG transitions old-> new valides
g_valid_changes = {
    MODE_WAIT : ( MODE_NORMAL,),
    MODE_NORMAL : (MODE_EXPLOSE, MODE_GAMEOVER,),
    MODE_EXPLOSE : (MODE_GAMEOVER, MODE_REMOVED,),
    MODE_GAMEOVER : (MODE_REMOVED,),
    MODE_REMOVED : None
}


class Fruit( object ):
    def __init__(self, space, kind=0, position=None):
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
        self._set_mode( MODE_WAIT )
        print( f"Creation {self}" )


    def _delete(self):
        #print( f"{self}.delete()")
        if( not self.removed ):
            print( f"WARNING: {self} delete() avec mode différent de MODE_REMOVED" )
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
    def removed(self):
        return self._fruit_mode == MODE_REMOVED
    

    def _is_deleted(self):
        return (self._body==None 
            and self._sprite==None 
            and self._shape==None
            and self._sprite_explosion==None)


    def _set_mode(self, mode):
        # debug
        old = self._fruit_mode
        log = f"{self} mode {self._fruit_mode}->{mode}"
        if( old and mode not in g_valid_changes[old] ):
            log += " INVALIDE"
        print(log)
        self._fruit_mode = mode
        attrs = _FRUIT_MODES[self._fruit_mode]

        # DYNAMIC ou KINEMATIC
        self._body.body_type = attrs[BODY_TYPE]
        self._sprite.visibility = attrs[VISI]

        # modifie les règkes de collision
        self._shape.filter = pm.ShapeFilter(
            categories= attrs[COLLISION_CAT],
            mask = attrs[COLLISION_MASK] | CAT_WALLS )  # collision systematique avec les murs


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

    def set_x(self, x):
        assert( self._body.body_type == pm.Body.KINEMATIC ), "disponible seulement sur le fruit en attente"
        # contrainte à l'interieur du jeu
        x = max(x, self._shape.radius )
        x = min(x, WINDOW_WIDTH - self._shape.radius)
        (x0, y0) = self._body.position
        self._body.position = ( x, y0 )


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


    def fade_out(self):
        assert( self._body.body_type == pm.Body.KINEMATIC )
        self.normal()
        self._sprite.fadeout = True


    def gameover(self):
        if( not self.removed ):
            self._set_mode(MODE_GAMEOVER)


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


    # def _on_animation_stop(self):
    #     #self._set_mode(MODE_NORMAL)
    #     self._stop_animation()

    # def _stop_animation(self):
    #     self._animation_start_time = None

    # def _start_animation(self):
    #     if( not self._animation_start_time ):
    #         self._animation_start_time = pg.clock.get_default().time()



def get_fruit_id(arbiter):
    # détecte le fruit et la maxline dans la collision

    def is_fruit_shape(shape):
        return shape.collision_type > 0 and shape.collision_type<=nb_fruits()

    if( is_fruit_shape( arbiter.shapes[0]) ):
        return arbiter.shapes[0].fruit_id
    elif ( is_fruit_shape( arbiter.shapes[1])):
        return arbiter.shapes[1].fruit_id
    else:
        raise RuntimeError( "Collision sans fruit")


ACTION_DEBORDE_DEBUT = 'deborde_debut'
ACTION_DEBORDE_FIN   = 'deborde_fin'
ACTION_EXPLOSE       = 'explose'

class CollisionHelper(object):
    """ Contient lecallback appelé par pymunk pour chaque collision 
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
        self._collisions_fruits.append( (shapes[0].fruit_id, shapes[1].fruit_id) )
        return True   # ne pas ignorer la collision dans la suite

    def collision_maxline(self, arbiter, action):
        assert action in [ACTION_DEBORDE_FIN, ACTION_DEBORDE_DEBUT]
        id = get_fruit_id(arbiter)
        self._actions[id]=action
#        print( f"{self._actions[id]} pour fruit {id}")
        return False # collision non prise en compte pour la simu physique


    def _eliminations(self):
        """ recherche les composantes connexes dans le graphe des collisions
        Le graphe est défini par une liste d'adjacence
        """
        if( not self._collisions_fruits ):  # optimisation
            return []

        # ensemble des boules concernées par les collisions à résoudre
        fruit_ids = set( [pair[0] for pair in self._collisions_fruits] 
                        +[pair[1] for pair in self._collisions_fruits] )

        # construit le graphe des boules en contact
        g = { ball:set() for ball in fruit_ids }
        for (a, b) in self._collisions_fruits :
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


    def process_collisions(self, fruits):
        """ modifie les fruits selon collisions apparues pendant pymunk.step()
        """
        # traite les explosions 
        for explose_ids in self._eliminations():

            # liste de Fruit à partir des ids, trié par vitesse croissante
            explose_fruits = [ fruits[id] for id in explose_ids ]
            explose_fruits.sort(key=lambda f:f.scalar_velocity)

            # remplace les fruits explosés par un seul nouveau fruit de taille supérieure
            levelup = len(explose_fruits) - 1  
            new_fruit = explose_fruits[0].create_larger(levelup=levelup)
            fruits[new_fruit.id] = new_fruit

            print( f"Fusion {explose_fruits} -> {new_fruit}" )

            # marque les fruits supprimés pour explosion
            # remplace les chgts de  mode sur collisions avec maxline (explosion prioritaire sur débordement)
            for f in explose_fruits:
                self._actions[f.id] = ACTION_EXPLOSE

        # modifie les fruits
        for (id, action) in self._actions.items():
#            print( f"action {action} pour fruit {id}")
            if( action==ACTION_EXPLOSE ):
                fruits[id].explose()
            elif( action==ACTION_DEBORDE_DEBUT ):
                fruits[id].blink( activate=True,delay=DELAI_CLIGNOTEMENT )
            elif( action==ACTION_DEBORDE_FIN ):
                fruits[id].blink( activate=False )
            else:
                raise RuntimeError( f"action {action} inconnue")


    def setup_handlers(self, space):
        # collisions entre fruits
        for id in range(1, nb_fruits()+1):
            h = space.add_collision_handler(id, id)
            h.begin = lambda arbiter, space, data : self.collision_fruit(arbiter)

        # collisions avec maxline
        h = space.add_wildcard_collision_handler( COLLISION_TYPE_MAXLINE )
        h.begin = lambda arbiter, space, data : self.collision_maxline(arbiter, ACTION_DEBORDE_DEBUT)
        h.separate = lambda arbiter, space, data : self.collision_maxline(arbiter, ACTION_DEBORDE_FIN)