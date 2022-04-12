import pygame
import textwrap

v = pygame.math.Vector2


def int_tuple(vector):
    return (int(vector[0]), int(vector[1]))

def get_alphabet(spritesheet):
    x_pointer = 0
    y_pointer = 0
    surface_list = {}
    for i in ALPHABET:
        char_pos = v(CHAR_SIZE[0] * x_pointer, CHAR_SIZE[1] * y_pointer)
        char_surf = pygame.Surface(CHAR_SIZE)
        char_surf.blit(spritesheet, int_tuple(-1 * char_pos))
        surface_list[i] = char_surf
        x_pointer += 1
        if x_pointer == LINE_LENGTH:
            x_pointer = 0
            y_pointer += 1

    return surface_list


CHAR_SIZE = v(5, 7) + v(2, 2)
LINE_LENGTH = 18
ALPHABET = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
ALPHABET_CELLPHONE = get_alphabet(pygame.image.load("images/charmap-cellphone_white.png"))
ALPHABET_FUTURISTIC = get_alphabet(pygame.image.load("images/charmap-futuristic_black.png"))
ALPHABET_OLDSCHOOL = get_alphabet(pygame.image.load("images/charmap-oldschool_white.png"))
SHIFT_LOWER = "abcdefghijklmnopqrstuvwxyz124567890-=[];'#,./\\"
SHIFT_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ!\"$%^&*()_+{}:@~<>?|"
CHAR_SIZE[0] -= 1


def generate_text(string, text_colour, bg_colour=None, font_type="cellphone", enlarge=0):
    surface_dims = v(CHAR_SIZE[0] * len(string), CHAR_SIZE[1])
    text_surface = pygame.Surface(surface_dims)
    text_surface.fill(text_colour)
    text_surface.set_colorkey((0, 0, 0))

    if font_type == "oldschool":
        alphabet_surfaces = ALPHABET_OLDSCHOOL
    elif font_type == "futuristic":
        alphabet_surfaces = ALPHABET_FUTURISTIC
    else:
        alphabet_surfaces = ALPHABET_CELLPHONE

    x_pointer = 0
    for char in string:
        if char in list(ALPHABET):
            char_surf = alphabet_surfaces[char]
            char_surf.set_colorkey((255, 255, 255))
            text_surface.blit(char_surf, (x_pointer * CHAR_SIZE[0], 0))
        x_pointer += 1

    colour_surface = pygame.Surface(surface_dims)
    if bg_colour is not None:
        colour_surface.fill(bg_colour)
    else:
        colour_surface.set_colorkey((0, 0, 0))

    colour_surface.blit(text_surface, (0, 0))

    for i in range(enlarge):
        colour_surface = pygame.transform.scale2x(colour_surface)
    return colour_surface


def generate_text_box(string, text_colour, bg_colour=None, font_type="cellphone", line_length=20,center = True):
    string_lines = textwrap.wrap(string, line_length)
    surface = pygame.Surface(((line_length * CHAR_SIZE[0])+3, (len(string_lines) * CHAR_SIZE[1])+4))
    surface.fill(bg_colour)
    offset = v(2, 2)
    for line in string_lines:
        surf = generate_text(line, text_colour, bg_colour, font_type)
        rect = surf.get_rect()
        rect.y = offset[1]
        if center:
            rect.centerx = surface.get_rect().centerx
        else:
            rect.x = offset[0]
        surface.blit(surf, rect)
        offset += v(0, CHAR_SIZE[1])
    surface.set_colorkey((0, 0, 0))
    return surface


class Button:
    def __init__(self, text, pos=(0, 0), colour_no_click=(150, 0, 0), colour_with_click=(100, 0, 0), bg_colour=None, max_width=None, center=True):

        self.mouse_down = False
        self.clicked = False

        self.max_width = max_width

        self.colour_no_click = colour_no_click
        self.colour_with_click = colour_with_click
        self.bg_colour = bg_colour

        self.change_text(text)
        self.text_rect.center = pos

    def update(self, blit_surf):
        # only click once >:(
        if pygame.mouse.get_pressed(3)[0]:
            if self.text_rect.collidepoint(pygame.mouse.get_pos()):
                if self.clicked:
                    self.clicked = False
                if not self.mouse_down and not self.clicked:
                    self.clicked = True
                    self.mouse_down = True
            else:
                self.mouse_down = True
        else:
            self.clicked = False
            self.mouse_down = False

        if self.text_rect.collidepoint(pygame.mouse.get_pos()):
            blit_surf.blit(self.text_surf_with_click, self.text_rect)
        else:
            blit_surf.blit(self.text_surf_no_click, self.text_rect)

        return self.clicked

    def update_draw(self,blit_surf):
        blit_surf.blit(self.text_surf_no_click, self.text_rect)

    def change_text(self, text):
        self.text = text
        if self.max_width == None:
            self.text_surf_no_click = generate_text(self.text, self.colour_no_click, self.bg_colour)
            self.text_surf_with_click = generate_text(self.text, self.colour_with_click, self.bg_colour)
        else:
            self.text_surf_no_click = generate_text_box(self.text, self.colour_no_click, self.bg_colour,"cellphone",self.max_width)
            self.text_surf_with_click = generate_text_box(self.text, self.colour_with_click, self.bg_colour,"cellphone",self.max_width)

        self.text_rect = self.text_surf_no_click.get_rect()

    def set_pos(self, pos):
        self.text_rect.y = pos[1]
        self.text_rect.centerx = pos[0]

    def set_pos_topleft(self,pos):
        self.text_rect.topleft = pos

    def set_pressed(self):
        self.mouse_down = True
        self.clicked = False