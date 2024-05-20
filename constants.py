
############ Apparence de l'application #############
WINDOW_HEIGHT = 1800
WINDOW_WIDTH  = 1400
BOCAL_MARGIN_TOP = 200
BOCAL_MARGIN_BOTTOM = 50
BOCAL_MARGIN_SIDE = 150
GUI_FONT_SIZE = 25
GUI_TOP_MARGIN = 10
NEXT_FRUIT_Y_POS = BOCAL_MARGIN_TOP//2   # pixels from top
PREVIEW_Y_POS =  90    # pixels from top
PREVIEW_SPRITE_SIZE = 50
PREVIEW_SLOT_SIZE = 70
PREVIEW_COUNT = 3

############### Apparence du bocal ############
WALL_THICKNESS = 20
WALL_COLOR = (205,200,255,255)
REDLINE_TOP_MARGIN = 170
REDLINE_THICKNESS = 2
REDLINE_COLOR= (255,20,20,255) 
BOCAL_MIN_WIDTH=300
BOCAL_MIN_HEIGHT=400

############ Simulation physique #############
PYMUNK_INTERVAL = 1 / 120.0     # cadence simulation physique
FRICTION = 1.0
GRAVITY = -981
INITIAL_VELOCITY = 1200
ELASTICITY_FRUIT = 0.05
ELASTICITY_WALLS = 0.05


############ Animations et temporisations du jeu #############
AUTOPLAY_INTERVAL_BASE = 0.05       # secondes
AUTOPLAY_INITIAL_RATE = 5

PREVIEW_SHIFT_DELAY = 0.1  # secondes
AUTOFIRE_DELAY = 0.5       # secondes 
SHAKE_FREQ_MIN = 1.5       # Hz
SHAKE_FREQ_MAX = 5         # Hz
SHAKE_ACCEL_DELAY = 0.5    # secondes
SHAKE_AMPLITUDE_X = 50
SHAKE_AMPLITUDE_Y = 50
SHAKE_RETURN_SPEED = 0.25      # coef vitesse de retour sur la position de ref
SHAKE_MOUSE_SPEED = 0.5       # coef vitesse de secousse manuelle
TUMBLE_FREQ = 0.25    # Hz
COUNTDOWN_DISPLAY_LIMIT = 3.0   # secondes
GAMEOVER_DELAY = 4.0            # secondes
GAMEOVER_ANIMATION_START = 5         # secondes
GAMEOVER_ANIMATION_INTERVAL = 0.3    # secondes


############# parametres animations des fruits ################
BLINK_DELAY = 1.0          # secondes
BLINK_FREQ  = 6.0          # Hz
FADEOUT_DELAY = 0.5        # secondes
FADEIN_DELAY = 0.08        # secondes
FADEIN_OVERSHOOT = 1.15    # ratio
FADE_SIZE = 0.2            # ratio pour la taille de départ (resp. fin) du fade-in (resp. fadeout)
EXPLOSION_DELAY = 0.3      # secondes
MERGE_DELAY = 0.1          # secondes
SPAWN_DELAY = 0.3          # secondes


# Identifiants pour dispatcher les collisions sur la logique de jeu
# les fruits ont un COLLISION_TYPE égal à leur espèce ( fruit.kind )
COLLISION_TYPE_WALL_BOTTOM = 1000
COLLISION_TYPE_WALL_SIDE = 1001
COLLISION_TYPE_MAXLINE = 1002
COLLISION_TYPE_FIRST_DROP = 1003

# catégories pour le filtrage rapide des collisions
CAT_WALLS          = 1 << 0
CAT_MAXLINE        = 1 << 1
CAT_FRUIT_WAIT     = 1 << 2
CAT_FRUIT_DROP     = 1 << 3
CAT_FRUIT          = 1 << 4
CAT_FRUIT_MERGE    = 1 << 5
CAT_FRUIT_REMOVED  = 1 << 6

