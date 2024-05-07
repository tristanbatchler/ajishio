import pygame as pg
from ajishio.game_sound import GameSound
from pathlib import Path
from ajishio.utils import _remove_ext


def load_sounds(sounds_directory: Path) -> dict[str, GameSound]:
    return {
        _remove_ext(sound_file.name): load_sound(sound_file) 
        for sound_file in sounds_directory.iterdir()
    }

def load_sound(sound_file: Path) -> GameSound:
    sound: pg.mixer.Sound = pg.mixer.Sound(str(sound_file))
    return GameSound(sound)