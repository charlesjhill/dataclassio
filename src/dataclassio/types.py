import dataclasses as dcs
import io
import os
from enum import Enum
from functools import total_ordering
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


PathLike: tp.TypeAlias = str | bytes | Path | os.PathLike
PathOrHandle: tp.TypeAlias = PathLike | io.IOBase


class DataclassInstance(tp.Protocol):
    __dataclass_fields__: tp.ClassVar[dict[str, dcs.Field]]


TDataclass = tp.TypeVar("TDataclass", bound=DataclassInstance)


@total_ordering
class ExtraFieldStrategy(Enum):
    STRICT = "strict"
    IGNORE = "ignore"
    CAPTURE = "capture"

    def __lt__(self, other):
        if not isinstance(other, ExtraFieldStrategy):
            return NotImplemented
        return self.value < other.value


EFS = ExtraFieldStrategy

FUNC_MAKER = tp.Callable[..., tp.Callable | CYCLE_DETECTED_T]
