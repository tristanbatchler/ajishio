from __future__ import annotations

class View:
    _instance: View | None = None
    def __new__(cls) -> View:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        self.view_current: int = 0
        self.view_xport: dict[int, float] = {self.view_current: 0}
        self.view_yport: dict[int, float] = {self.view_current: 0}
        self.view_wport: dict[int, float] = {self.view_current: 800}
        self.view_hport: dict[int, float] = {self.view_current: 600}

    def view_set_wport(self, view: int, w: float) -> None:
        self.view_wport[view] = w

    def view_set_hport(self, view: int, h: float) -> None:
        self.view_hport[view] = h

    def view_set_xport(self, view: int, x: float) -> None:
        self.view_xport[view] = x

    def view_set_yport(self, view: int, y: float) -> None:
        self.view_yport[view] = y

    @property
    def offset(self) -> tuple[float, float]:
        return (-self.view_xport[self.view_current], -self.view_yport[self.view_current])


_view: View = View()

# Put exposed instance variables here to help with code completion, but they are actually evaluated 
# at runtime by the __getattr__ method in ajishio.__init__.py
view_current: int
view_xport: dict[int, float]
view_yport: dict[int, float]
view_wport: dict[int, float]
view_hport: dict[int, float]

# These do not need to be evaluated at runtime, since they are references to methods, so they go here
view_set_wport = _view.view_set_wport
view_set_hport = _view.view_set_hport
view_set_xport = _view.view_set_xport
view_set_yport = _view.view_set_yport