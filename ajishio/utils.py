import pygame as pg
import math


def room_set_caption(caption: str) -> None:
    pg.display.set_caption(caption)

def lengthdir_x(length: float, direction: float) -> float:
    return length * math.cos(direction)

def lengthdir_y(length: float, direction: float) -> float:
    return length * math.sin(direction)

def clamp(value: float, min: float, max: float) -> float:
    return min if value < min else max if value > max else value

def map_value(value: float, min: float, max: float, new_min: float, new_max: float) -> float:
    return (value - min) / (max - min) * (new_max - new_min) + new_min

def sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0