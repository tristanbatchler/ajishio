from __future__ import annotations


class View:
    _instance: View | None = None

    def __new__(cls) -> View:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self) -> None:
        self.view_current: int = 0
        self.window_width: int = 800
        self.window_height: int = 600
        self.view_xport: dict[int, float] = {self.view_current: 0}
        self.view_yport: dict[int, float] = {self.view_current: 0}
        self.view_wport: dict[int, float] = {self.view_current: self.window_width}
        self.view_hport: dict[int, float] = {self.view_current: self.window_height}

    def view_set_wport(self, view: int, w: float) -> None:
        self.view_wport[view] = w

    def view_set_hport(self, view: int, h: float) -> None:
        self.view_hport[view] = h

    def view_set_xport(self, view: int, x: float) -> None:
        self.view_xport[view] = x

    def view_set_yport(self, view: int, y: float) -> None:
        self.view_yport[view] = y

    def window_set_size(self, w: int, h: int) -> None:
        self.window_width = w
        self.window_height = h
        # Keep the default viewport in sync with the window size
        self.view_wport[self.view_current] = w
        self.view_hport[self.view_current] = h

    @property
    def offset(self) -> tuple[float, float]:
        return (
            -self.view_xport[self.view_current],
            -self.view_yport[self.view_current],
        )


view = View()
