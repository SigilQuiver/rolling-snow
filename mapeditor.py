import pygame
import math
import copy
import uuid
import timer as t
import pickle
import text

from random import *
from small_utils import *

UP = V(0, -1)
DOWN = V(0, 1)
LEFT = V(-1, 0)
RIGHT = V(1, 0)
CTRLS = {"left": "a",
         "right": "d",
         "jump": "w",
         "down": "s",
         "left2": "left",
         "right2": "right",
         "jump2": "up",
         "down2": "down",
         "restart": "r",
         "switch": "space",
         }
DIMS_START = V(600,600)
TILESIZE = 16

IMAGES = {}

def get_images(image_dict):
    for k in image_dict:
        IMAGES[k] = pygame.image.load(image_dict[k]).convert_alpha()


def init_images():
    global IMAGES
    sprite_sheet = pygame.image.load("images/debugs.png")
    names = ["block", "slope_r", "slope_l", "slope_s_r_1", "slope_s_r_2", "slope_s_l_2", "slope_s_l_1", "platform",
             "snow_block", "snow_slope_r", "snow_slope_l", "snow_slope_s_r_1", "snow_slope_s_r_2", "snow_slope_s_l_2",
             "snow_slope_s_l_1", "snow_platform"]
    for i in range(0, len(names)):
        x = i * TILESIZE
        y = 0
        sub_rect = pygame.Rect(V(x, y), V(TILESIZE, TILESIZE))
        IMAGES[names[i]] = sprite_sheet.subsurface(sub_rect).convert_alpha()

    sprite_sheet = pygame.image.load("images/meter.png")
    names = ["meter_notch","meter_middle","meter_end"]
    for i in range(0, len(names)):
        x = i * TILESIZE
        y = 0
        sub_rect = pygame.Rect(V(x, y), V(TILESIZE, 2))
        IMAGES[names[i]] = sprite_sheet.subsurface(sub_rect).convert_alpha()

    image_dict = {
        "snowman_head":"images/snowmanhead.png",
        "snowman_head2": "images/snowmanhead2.png",
        "snowman_head3": "images/snowmanhead3.png",
        "snowman_body":"images/snowmanbody.png",
        "marker":"images/place_marker.png",
        "spawn":"images/spawn.png",
        "sign":"images/sign.png",
        "tail":"images/bubbletail.png",
        "snowpile":"images/snowpile.png",
        "grassicon":"images/grassicon.png",
        "sizeicon":"images/sizeicon.png"
    }
    get_images(image_dict)


class Player:
    def __init__(self, pos=V(0, 0)):
        self.image = "snowman_head"
        self.rect = IMAGES["snowman_head"].get_rect()

        self.pos = pos
        self.velocity = V(0, 0)

        self.walk_speed = 16 * 5

        self.accel = {"walk": {"max_vel": self.walk_speed, "time_in": 0.25, "time_out": 0.25}}

        self.gravity = 16 * 30
        self.jump_height = (16 * 4) + 5
        self.jump_vel = math.sqrt(self.jump_height * (2 * self.gravity))
        self.on_slope = False

        self.can_jump = False
        self.coyote_time = 0.1
        self.buffer_time = 0.2

        self.state = "walk"

        self.collisions = {}

        self.center = V(0,0)

    def draw(self, screen,dt, offset=V(0, 0)):
        screen.blit(IMAGES["player"], self.pos)

    def update(self, dt, timer, block_list, keys_pressed, keys_held):
        self.update_controller(timer, keys_pressed, keys_held, dt)
        self.update_physics(dt, block_list,timer)

    def update_physics(self, dt, block_list, timer):
        self.collisions = {"bottom": False, "top": False, "left": False, "right": False}

        self.velocity[1] += self.gravity * dt

        self.pos += V(self.velocity[0] * dt, 0)
        # randomise order of block list array
        keys = list(block_list.keys())
        if len(keys) > 2:
            shuffle(keys)
        for k in keys:
            block = block_list[k]
            self.collide_block_x(block)

        # if on a slope add x vel to correct bouncing
        if self.on_slope:
            self.pos += V(0, (abs(self.velocity[0])+self.velocity[1]) * dt)
        else:
            self.pos += V(0, self.velocity[1] * dt)

        for k in keys:
            block = block_list[k]
            self.collide_block_y(block)

        for k in keys:
            block = block_list[k]
            self.collide_side(block,True)

        if self.collisions["bottom"] or self.collisions["top"]:
            self.velocity[1] = 0
        if self.collisions["left"] or self.collisions["right"]:
            self.velocity[0] = 0

        if timer.exists("coyote_time"):
            timer.create_timer("coyote_time",self.coyote_time)

        if self.collisions["bottom"]:
            self.can_jump = True
            timer.reset_timer("coyote_time")
        else:
            if timer.check_timer("coyote_time",self.coyote_time):
                self.can_jump = False

        self.center = copy.deepcopy(self.rect.center)

    def isbottom(self,block):
        pass

    def collide_side(self, block,withbottom=False):
        self.rect.topleft = self.pos
        collide_rect_l = pygame.Rect(V(self.rect.topleft) - V(3, 0), V(3, self.rect.width))
        collide_rect_r = pygame.Rect(V(self.rect.topleft) + V(self.rect.width, 0), V(16, self.rect.width))
        collide_rect_b = pygame.Rect(V(self.rect.topleft) + V(0, self.rect.width), V(self.rect.width, 3))
        collide_rect_t = pygame.Rect(V(self.rect.topleft) - V(0, 3), V(self.rect.width, 3))

        collides = []

        if block.get_rect().colliderect(collide_rect_l):
            collides.append("left")
        if block.get_rect().colliderect(collide_rect_r):
            collides.append("right")
        if block.get_rect().colliderect(collide_rect_b):
            collides.append("bottom")
            if withbottom:
                self.isbottom(block)
            if block.type in ["slope_l","slope_r"]:
                self.on_slope = True
        if block.get_rect().colliderect(collide_rect_t):
            collides.append("top")
        return collides

    def collide_slope(self, block):
        self.rect.topleft = self.pos

        rel_x = self.pos[0] - block.pos[0]
        pos_height = 0
        if block.type == "slope_l":
            rel_x += self.rect.width
            pos_height = block.get_rect().width-rel_x
        elif block.type == "slope_r":
            pos_height = rel_x

        pos_height = min(pos_height, block.rect.width)
        pos_height = max(pos_height, 0)

        y_aim = pos_height + block.pos[1]

        # pygame.draw.circle(a.get_screen(),(255,0,0),(self.pos[0],y_aim),3)

        if self.rect.bottom > y_aim:
            self.rect.bottom = y_aim
            self.pos[1] = self.rect.y
            self.collisions["bottom"] = True
            self.on_slope = True
            self.collide_block(block)

    def collide_block_x(self, block):
        block_rect = block.get_rect()
        type = block.type
        self.rect.topleft = self.pos

        right = False
        left = False
        if type == "block":
            right = True
            left = True
        elif type == "slope_r":
            right = True
        elif type == "slope_l":
            left = True
        if self.rect.colliderect(block_rect):
            collidesides = self.collide_side(block)
            if self.velocity[0] > 0 and right and "right" in collidesides:
                self.rect.right = block_rect.left
                self.pos[0] = self.rect.x
                self.collisions["right"] = True
                self.collide_block(block)
            elif self.velocity[0] < 0 and left and "left" in collidesides:
                self.rect.left = block_rect.right
                self.pos[0] = self.rect.x
                self.collisions["left"] = True
                self.collide_block(block)

    def collide_block_y(self, block):
        block_rect = block.get_rect()
        type = block.type
        self.rect.topleft = self.pos
        bottom = False
        top = False
        if type == "block":
            bottom = True
            top = True
        elif type == "platform":
            bottom = True
        elif type in ["slope_r", "slope_l"]:
            top = True

        collidesides = self.collide_side(block)

        if self.rect.colliderect(block_rect):
            self.on_slope = False
            if type == "slope_r" and ("bottom" in collidesides or "left" in collidesides):
                self.collide_slope(block)
            elif type == "slope_l" and ("bottom" in collidesides or "right" in collidesides):
                self.collide_slope(block)
            if self.velocity[1] > 0 and bottom and "bottom" in collidesides:
                self.rect.bottom = block_rect.top
                self.pos[1] = self.rect.y
                self.collisions["bottom"] = True
                self.collide_block(block)
            elif self.velocity[1] < 0 and top and "top" in collidesides:
                self.rect.top = block_rect.bottom
                self.pos[1] = self.rect.y
                self.collisions["top"] = True
                self.collide_block(block)

    def collide_block(self,block):
        pass

    def update_controller(self, timer, keys_pressed, keys_held, dt):
        if CTRLS["left"] in keys_held or CTRLS["left2"] in keys_held:
            maxx = self.accel[self.state]["max_vel"]
            toadd = (maxx / self.accel[self.state]["time_in"]) * dt
            self.velocity[0] = max(self.velocity[0] - toadd, -maxx)
        elif CTRLS["right"] in keys_held or CTRLS["right2"] in keys_held:
            maxx = self.accel[self.state]["max_vel"]
            toadd = (maxx / self.accel[self.state]["time_in"]) * dt
            self.velocity[0] = min(self.velocity[0] + toadd, maxx)
        else:
            if self.velocity[0] != 0:
                isminusx = self.velocity[0] / abs(self.velocity[0])  # -1 if vel is minus, else is 1

                maxx = self.accel[self.state]["max_vel"]
                toadd = (maxx / self.accel[self.state]["time_out"]) * dt

                self.velocity[0] = self.velocity[0] + (toadd * isminusx * -1)

                if self.velocity[0] != 0:
                    isminusx2 = self.velocity[0] / abs(self.velocity[0])

                    if isminusx2 != isminusx:
                        self.velocity[0] = 0

        if CTRLS["jump"] in keys_pressed or CTRLS["jump2"] in keys_pressed :
            if self.can_jump:
                self.can_jump = False
                self.velocity[1] = -self.jump_vel
            else:
                timer.create_timer("jump_buffer", self.buffer_time)
        elif timer.exists("jump_buffer"):
            if timer.check_timer("jump_buffer",self.buffer_time):
                timer.remove("jump_buffer")
            if self.can_jump:
                self.can_jump = False
                self.velocity[1] = -self.jump_vel
                timer.remove("jump_buffer")


class Snowman(Player):
    def __init__(self, pos=V(0, 0), radius=12):
        super().__init__(pos)

        self.active = True

        self.walk_speed = 16 * 7
        self.accel = {"walk": {"max_vel": self.walk_speed, "time_in": 0.25, "time_out": 0.25}}
        self.gravity = 16 * 30
        self.jump_height = (16 * 4) + 5
        self.jump_vel = math.sqrt(self.jump_height * (2 * self.gravity))

        self.body_angle = 0

        self.radius = radius

        self.rect.topleft = self.pos

        self.set_r_size()

        self.rect.centerx = pos[0] + 8
        self.pos = self.rect.topleft

    def update(self, dt, timer, block_list, keys_pressed, keys_held):
        if self.active:
            self.update_controller(timer, keys_pressed, keys_held, dt)
            self.update_physics(dt, block_list,timer)

    def draw(self, screen,dt, offset=V(0, 0)):
        if self.active:
            if self.can_jump:
                self.body_angle -= self.velocity[0]*5*dt

            pos = copy.copy(self.pos)
            rect = copy.copy(self.rect)

            img_rect = IMAGES["snowman_head3"].get_rect()
            img_rect.centerx = rect.centerx
            img_rect.bottom = rect.top+1
            screen.blit(IMAGES["snowman_head3"],img_rect.topleft+offset)
            pygame.draw.circle(screen,(255,255,255),self.rect.center+offset,math.floor(self.radius))

    def isbottom(self,block):
        turned = block.turn_snow()
        if turned:
            self.radius -= 0.3

            self.set_r_size()

    def set_r_size(self):
        prev_center = copy.copy(self.rect.centerx)
        prev_rect = copy.deepcopy(self.rect)

        new_dim = math.floor(copy.copy(self.radius)) * 2

        self.rect.size = V(new_dim,new_dim)
        self.rect.bottom = prev_rect.bottom
        self.rect.centerx = self.center[0]
        self.pos = self.rect.topleft

    def add_r(self,radius_add):
        self.radius += radius_add
        self.set_r_size()


class Block:
    def __init__(self, pos, typ="block", img="block"):
        self.type = typ
        self.image = img
        self.pos = V(pos)
        self.rect = pygame.Rect(self.pos, V(TILESIZE, TILESIZE))
        self.delete = False

    def draw(self, screen, offset):
        #print(int_tuple(V(self.pos)+V(offset)))
        screen.blit(IMAGES[self.image], int_tuple(V(self.pos)+V(offset)))

        temprect = copy.copy(self.rect)
        temprect.topleft = V(self.pos)+V(offset)
        #pygame.draw.rect(screen,(0,0,0),temprect)

    def get_rect(self):
        return self.rect

    def get_pos(self):
        return self.pos

    def turn_snow(self):
        if not self.image[:5] == "snow_":
            self.image = "snow_"+self.image
            return True
        return False


class Sign(Block):
    def __init__(self, pos, text = "empty :( where is the text wtf cringe wow cringe XD cringe cringe lmao lol cringe"):
        super().__init__(pos, "sign", "sign")
        self.text = text

    def draw_bubble(self,screen,player_rect):
        if player_rect.colliderect(self.rect):
            tail_rect = IMAGES["tail"].get_rect()
            tail_rect.centerx = self.rect.centerx
            tail_rect.bottom = min (player_rect.top - 8,self.rect.top -2)
            screen.blit(IMAGES["tail"],tail_rect)

            text_img = text.generate_text_box(self.text,(0,0,1),(255,255,255),"oldschool",20,False).convert_alpha()
            for x in [0,text_img.get_width()-1]:
                for y in [0,text_img.get_height()-1]:
                    text_img.set_at((x,y),(0,0,0,0))
            text_rect = text_img.get_rect()
            text_rect.bottom = tail_rect.top
            text_rect.centerx = tail_rect.centerx
            text_rect.left = max(text_rect.left,0)
            screen.blit(text_img,text_rect)

    def turn_snow(self):
        return False


class SnowPile(Block):
    def __init__(self, pos):
        super().__init__(pos, "snowpile","snowpile")

    def grow_player(self,player):
        if player.rect.colliderect(self.rect):
            player.add_r(2)

            self.delete = True

    def turn_snow(self):
        return False

class UI:
    def __init__(self):
        pass
    def draw_top(self,screen,radius,grass):
        toblit_img = pygame.Surface(V(DIMS_START[0],10))
        toblit_img.fill((0,0,0))
        toblit_rect = toblit_img.get_rect()

        xpointer = 4
        ico1 = IMAGES["grassicon"]
        ico1_rect = ico1.get_rect()
        ico1_rect.centery = toblit_rect.centery
        ico1_rect.x = xpointer
        xpointer += 8
        toblit_img.blit(ico1,ico1_rect)

        icotext1 = text.generate_text(":"+str(grass),(255,255,255),None,"oldschool")
        icotext1_rect = ico1.get_rect()
        icotext1_rect.centery = toblit_rect.centery
        icotext1_rect.x = xpointer
        xpointer += icotext1.get_width()
        toblit_img.blit(icotext1, icotext1_rect)

        xpointer += 6

        ico2 = IMAGES["sizeicon"]
        ico2_rect = ico1.get_rect()
        ico2_rect.centery = toblit_rect.centery
        ico2_rect.x = xpointer
        xpointer += 8
        toblit_img.blit(ico2, ico2_rect)

        size = "normal(1)"
        if radius < 8:
            size = "small(<1)"
        elif radius >= 16:
            size = "large(>2)"
        elif radius >= 8:
            size = "big(>1)"

        icotext2 = text.generate_text(":" + size, (255, 255, 255), None, "oldschool")
        icotext2_rect = ico1.get_rect()
        icotext2_rect.centery = toblit_rect.centery
        icotext2_rect.x = xpointer
        xpointer += icotext1.get_width()
        toblit_img.blit(icotext2, icotext2_rect)

        screen.blit(toblit_img,toblit_rect)

    """def draw_meter(self,name,colour,value,value_max,screen):
        max_len = 50
        unit_len = max_len//value_max
        unit_amnt = max_len//unit_len
        img_len = 2

        toblit_img = pygame.Surface(V(16,max_len*img_len))
        toblit_img.fill((255,0,0))

        #draw the amount bit first
        amount_img = pygame.Surface(V(16,unit_len*img_len*value))
        amount_img.fill(colour)
        toblit_img.blit(amount_img,(0,0))

        len_left = 50
        ypointer = 0
        for i in range(unit_amnt):
            for x in range(unit_len-1):
                toblit_img.blit(IMAGES["meter_middle"], (0,ypointer))
                ypointer += img_len
            toblit_img.blit(IMAGES["meter_notch"],(0,ypointer))
            ypointer += img_len
        ypointer -= img_len
        toblit_img.blit(IMAGES["meter_end"],(0,ypointer))

        rotated_img = pygame.transform.rotate(toblit_img,-90)"""

class Blocks:
    def __init__(self,player):
        self.blockList = {}
        self.place_type = None
        self.types = ["block", "platform", "slope_r", "slope_l"]
        self.level = 0
        self.snow = False
        self.spawn_pos = V(0,0)
        self.start_radius = 10

        self.load_level(player,False)

    def update(self, mouse_pos, keys_pressed,screen,player,scroll):
        nearest = V((mouse_pos[0] // TILESIZE) * TILESIZE, (mouse_pos[1] // TILESIZE) * TILESIZE)
        screen.blit(IMAGES["marker"],nearest)
        screen.blit(IMAGES["spawn"],self.spawn_pos)

        prefix = ""
        if self.snow:
            prefix = "snow_"

        if tuple(nearest) not in self.blockList and pygame.mouse.get_pressed(3)[0]:
            self.add(Block(nearest, self.types[0], prefix+self.types[0]))
        elif tuple(nearest) in self.blockList and pygame.mouse.get_pressed(3)[0]:
            if self.blockList[tuple(nearest)].image != prefix+self.types[0]:
                self.blockList.pop(tuple(nearest))
                self.add(Block(nearest, self.types[0], prefix+self.types[0]))
        elif tuple(nearest) in self.blockList and pygame.mouse.get_pressed(3)[2]:
            self.blockList.pop(tuple(nearest))

        for k in list(self.blockList.keys()):
            if k in self.blockList:
                block = self.blockList[k]
                if "delete" in vars(block):
                    if block.delete:
                        self.blockList.pop(k)
                else:
                    block.delete = False

        if CTRLS["switch"] in keys_pressed:
            self.types.append(self.types.pop(0))
        if "c" in keys_pressed:
            self.blockList = {}
        if "z" in keys_pressed:
            self.snow = not self.snow
        if "x" in keys_pressed:
            self.spawn_pos = nearest
        if "v" in keys_pressed and tuple(nearest) not in self.blockList:
            self.add(Sign(nearest,input("sign text:")))
        if "b" in keys_pressed and tuple(nearest) not in self.blockList:
            self.add(SnowPile(nearest))
        if "q" in keys_pressed:
            self.level -= 1
            self.load_level(player)
            scroll.__init__(self.get_level_size())
        if "e" in keys_pressed:
            self.level += 1
            self.load_level(player)
            scroll.__init__(self.get_level_size())
        if "k" in keys_pressed:
            self.save_level()
        if "r" in keys_pressed:
            self.load_level(player)
            scroll.__init__(self.get_level_size())
        if "l" in keys_pressed:
            self.load_level(player,False)
            scroll.__init__(self.get_level_size())
        if "p" in keys_pressed:
            self.start_radius = float(input("start radius:"))

    def save_level(self):
        self.save_file("levels/level_"+str(self.level))

    def load_level(self,player,withplayer=True):
        self.load_file("levels/level_"+str(self.level))
        player.__init__(copy.copy(self.spawn_pos),copy.copy(self.start_radius))
        if not withplayer:
            player.active = False

    def update_sblocks(self, screen, player):
        for k in self.blockList:
            block = self.blockList[k]
            if block.type == "sign":
                block.draw_bubble(screen,player.rect)
            if block.type == "snowpile":
                block.grow_player(player)

    def add(self, block):
        self.blockList[tuple(block.get_pos())] = block

    def draw(self, screen, offset=V(0, 0),num=0):
        screen_rect = pygame.Rect(-offset, DIMS_START)
        total = 0

        for v in self.blockList:
            total += 1
            block = self.blockList[v]
            if block.get_rect().colliderect(screen_rect):
                screen.blit(IMAGES[block.image], int_tuple(V(block.pos) + V(offset)))
                screen.blit(IMAGES[block.image], V((num*16)+10,0))
                block.draw(screen, offset)

    def get_blocks(self):
        return self.blockList

    def save_file(self, name):
        file = open(name, "wb")
        pickle_dict = {"blockList":self.blockList,"spawn_pos":self.spawn_pos,"start_radius":self.start_radius}
        pickle.dump(pickle_dict, file)
        file.close()

    def load_file(self, name):
        try:
            file = open(name, "rb")
            pickle_dict = pickle.load(file)
            self.blockList = pickle_dict["blockList"]
            self.spawn_pos = pickle_dict["spawn_pos"]
            self.start_radius = pickle_dict["start_radius"]
            file.close()
        except:
            self.blockList = {}
            self.spawn_pos = V(0,0)
            self.start_radius = 12

    def get_grass(self):
        total = 0
        for k in self.blockList:
            block = self.blockList[k]
            for type in self.types:
                if block.type == type:
                    total += 1
        return total

    def get_level_size(self):
        dims = V(DIMS_START)
        for k in self.blockList:
            if k[0] >= dims[0] and k[1] >= dims[1]:
                dims = V(k)
        return dims

class Scroll:
    def __init__(self,level_size):
        self.rect = pygame.Rect((0,0),DIMS_START)
        self.level_size = level_size
        self.center = V(0,0)
        self.pos = V(0,0)

    def get_scroll(self,aim,dt):

        self.rect.center = aim

        """if self.rect.left < 0:
            self.rect.left = 0
            self.center = self.rect.center

        if self.rect.top < 0:
            self.rect.top = 0
            self.center = self.rect.center
        if self.rect.right > self.level_size[0]:
            self.rect.right = 0
            self.center = self.rect.center
        if self.rect.bottom > self.level_size[1]:
            self.rect.bottom = 0
            self.center = self.rect.center"""
        #self.pos = self.rect.topleft
        return V(0,0)






class App:
    def __init__(self):
        pygame.init()

        self.__game_dims = DIMS_START
        self.__window_dims = C(DIMS_START)
        self.__game_screen = pygame.Surface(int_tuple(self.__game_dims), pygame.HWSURFACE)
        self.__window = pygame.display.set_mode(int_tuple(self.__window_dims), pygame.RESIZABLE)

        init_images()
        self.__update_screen()

        self.__framerate = 60
        self.__clock = pygame.time.Clock()

        self.__timer = t.Timer()

        self.__keys_pressed = []
        self.__keys_held = []

        self.__keys_allow_hold = {CTRLS["restart"]: (3, 1)}

        self.player = Snowman()
        self.blocks = Blocks(self.player)

        self.UI = UI()
        self.scroll = Scroll(self.blocks.get_level_size())

        self.seconds = 0

    def __update_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.VIDEORESIZE:
                self.__window_dims = V(event.w, event.h)
            if event.type == pygame.KEYDOWN:
                key = pygame.key.name(event.key)
                if key not in self.__keys_held:
                    self.__keys_pressed.append(key)
                    self.__keys_held.append(key)
                else:
                    tag = "key:" + key + ":first"
                    self.__timer.reset_timer(tag)
            if event.type == pygame.KEYUP:
                key = pygame.key.name(event.key)
                if key in self.__keys_held:
                    self.__keys_held.remove(key)

        for key in self.__keys_held:
            if key in self.__keys_allow_hold:
                tag1 = "key:" + key + ":first"
                tag2 = "key:" + key + ":second"
                if self.__timer.check_timer(tag1, self.__keys_allow_hold[key][0]):
                    if self.__timer.just_finished(tag1):
                        self.__keys_pressed.append(key)
                    else:
                        if self.__timer.check_timer(tag2, self.__keys_allow_hold[key][1]):
                            self.__timer.reset_timer(tag2)
                            self.__keys_pressed.append(key)

    def __update_screen(self):
        x_div = self.__window_dims[0] // self.__game_dims[0]
        y_div = self.__window_dims[1] // self.__game_dims[1]
        self.scale = min(x_div, y_div)

        scaled_game_dims = self.__game_dims * self.scale
        scaled_game_screen = pygame.transform.scale(self.__game_screen, int_tuple(scaled_game_dims))
        self.scaled_rect = scaled_game_screen.get_rect()
        self.scaled_rect.center = pygame.Rect((0, 0), self.__window_dims).center

        self.__window.blit(scaled_game_screen, self.scaled_rect.topleft)
        pygame.display.flip()

    def __get_mouse_pos(self):
        pos = (V(pygame.mouse.get_pos()) - V(self.scaled_rect.topleft)) / self.scale
        return pos

    def get_screen(self):
        return self.__game_screen

    def run(self):
        while True:
            dt = self.__clock.tick(self.__framerate) / 1000
            scroll = V(self.scroll.get_scroll([self.player.rect.centerx,self.player.rect.bottom], dt))
            pygame.display.set_caption(str(self.__clock.get_fps()))

            self.__keys_pressed = []
            self.__update_events()

            self.__game_screen.fill((200,200,255))
            self.__window.fill((50, 0, 0))

            self.__timer.update(dt)

            self.blocks.draw(self.__game_screen, scroll)
            self.blocks.update(self.__get_mouse_pos(), self.__keys_pressed, self.__game_screen,self.player, self.scroll)
            self.blocks.update_sblocks(self.__game_screen, self.player)

            self.player.draw(self.__game_screen,self.__timer.dt(),scroll)
            self.player.update(dt, self.__timer, self.blocks.get_blocks(), self.__keys_pressed, self.__keys_held)

            self.UI.draw_top(self.__game_screen,self.player.radius,self.blocks.get_grass())

            descripts = [
                "space:switch",
                "z:snow",
                "x:spawn point",
                "v:add sign",
                "b:add snow pile",
                "q,e:back,forward level",
                "k,l:save,load",
                "p:set start radius",
                "level num:"+str(self.blocks.level),
                "block type:"+str(self.blocks.types[0]),
                "snow:"+str(self.blocks.snow)
            ]
            ypointer = 0
            for descript in descripts:
                t_img = text.generate_text(descript,(255,255,255),(0,0,0),"oldschool")
                t_rect = t_img.get_rect()
                t_rect.y = ypointer
                t_rect.right = DIMS_START[0]
                self.__game_screen.blit(t_img,t_rect)
                ypointer += 8

            self.__update_screen()


a = App()
a.run()
