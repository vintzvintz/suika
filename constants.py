
WINDOW_HEIGHT = 1200
WINDOW_MAXLINE_MARGIN = 100
WINDOW_WIDTH  = 800


PYMUNK_INTERVAL = 1 / 120.0     # physics engine steps per sec.
FRICTION = 1.0
GRAVITY = 9.81

DELAI_CLIGNOTEMENT = 1.0
DELAI_DEBORDEMENT = 5.0
DELAI_FADEOUT = 0.5

AUTOPLAY_INTERVAL = 0.5

# Identifiants pour dispatcher les collisions sur la logique de jeu ( collision_handler )

# COLLISION_TYPE_*fruits*  définis implicitement (entiers inférieurs à 1000)
#COLLISION_TYPE_WALL = 1001
COLLISION_TYPE_MAXLINE = 1002


# catégories pour la creation des collisions
CAT_WALLS          = 1 << 0
CAT_MAXLINE        = 1 << 1
CAT_FRUIT_WAIT     = 1 << 2
CAT_FRUIT_FALL     = 1 << 3
CAT_FRUIT_EXPLOSE  = 1 << 4
CAT_FRUIT_REMOVED  = 1 << 5


SPRITE_GROUP_FOND = 'fond'
SPRITE_GROUP_FRUITS = 'fruit'
SPRITE_GROUP_EXPLOSIONS = 'explosions'
SPRITE_GROUP_GUI = 'gui'
