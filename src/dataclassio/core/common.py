import dataclasses as dcs
import types

import typing_extensions as tp

from ..types import NO_DEFAULT

__all__ = ("get_fields", "field_has_default", "get_field_default", "strip_optional")


def get_fields(cls: type, include_all=False) -> tuple[dcs.Field, ...]:
    if not dcs.is_dataclass(cls):
        msg = f"Unsupported type: {cls}. Currently, just `dataclasses.dataclass` is supported."
        raise TypeError(msg)

    if include_all:
        return tuple(cls.__dataclass_fields__.values())

    return dcs.fields(cls)


def field_has_default(f: dcs.Field):
    return get_field_default(f, call_factory=False) is not NO_DEFAULT


def get_field_default(f: dcs.Field, *, call_factory: bool = True):
    """Get the default value for a field, if any."""
    if f.default is not dcs.MISSING:
        return f.default

    if f.default_factory is not dcs.MISSING:
        return f.default_factory() if call_factory else f.default_factory

    return NO_DEFAULT


def strip_optional(t: tp.TypeForm) -> tuple[tp.Any, bool]:
    """Check if a type annotation is an optional and if so, remove it.

    Returns:
        (type, bool): Corresponds to (non-None arguments of the type, flag if the type was an Optional)
    """
    origin, args = tp.get_origin(t), tp.get_args(t)
    if not (origin is tp.Union or origin is types.UnionType):
        return t, False

    non_none_args = [x for x in args if x is not types.NoneType]

    if len(non_none_args) == len(args):
        return t, False

    if len(non_none_args) == 1:
        # Must have been [None, X]
        return non_none_args[0], True

    # len(non_none_args) > 1
    return tp.Union[non_none_args], True
