from ajishio.engine import _engine
from ajishio.engine import *
from ajishio.input import *
from ajishio.rendering import *
from ajishio.view import _view
from ajishio.view import *
from ajishio.level_loader import *

# Create dynamic references to _engine properties which are accessible at runtime from the outside
def __getattr__(name: str) -> object:
    if name in sys.modules[__name__].__dict__:
        return sys.modules[__name__].__dict__[name]

    if name in _engine.__dict__:
        return getattr(_engine, name)
    
    if name in _view.__dict__:
        return getattr(_view, name)
    
    raise AttributeError(f"module 'ajishio' has no attribute '{name}'")  