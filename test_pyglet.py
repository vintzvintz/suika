
import random

import pyglet as pg
from pyglet import shapes
import pymunk as pm

random.seed(1)   # make the simulation the same each time, easier to debug

WINDOW_HEIGHT = 1000
WINDOW_WIDTH  = 600

PYMUNK_PERIOD = 1 / 200.0     # physics engine steps per sec.


def random_color():
    return (
        random.randint(50,200),
        random.randint(50,200),
        random.randint(50,200),
    )

class Ball( object ):
    def __init__(self, body, pg_shape ):
        self.body = body

        # Cree la forme pyglet associée à l'objet pymunk
        self.pg_shape = pg_shape

    def is_offscreen(self) -> bool :
        return self.body.position.y < 0

    def position_changed(self):
        self.pg_shape.x , self.pg_shape.y = self.body.position
        #self.pg_shape.y = self.body.position.y

    def deallocate(self):
        circle = self.body.shapes
        assert len(circle)==1
        self.body.space.remove( self.body, *circle )


class Lshape( object ):
    def __init__(self, body, pg_lines  ):
        self.body = body
        self.pg_lines = pg_lines

    def position_changed(self):
        lines = zip( self.body.shapes, self.pg_lines )
        for pm_line, pg_line in lines:
            pv1 = self.body.position + pm_line.a.rotated(self.body.angle)
            pv2 = self.body.position + pm_line.b.rotated(self.body.angle)
            pg_line.x, pg_line.y = round(pv1.x), round(pv1.y)
            pg_line.x2, pg_line.y2 = round(pv2.x), round(pv2.y)



class HelloWorldWindow(pg.window.Window):
    def __init__(self):
        super().__init__(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

        self.batch = pg.graphics.Batch()

        self.label = pg.text.Label('Hello, world',
                          font_name='Times New Roman',
                          font_size=36,
                          x=self.width//2, y=self.height-10,
                          anchor_x='center', anchor_y='top',
                          batch=self.batch)

        self.space = pm.Space( )
        self.space.gravity = (0, -900)

        self.balls = []
        self.lshape = None

        pg.clock.schedule_interval( self.pymunk_update, interval=PYMUNK_PERIOD)
        pg.clock.schedule_interval( self.add_ball, interval=1)
        pg.clock.schedule_once( self.add_L, delay=0 )



    def add_ball(self, dt):
        radius = random.randint(12,36)
        mass = radius*radius/100
        body = pm.Body()
        x = random.randint(radius, WINDOW_WIDTH-radius)
        body.position = x, WINDOW_HEIGHT-radius
        
        shape = pm.Circle(body, radius)
        shape.mass = mass
        shape.friction = 1

        self.space.add(body, shape)

        # Cree la forme pyglet associée à l'objet pymunk
        pyglet_shape = shapes.Circle(
            x=body.position.x, 
            y=body.position.y, 
            radius=radius, 
            color=random_color(),
            batch=self.batch )

        self.balls.append(Ball( body=body, pg_shape=pyglet_shape) )
        random.randint(50,200),


    def add_L(self, dt):

        rotation_center_body = pm.Body(body_type=pm.Body.STATIC)
        rotation_center_body.position = (300, 300)

        rotation_limit_body = pm.Body(body_type = pm.Body.STATIC)
        rotation_limit_body.position = (200,300)

        # pymunk objects
        body = pm.Body()
        body.position = (300, 300)
        l1 = pm.Segment(body, (-150, 0), (255, 0), 5)
        l2 = pm.Segment(body, (-150, 0), (-150, 50), 5)
        l1.friction = 1
        l2.friction = 1
        l1.mass = 8
        l2.mass = 1
        
        rotation_center_joint = pm.PinJoint(
            body, rotation_center_body, (0, 0), (0, 0) )
        joint_limit = 25
        rotation_limit_joint = pm.SlideJoint(body, rotation_limit_body, (-100,0), (0,0), 0, joint_limit) # 2

        self.space.add(l1, l2, body, rotation_center_joint, rotation_limit_joint)

        # associated pyglet objects
        pg_l1 = pg.shapes.Line( x=round(l1.a.x),  y=round(l1.a.y),
                                x2=round(l1.b.x),  y2=round(l1.b.y),
                                color=(255,255,255),
                                batch = self.batch )
        pg_l2 = pg.shapes.Line( x=round(l2.a.x),  y=round(l2.a.y),
                                x2=round(l2.b.x),  y2=round(l2.b.y),
                                color=(255,255,255),
                                batch = self.batch )
        self.lshape = Lshape( body=body, pg_lines=(pg_l1, pg_l2) )


    def pymunk_update(self, dt):
        # calcule les positions des objets
        self.space.step( PYMUNK_PERIOD )
        self.remove_offscreen()


    def remove_offscreen(self):
        # supprime les objets tombés
        suppr_balls = [b for b in self.balls if b.is_offscreen() ]
        for b in suppr_balls:
            b.deallocate()
            self.balls.remove( b ) 

    def on_draw(self):
        # met a jour les positions des objets graphiques pyglet
        self.lshape.position_changed()
        for b in self.balls:
            b.position_changed()
        self.label.text = f"Balls = {len(self.balls)}"

        # met à jour l'affichage
        self.clear()
        self.batch.draw()


    def on_key_press(self, symbol, modifiers):
        print('A key was pressed')


if __name__ == '__main__':
    window = HelloWorldWindow()
    pg.app.run()

