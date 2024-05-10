

import pyglet as pg
from constants import *
from fruit import nb_fruits


def _is_fruit_shape(shape):
    return shape.collision_type > 0 and shape.collision_type<=nb_fruits()

def _get_fruit(arbiter):
    # détecte le fruit et la maxline dans la collision
    if( _is_fruit_shape( arbiter.shapes[0]) ):
        return arbiter.shapes[0].fruit
    elif ( _is_fruit_shape( arbiter.shapes[1])):
        return arbiter.shapes[1].fruit
    else:
        raise RuntimeError( "Collision sans fruit")

def _get_fruit_first_drop(arbiter):
    """ Detecte le fruit MODE_FIRST_DROP dans une collision
    """
    s0 =arbiter.shapes[0]  # alias
    s1 =arbiter.shapes[1]

    first_fruit = None   # results
    other_fruit = None
    if( s0.collision_type==COLLISION_TYPE_FIRST_DROP ):
        first_fruit = s0.fruit
        if( _is_fruit_shape(s1) ):
            other_fruit = s1.fruit
    if( s1.collision_type==COLLISION_TYPE_FIRST_DROP ):
        first_fruit = s1.fruit
        if( _is_fruit_shape(s0) ):
            other_fruit = s0.fruit
    if( not first_fruit ):
        raise AssertionError("collision handler appelé sur autre chose qu'un fruit en mode FIRST_DROP")
    return (first_fruit, other_fruit)


class CollisionHelper(object):
    """ Contient le callback appelé par pymunk pour chaque collision 
    et les algorithmes de choix des fruits à fusionner et créer
    """
    def __init__(self, space):
        self.reset()
        self.setup_handlers( space )


    def reset( self ):
         self._collisions_fruits = []
         self._actions = []

    def collision_fruit( self, arbiter ):
        """ Callback pour pymunk collision_handler
        """
        s0 = arbiter.shapes[0]
        s1 = arbiter.shapes[1]

        shapes = arbiter.shapes
        assert( len(shapes)==2 ), " WTF ???"
        assert( s0.fruit.kind == s1.fruit.kind )
        self._collisions_fruits.append( (s0.fruit, s1.fruit) )
        return True


    def collision_first_drop( self, arbiter ):
        """ Appelé quand un fruit tombe sur un autre pour la 1ere fois après avoir été mis en jeu
        """
        (first_fruit, other_fruit) = _get_fruit_first_drop(arbiter)
        self._actions.append( lambda : first_fruit.normal() )
        # la premiere collision est aussi une collision normale
        if( other_fruit and first_fruit.kind==other_fruit.kind ):
            self.collision_fruit(arbiter)
        return True

    def collision_maxline_begin(self, arbiter):
        f = _get_fruit(arbiter)
        # execution différée, l'action peut changer en cas de collision  avec un autre fruit
        self._actions.append( lambda : f.blink( activate=True, delay= BLINK_DELAY ) )
        return False  # ignore les collisions avec maxline pour la simu physique

    def collision_maxline_separate(self, arbiter):
        f = _get_fruit(arbiter)
        # execution différée, l'action peut changer en cas de collision ou autre
        self._actions.append( lambda : f.blink( activate=False ) )
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


    def _process_collisions(self, spawn_func, world_to_bocal_func):
        """ modifie les fruits selon collisions apparues pendant pymunk.step()
        """
        # traite les explosions 
        for collision_set in self._collision_sets():
            # liste de Fruit à partir des ids, trié par altitude
            explose_fruits = sorted( collision_set,  key=lambda f: f.position.y )
            assert len( explose_fruits ) >= 2, "collision à un seul fruit ???"

            # traite uniquement les 2 fruits les plus bas en cas de collision multiple
            f0 = explose_fruits[0]
            f1 = explose_fruits[1]
            assert( f0.kind == f1.kind )
#            print( f"Fusion {[f0, f1]}" )
            self._actions.append( f0.explose )
            self._actions.append( lambda : f1.merge_to( dest=f0.position ) )

            # remplace les fruits explosés par un seul nouveau fruit de taille supérieure
            # copie les infos car f0 peut être REMOVED quand spawn() sera appelée
            kind = min( f0.kind + 1, nb_fruits() )
            bocal_coords = world_to_bocal_func( f0.position )
            spawn_fruit = lambda dt : spawn_func(kind=kind, bocal_coords=bocal_coords)
            pg.clock.schedule_once( spawn_fruit, delay=SPAWN_DELAY )


    def process(self, spawn_func, world_to_bocal_func):
        self._process_collisions(spawn_func, world_to_bocal_func)

        # exectude les actions sur les fruits existants ( explose(), blink(), etc... )
        for action in self._actions:
            action()
        self.reset()


    def setup_handlers(self, space):

        # collisions entre fruits en mode normal
        for kind in range(1, nb_fruits()+1):
            h = space.add_collision_handler(kind, kind)
            h.begin = lambda arbiter, space, data : self.collision_fruit(arbiter)

        # collisions des fruits FIRST_DROP avec les fruits normaux ou le sol
        h = space.add_wildcard_collision_handler( COLLISION_TYPE_FIRST_DROP )
        h.begin = lambda arbiter, space, data: self.collision_first_drop(arbiter)

        # collisions avec maxline
        h = space.add_wildcard_collision_handler( COLLISION_TYPE_MAXLINE )
        h.begin = lambda arbiter, space, data : self.collision_maxline_begin(arbiter)
        h.separate = lambda arbiter, space, data : self.collision_maxline_separate(arbiter)