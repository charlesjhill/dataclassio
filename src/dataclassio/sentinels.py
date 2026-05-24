from enum import Enum, auto

import typing_extensions as tp


class _Sentinels(Enum):
    NO_DEFAULT = auto()
    NO_VALUE = auto()
    IN_PROGRESS = auto()
    CYCLE_DETECTED = auto()


NO_DEFAULT: tp.Final = _Sentinels.NO_DEFAULT
NO_VALUE: tp.Final = _Sentinels.NO_VALUE
IN_PROGRESS: tp.Final = _Sentinels.IN_PROGRESS
CYCLE_DETECTED: tp.Final = _Sentinels.CYCLE_DETECTED


T = tp.TypeVar("T")
NoValueOr: tp.TypeAlias = tp.Union[T, tp.Literal[_Sentinels.NO_VALUE]]
NoDefaultOr: tp.TypeAlias = tp.Union[T, tp.Literal[_Sentinels.NO_DEFAULT]]
InProgressOr: tp.TypeAlias = tp.Union[T, tp.Literal[_Sentinels.IN_PROGRESS]]
CycleOr: tp.TypeAlias = tp.Union[T, tp.Literal[_Sentinels.CYCLE_DETECTED]]
