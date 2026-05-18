from enum import Enum, auto

import typing_extensions as tp


class _Sentinels(Enum):
    NO_DEFAULT = auto()
    NO_VALUE = auto()
    IN_PROGRESS = auto()
    CYCLE_DETECTED = auto()


NO_DEFAULT: tp.Final = _Sentinels.NO_DEFAULT
NO_DEFAULT_T: tp.TypeAlias = tp.Literal[_Sentinels.NO_DEFAULT]

NO_VALUE: tp.Final = _Sentinels.NO_VALUE
NO_VALUE_T: tp.TypeAlias = tp.Literal[_Sentinels.NO_VALUE]

IN_PROGRESS: tp.Final = _Sentinels.IN_PROGRESS
IN_PROGRESS_T: tp.TypeAlias = tp.Literal[_Sentinels.IN_PROGRESS]

CYCLE_DETECTED: tp.Final = _Sentinels.CYCLE_DETECTED
CYCLE_DETECTED_T: tp.TypeAlias = tp.Literal[_Sentinels.CYCLE_DETECTED]
