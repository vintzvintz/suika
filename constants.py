
WINDOW_HEIGHT = 1200
WINDOW_MAXLINE_MARGIN = 250
WINDOW_WIDTH  = 800


PYMUNK_INTERVAL = 1 / 120.0     # physics engine steps per sec.
FRICTION = 1.0
GRAVITY = 9.81

NEXT_FRUIT_INTERVAL = 0.2
AUTOPLAY_INTERVAL = 0.5

COUNTDOWN_DISPLAY_LIMIT = 3.0   # secondes
GAMEOVER_DELAY = 4.0         # secondes

# parametres animations 
BLINK_DELAY = 1.0          #secondes
BLINK_FREQ  = 6.0          # Hz
FADEOUT_DELAY = 0.2
FADEIN_DELAY = 0.2
FADEIN_OVERSHOOT = 1.1
FADE_SIZE = 0.2     # ratio pour la taille de départ (resp. fin) du fade-in (resp. fadeout)
EXPLOSION_DELAY = 0.5


# Identifiants pour dispatcher les collisions sur la logique de jeu ( collision_handler )

# COLLISION_TYPE_*fruits*  définis implicitement (entiers inférieurs à 1000)
#COLLISION_TYPE_WALL = 1001
COLLISION_TYPE_MAXLINE = 1000

# catégories pour la creation des collisions
CAT_WALLS          = 1 << 0
CAT_MAXLINE        = 1 << 1
CAT_FRUIT_WAIT     = 1 << 2
CAT_FRUIT          = 1 << 3
CAT_FRUIT_EXPLOSE  = 1 << 4
CAT_FRUIT_REMOVED  = 1 << 5


SPRITE_GROUP_FOND = 'fond'
SPRITE_GROUP_FRUITS = 'fruit'
SPRITE_GROUP_EXPLOSIONS = 'explosions'
SPRITE_GROUP_GUI = 'gui'
