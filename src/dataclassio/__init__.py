import importlib.metadata

from .config2 import FieldOptions as FieldOptions
from .io_mixin import IOMixin as IOMixin
from .types import EFS as EFS
from .types import ExtraFieldStrategy as ExtraFieldStrategy

__version__ = importlib.metadata.version("hill.dataclassio")
