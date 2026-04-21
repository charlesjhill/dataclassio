import dataclasses as dcs
import types

import typing_extensions as tp

from ..types import DataclassInstance


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


class SerializerData(tp.NamedTuple):
    """Extra information needed by `get_field_expression` to do its thing."""

    registry: tp.MutableMapping
    namespace: tp.MutableMapping
    maker_func: tp.Callable[[DataclassInstance], tp.Callable]
    cache_args: tuple


def get_field_expression(
    f: dcs.Field,
    serializer_data: SerializerData,
    direction: tp.Literal["to_dict", "from_dict"] = "from_dict",
):
    def build_expr(t: tp.TypeForm, expr_str: str):
        origin, args = tp.get_origin(t), tp.get_args(t)

        stripped_type, is_optional = strip_optional(t)

        if is_optional:
            inner_expr = build_expr(stripped_type, expr_str)
            if inner_expr == expr_str:
                return expr_str
            return f"({inner_expr} if {expr_str} is not None else None)"

        if dcs.is_dataclass(t):
            cache_key = (t, *serializer_data.cache_args)
            if cache_key not in serializer_data.registry:
                serializer_data.registry[cache_key] = None  # Refuse to recurse.
                serializer_data.registry[cache_key] = serializer_data.maker_func(t)
            fname = f"{func_prefix}_{t.__name__}"
            serializer_data.namespace[fname] = serializer_data.registry[cache_key]
            return f"{fname}({expr_str})"

        if origin in (list, tp.List):
            inner_type = args[0] if args else tp.Any
            inner_expr = build_expr(inner_type, "x")
            if inner_expr == "x":
                # No list comprehension needed.
                return expr_str
            return f"[{inner_expr} for x in {expr_str}]"

        if origin in (dict, tp.Mapping):
            k_type, v_type = args if args else (tp.Any, tp.Any)
            k_expr = build_expr(k_type, "k")
            v_expr = build_expr(v_type, "v")
            if k_expr == "k" and v_expr == "v":
                # No subparsing necesary, just return as is.
                return expr_str
            return f"{{{k_expr}: {v_expr} for k, v in {expr_str}.items()}}"

        if (origin is tp.Union or origin is types.UnionType) and (
            any(dcs.is_dataclass(a) for a in args)
        ):
            msg = "Union types where any non-None argument is a dataclass are not currently supported."
            raise RuntimeError(msg)

        return expr_str

    if direction == "from_dict":
        access_expr = f"dikt[{f.name!r}]"
        func_prefix = "deserialize"
    elif direction == "to_dict":
        access_expr = f"inst.{f.name}"
        func_prefix = "serialize"
    else:
        msg = f"Unknown {direction=}. Expected 'to_dict' or 'from_dict'."
        raise ValueError(msg)

    return build_expr(f.type, access_expr)
