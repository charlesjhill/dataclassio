import dataclasses as dcs
import logging
import types

import typing_extensions as tp

from ..types import DataclassInstance

_logger = logging.getLogger("dataclass_io")


def indent(strs: tp.Iterable[str], level=2):
    """Indent text by the given level."""
    for s in strs:
        yield f"{level * ' '}{s}"


def get_fields(cls: type) -> tuple[dcs.Field, ...]:
    try:
        return dcs.fields(cls)
    except TypeError as e:
        msg = f"Unsupported type: {cls}. Currently, just `dataclasses.dataclass` is supported."
        raise TypeError(msg) from e


def field_has_default(f: dcs.Field):
    return (f.default is not dcs.MISSING) or (f.default_factory is not dcs.MISSING)


def field_get_default(f: dcs.Field):
    if f.default is not dcs.MISSING:
        return f.default

    if f.default_factory is not dcs.MISSING:
        return f.default_factory()

    return None


def get_dataclass_from_field_type(f: dcs.Field) -> tp.Optional[type[DataclassInstance]]:
    # the field type is f: Dataclass or f: Optional[Dataclass] if
    # the type is directly a dataclass OR has the form Union[Dataclass, NoneType]
    t = f.type

    # TODO: We will need to make this recursive to support freakier expressions.

    if isinstance(t, str):
        _logger.warning("Got str for the type of %s", f.name)
        return None

    if dcs.is_dataclass(t):
        return tp.cast(type[DataclassInstance], t)

    # Check for Optional[Dataclass]
    origin = tp.get_origin(t)
    args = tp.get_args(t)

    if isinstance(origin, str) or any(isinstance(a, str) for a in args):
        _logger.warning("Got str in origin/args for the field %s", f.name)

    parsed_dc_types = [x for x in args if dcs.is_dataclass(x) and isinstance(x, type)]

    if len(parsed_dc_types) >= 2:
        msg = f"Multiple top-level dataclasses in the type annotation for field={f}."
        raise ValueError(msg)

    if len(parsed_dc_types) == 1:
        # There was one valid option, which we will return
        return parsed_dc_types[0]


def strip_optional(t: type) -> tuple[tp.Any, bool]:
    """Check if a type annotation is an optional and if so, remove it.

    Returns:
        (type, bool): Corresponds to (non-None arguments of the type, flag if the type was an Optional)
    """
    origin, args = tp.get_origin(t), tp.get_args(t)

    if origin is not tp.Union:
        return t, False

    non_none_args = [x for x in args if x is not types.NoneType]

    if len(non_none_args) == len(args):
        return t, False

    if len(non_none_args) == 1:
        # Must have been [None, X]
        return non_none_args[0], True

    # len(non_none_args) > 1
    return tp.Union[non_none_args], True


def get_field_expression(
    f: dcs.Field,
    field_converter_name: str = "",
    direction: tp.Literal["to_dict", "from_dict"] = "from_dict",
):
    if direction == "from_dict":
        access_expr = f"dikt[{f.name!r}]"
    elif direction == "to_dict":
        access_expr = f"inst.{f.name}"
    else:
        msg = f"Unknown {direction=}. Expected 'to_dict' or 'from_dict'."
        raise ValueError(msg)

    if not field_converter_name:
        # no field_converter. This is simple.
        return access_expr

    # If we are here, we know there is a dataclass we need to hydrate somewhere in the typehint.
    stripped_type, is_optional = strip_optional(f.type)
    field_container_type = tp.get_origin(stripped_type)

    if field_container_type is None:
        # Support scalar dataclasses

        if is_optional and direction == "to_dict":
            # We shouldn't call a field convert on a nested dataclass if it could be optional and is None.
            expr = f"({field_converter_name}(x) if (x := {access_expr}) is not None else None)"
        else:
            expr = f"{field_converter_name}({access_expr})"

        return expr

    if field_container_type is list:
        return f"[{field_converter_name}(d) for d in {access_expr}]"

    if field_container_type is dict:
        field_args = tp.get_args(f.type)
        if len(field_args) == 2 and dcs.is_dataclass(field_args[1]):
            # dict[..., Dataclass]
            return f"{{k: {field_converter_name}(v) for k, v in {access_expr}.items()}}"

        if len(field_args) == 2 and dcs.is_dataclass(field_args[0]):
            # dict[Dataclass, ...]
            return f"{{{field_converter_name}(k): v for k, v in {access_expr}.items()}}"

        msg = f"Unsupported dict type-hints: field={f}"
        raise NotImplementedError(msg)

    # It is not list, dict, none or OPTIONAL[...]
    msg = f"Unsupported field_container_type={field_container_type} for field={f}."
    raise NotImplementedError(msg)
