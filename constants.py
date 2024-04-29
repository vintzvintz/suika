
WINDOW_HEIGHT = 800
WINDOW_MAXLINE_MARGIN = 200
WINDOW_WIDTH  = 1000

GUI_FONT_SIZE = 25
GUI_TOP_MARGIN = 10

PREVIEW_Y_POS = WINDOW_HEIGHT - 90
PREVIEW_SPRITE_SIZE = 50
PREVIEW_SLOT_SIZE = 70
PREVIEW_COUNT = 3
PREVIEW_SHIFT_DELAY = 0.2  # seconds


PYMUNK_INTERVAL = 1 / 120.0     # physics engine steps per sec.
FRICTION = 0.50
GRAVITY = 9.81
INITIAL_VELOCITY = 1000


NEXT_FRUIT_INTERVAL = 0.2
AUTOPLAY_INTERVAL = 0.5
AUTOPLAY_FLOW = 1 + WINDOW_WIDTH // 750

COUNTDOWN_DISPLAY_LIMIT = 3.0   # secondes
GAMEOVER_DELAY = 4.0         # secondes

# parametres animations 
BLINK_DELAY = 1.0          #secondes
BLINK_FREQ  = 6.0          # Hz
FADEOUT_DELAY = 0.5
FADEIN_DELAY = 0.08
FADEIN_OVERSHOOT = 1.15
FADE_SIZE = 0.2           # ratio pour la taille de départ (resp. fin) du fade-in (resp. fadeout)
EXPLOSION_DELAY = 0.3
MERGE_DELAY = 0.1
SPAWN_DELAY = 0.3

# Identifiants pour dispatcher les collisions sur la logique de jeu ( collision_handler )

# COLLISION_TYPE_*fruits*  définis implicitement (entiers inférieurs à 1000)
COLLISION_TYPE_WALL_BOTTOM = 1000
COLLISION_TYPE_WALL_SIDE = 1001
COLLISION_TYPE_MAXLINE = 1002
COLLISION_TYPE_FIRST_DROP = 1003

# catégories pour la creation des collisions
CAT_WALLS          = 1 << 0
CAT_MAXLINE        = 1 << 1
CAT_FRUIT_WAIT     = 1 << 2
CAT_FRUIT_DROP     = 1 << 3
CAT_FRUIT          = 1 << 4
CAT_FRUIT_MERGE    = 1 << 5
CAT_FRUIT_REMOVED  = 1 << 6


SPRITE_GROUP_FOND = 'fond'
SPRITE_GROUP_FRUITS = 'fruit'
SPRITE_GROUP_EXPLOSIONS = 'explosions'
SPRITE_GROUP_MASQUE = 'masque'
SPRITE_GROUP_GUI = 'gui'

