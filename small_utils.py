import pygame
import copy


def ease_out_quad(x):
    return 1 - (1 - x) * (1 - x)


def ease_in_quad(x):
    return x * x * x


def int_tuple(vector):
    return int(vector[0]), int(vector[1])


def lerp(a,b,p):
    return a + (b - a ) * p


class DelayFunc:
    def __init__(self,func,*args):
        self.args = args
        self.func = func

    def run(self):
        return self.func(*self.args)


V = pygame.Vector2
C = copy.deepcopy
