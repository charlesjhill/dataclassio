import dataclasses as dcs

import typing_extensions as tp

from dataclassio.sentinels import NO_DEFAULT, NoDefaultOr
from dataclassio.types import TNamespace

from .variables import set_variable_in_ns

__all__ = ("get_fields", "get_field_default", "field_has_default", "parse_default_expression")


def get_fields(cls: type, include_all=False) -> tuple[dcs.Field, ...]:
    if not dcs.is_dataclass(cls):
        msg = f"Unsupported type: {cls}. Currently, just `dataclasses.dataclass` is supported."
        raise TypeError(msg)

    if include_all:
        return tuple(
            v for v in cls.__dataclass_fields__.values() if v._field_type.name != "_FIELD_CLASSVAR"
        )

    return dcs.fields(cls)


def get_field_default(f: dcs.Field, *, call_factory: bool = True) -> NoDefaultOr[tp.Any]:
    """Get the default value for a field, if any."""
    if f.default is not dcs.MISSING:
        return f.default

    if f.default_factory is not dcs.MISSING:
        return f.default_factory() if call_factory else f.default_factory

    return NO_DEFAULT


def field_has_default(f: dcs.Field):
    return get_field_default(f, call_factory=False) is not NO_DEFAULT


def parse_default_expression(
    f: dcs.Field, namespace: TNamespace, precompute_factory=False
) -> NoDefaultOr[str]:
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

    def _register(val: tp.Any, is_call=False):
        suffix = "factory" if is_call else "default"
        ns_key = set_variable_in_ns(f"{f.name}_{suffix}", value=val, ns=namespace)
        return f"{ns_key}()" if is_call else ns_key

    literal_map = {list: "[]", dict: "{}", tuple: "()"}
    if f.default_factory in literal_map:
        return literal_map[f.default_factory]

    if f.default_factory is not dcs.MISSING:
        if not precompute_factory:
            return _register(f.default_factory, is_call=True)
        value = f.default_factory()
    elif f.default is not dcs.MISSING:
        value = f.default
    else:
        return NO_DEFAULT

    if value is None or isinstance(value, (int, float, str, bool)):
        return repr(value)
    return _register(value, False)
