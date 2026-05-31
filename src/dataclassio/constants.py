from enum import Enum, auto

import typing_extensions as tp

__all__ = (
    "_EXTRA_FIELD_ATTR_NAME",
    "_SPACER",
    "NO_DEFAULT",
    "NoDefaultOr",
    "NO_VALUE",
    "NoValueOr",
    "IN_PROGRESS",
    "InProgressOr",
    "CYCLE_DETECTED",
    "CycleOr",
    "ALIAS_OBJ",
    "AliasOr",
    "_PRE_TO_DICT_HOOK",
    "_POST_TO_DICT_HOOK",
    "_PRE_FROM_DICT_HOOK",
    "_POST_FROM_DICT_HOOK",
)


_EXTRA_FIELD_ATTR_NAME = "_extra_fields"
_SPACER = "  "

_PRE_TO_DICT_HOOK = "__pre_to_dict__"
_POST_TO_DICT_HOOK = "__post_to_dict__"
_PRE_FROM_DICT_HOOK = "__pre_from_dict__"
_POST_FROM_DICT_HOOK = "__post_from_dict__"


class _Sentinels(Enum):
    NO_DEFAULT = auto()
    NO_VALUE = auto()
    IN_PROGRESS = auto()
    CYCLE_DETECTED = auto()
    ALIAS_OBJ = auto()


NO_DEFAULT: tp.Final = _Sentinels.NO_DEFAULT
NO_VALUE: tp.Final = _Sentinels.NO_VALUE
IN_PROGRESS: tp.Final = _Sentinels.IN_PROGRESS
CYCLE_DETECTED: tp.Final = _Sentinels.CYCLE_DETECTED
ALIAS_OBJ: tp.Final = _Sentinels.ALIAS_OBJ


T = tp.TypeVar("T")
NoValueOr: tp.TypeAlias = T | tp.Literal[_Sentinels.NO_VALUE]
NoDefaultOr: tp.TypeAlias = T | tp.Literal[_Sentinels.NO_DEFAULT]
InProgressOr: tp.TypeAlias = T | tp.Literal[_Sentinels.IN_PROGRESS]
CycleOr: tp.TypeAlias = T | tp.Literal[_Sentinels.CYCLE_DETECTED]
AliasOr: tp.TypeAlias = T | tp.Literal[_Sentinels.ALIAS_OBJ]
