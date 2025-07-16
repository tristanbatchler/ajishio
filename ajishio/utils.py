import pygame as pg
import math

def remove_ext(filename: str) -> str:
    return filename[:filename.rfind('.')]

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

def lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t

def point_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)
