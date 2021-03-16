# recursive `from module import *` excluding anything prefixed with '_':
from importlib import import_module
from pkgutil import walk_packages
for mod_info in walk_packages(__path__, __name__ + '.'):
    if mod_info.name.endswith('__main__'):
        continue
    mod = import_module(mod_info.name)
    try:
        names = mod.__dict__['__all__']
    except KeyError:
        names = [k for k in mod.__dict__ if not k.startswith('_')]
    globals().update({ k: getattr(mod, k) for k in names })