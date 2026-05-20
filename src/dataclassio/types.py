import dataclasses as dcs
import io
import os
from enum import Enum
from pathlib import Path

import typing_extensions as tp

from .sentinels import CYCLE_DETECTED_T

__all__ = (
    "PathLike",
    "PathOrHandle",
    "ExtraFieldStrategy",
    "EFS",
    "DataclassInstance",
    "TDataclass",
    "FUNC_MAKER",
)


class DataclassInstance(tp.Protocol):
    __dataclass_fields__: tp.ClassVar[dict[str, dcs.Field]]


class ExtraFieldStrategy(Enum):
    STRICT = "strict"
    IGNORE = "ignore"
    CAPTURE = "capture"


PathLike: tp.TypeAlias = str | bytes | Path | os.PathLike
PathOrHandle: tp.TypeAlias = PathLike | io.IOBase
EFS = ExtraFieldStrategy
TDataclass = tp.TypeVar("TDataclass", bound=DataclassInstance)
FUNC_MAKER = tp.Callable[..., tp.Callable | CYCLE_DETECTED_T]
