import dataclasses as dcs
import types

import typing_extensions as tp

from ..types import NO_DEFAULT

__all__ = (
    "get_fields",
    "field_has_default",
    "get_field_default",
    "strip_optional",
    "parse_default_expression",
)


def get_fields(cls: type, include_all=False) -> tuple[dcs.Field, ...]:
    if not dcs.is_dataclass(cls):
        msg = f"Unsupported type: {cls}. Currently, just `dataclasses.dataclass` is supported."
        raise TypeError(msg)

    if include_all:
        return tuple(
            v for v in cls.__dataclass_fields__.values() if v._field_type.name != "_FIELD_CLASSVAR"
        )

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


def parse_default_expression(f: dcs.Field, namespace: tp.MutableMapping, precompute_factory=False):
    """Get an expression (and populate the namespace) with the default value for a field.

    Args:
        f: The field to parse.
        namespace: A mutable mapping to store precomputed default values.
        precompute_factory: Flag to precompute the value of a factory function. If true,
            the factory is called once at compile time and its value is stored for use later in
            the namespace. If False, the returned expression will invoke the factory function
            at runtime.

    Returns:
        A string if there if the field had a default or default_factory. Otherwise, the
        `NO_DEFAULT` sentinel.
    """

    def _register(val: tp.Any, suffix: str, is_call=False):
        ns_key = f"_dio_{f.name}_{suffix}"
        namespace[ns_key] = val
        return f"{ns_key}()" if is_call else ns_key

    def _is_atom(x):
        return x is None or isinstance(x, (int, float, str, bool))

    literal_map = {list: "[]", dict: "{}", tuple: "()"}
    if f.default_factory in literal_map:
        return literal_map[f.default_factory]

    if f.default_factory is not dcs.MISSING:
        if not precompute_factory:
            return _register(f.default_factory, "default_factory", is_call=True)
        value = f.default_factory()
    elif f.default is not dcs.MISSING:
        value = f.default
    else:
        return NO_DEFAULT

    if _is_atom(value):
        return repr(value)
    return _register(value, "default")


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
