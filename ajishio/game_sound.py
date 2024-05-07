import pygame as pg
from ajishio.engine import _engine

class GameSound:
    def __init__(self, sound: pg.mixer.Sound) -> None:
        self.sound: pg.mixer.Sound = sound
        self.duration_ms: float = sound.get_length() * 1000
        self._time_since_started_playing: float | None = None

    def _play(self, loop: bool = False) -> None:
        self.sound.play(-1 if loop else 0)
        self._time_since_started_playing = 0

    def _is_finished(self) -> bool:
        if self._time_since_started_playing is None:
            return True
        self._time_since_started_playing += _engine.delta_time
        if self._time_since_started_playing > self.duration_ms:
            self._time_since_started_playing = None
            return True
        return False
