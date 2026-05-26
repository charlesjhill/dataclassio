import dataclasses as dcs
import io
import os
from enum import Enum
from pathlib import Path

import typing_extensions as tp

from dataclassio.sentinels import CycleOr

if tp.TYPE_CHECKING:
    from dataclassio.config2 import ResolvedConfig
    from dataclassio.core.lines import TextLines


__all__ = (
    "PathLike",
    "PathOrHandle",
    "ExtraFieldStrategy",
    "EFS",
    "DataclassInstance",
    "TDataclass",
    "SourceCodeMaker",
    "TNamespace",
    "FunctionMaker",
)


class DataclassInstance(tp.Protocol):
    __dataclass_fields__: tp.ClassVar[dict[str, dcs.Field]]


class ExtraFieldStrategy(Enum):
    STRICT = "strict"
    IGNORE = "ignore"
    CAPTURE = "capture"


EFS = ExtraFieldStrategy
TDataclass = tp.TypeVar("TDataclass", bound=DataclassInstance)
PathLike: tp.TypeAlias = str | Path | os.PathLike
PathOrHandle: tp.TypeAlias = PathLike | io.IOBase
TNamespace: tp.TypeAlias = dict[str, tp.Any]


class SourceCodeMaker(tp.Protocol):
    def __call__(
        self,
        cls: type[DataclassInstance],
        *,
        frame_config: "ResolvedConfig",
        _ns: TNamespace | None = None,
    ) -> "TextLines": ...


FunctionMaker: tp.TypeAlias = tp.Callable[[type[TDataclass]], CycleOr[tp.Callable]]
