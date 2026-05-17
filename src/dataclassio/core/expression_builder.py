import dataclasses as dcs
import enum
import types
from datetime import datetime

import typing_extensions as tp

from ..config import NoValue, _TotalDioOptions
from ..types import DataclassInstance
from .common import get_fields, make_variable_name, strip_optional

__all__ = ("SerializerData", "build_expr", "get_field_expression")


class SerializerData(tp.NamedTuple):
    """Extra information needed by `build_expr` to parse nested dataclasses."""

    registry: tp.MutableMapping
    namespace: tp.MutableMapping
    maker_func: tp.Callable[[type[DataclassInstance]], tp.Callable]
    cache_key: tuple[tp.Hashable, str]
    options: _TotalDioOptions

    def get_dataclass_function(self, kls: type[DataclassInstance]) -> tuple[tp.Callable, str]:
        """Return a function for making a kls, and its suggested rootname."""
        # Get the maker func
        cache_data, postfix = self.cache_key
        cache_key = (kls, cache_data)
        if cache_key not in self.registry:
            self.registry[cache_key] = self.maker_func(kls)
        maker_func = self.registry[cache_key]

        return maker_func, f"{kls.__name__}{postfix}"


def build_expr(
    t: tp.TypeForm,
    expr_str: str,
    serializer_data: SerializerData,
    func_prefix: tp.Literal["deserialize", "serialize"] = "deserialize",
) -> str:
    """Create the expression to pack or unpack a type.

    This function currently supports:

    - Optional expressions: `Optional[T]`, `T | None`, or `Union[T, None]`
    - Embedded dataclasses: `DataclassType`
    - Lists: `list[T]`
    - Dicts: `dict[TK, TV]`
    - Enums: `Enum`
    - Datetimes
    - fundamental types: `int`, `float`, `str`, `bool`

    Where the `T`, `TK`, and `TV` type variables may be any other type listed in the table.
    For instance, `dict[str, list[DataclassType | None]]` is supported.

    Args:
        t: A type for which to create a packing/unpacking expression.
        expr_str: string representation of how to access the value to pack or unpack.
            e.g., `"inst.attribute_name"` or `"dikt['attributeName']"`
        serializer_data: The structure to track information for parsing embedded dataclasses.
        func_prefix: Prefix for dynamically created functions to pack or unpack embedded
            dataclasses.
    """
    if isinstance(t, dcs.InitVar):
        # Strip the InitVar wrapper
        t = t.type

    origin, args = tp.get_origin(t), tp.get_args(t)
    stripped_type, is_optional = strip_optional(t)

    # 1. Handle composite types (e.g., Optionals and containers)
    if is_optional:
        inner_expr = build_expr(
            stripped_type, expr_str, serializer_data=serializer_data, func_prefix=func_prefix
        )
        if inner_expr == expr_str:
            return expr_str
        return f"({inner_expr} if {expr_str} is not None else None)"

    if origin in (list, tp.List):
        inner_type = args[0] if args else tp.Any
        inner_expr = build_expr(
            inner_type, "x", serializer_data=serializer_data, func_prefix=func_prefix
        )
        if inner_expr == "x":
            # No list comprehension needed.
            return expr_str
        return f"[{inner_expr} for x in {expr_str}]"

    if origin in (dict, tp.Mapping):
        k_type, v_type = args if args else (tp.Any, tp.Any)
        k_expr = build_expr(k_type, "k", serializer_data=serializer_data, func_prefix=func_prefix)
        v_expr = build_expr(v_type, "v", serializer_data=serializer_data, func_prefix=func_prefix)
        if k_expr == "k" and v_expr == "v":
            # No subparsing necesary, just return as is.
            return expr_str
        return f"{{{k_expr}: {v_expr} for k, v in {expr_str}.items()}}"

    if (origin is tp.Union or origin is types.UnionType) and any(
        dcs.is_dataclass(a) for a in args
    ):
        if not all(dcs.is_dataclass(a) for a in args):
            msg = (
                f"type={t}, generated via {expr_str=} is not supported."
                " Union types with any dataclass options must be _all_ dataclasses."
            )
            raise RuntimeError(msg)
        # check the field options.
        discriminator = serializer_data.options["discriminator"]
        if discriminator is NoValue:
            msg = (
                f"type={t}, generated via {expr_str=} is not supported."
                " A discriminator field was not provided."
            )
        assert isinstance(discriminator, str)

        # base case
        if func_prefix == "deserialize":
            # from_dict
            inner_expr = f"{expr_str}[{discriminator!r}]"
        else:
            # to_dict
            inner_expr = f"{expr_str}.{discriminator!s}"

        # build list of types:
        maker_map_data: dict[str, tp.Any] = {}
        for cls_option in args:
            fields = [f for f in get_fields(cls_option) if f.name == discriminator]
            if not fields:
                msg = (
                    f"type={t}, generated via {expr_str=} is not supported."
                    f"Union option {cls_option} does not have a field with the name {discriminator}."
                )
                raise RuntimeError(msg)
            # get the type.
            f_type = fields[0].type
            discrim_origin = tp.get_origin(f_type)
            discrim_args = tp.get_args(f_type)
            if discrim_origin is not tp.Literal or not all(
                isinstance(x, str) for x in discrim_args
            ):
                msg = (
                    f"type={t}, generated via {expr_str=} is not supported."
                    f"Union option {cls_option} has a field with name {discriminator}, but it is not a Literal with string arguments."
                )
                raise RuntimeError(msg)

            # Get the maker func
            maker_func, _ = serializer_data.get_dataclass_function(cls_option)

            for arg_name in discrim_args:
                if arg_name in maker_map_data:
                    msg = (
                        f"type={t}, generated via {expr_str=} is not supported."
                        f"The union options have duplicate values for {discriminator}."
                    )
                    raise RuntimeError(msg)
                maker_map_data[arg_name] = maker_func

        fname = make_variable_name("_DISAMBIGUATOR", ns=serializer_data.namespace)
        serializer_data.namespace[fname] = maker_map_data
        # build the final expression:
        return f"{fname}[{inner_expr}]({expr_str})"

    # 2. Handle atoms (note that we don't recurse into `build_expr`)
    if dcs.is_dataclass(t):
        maker_func, root_name = serializer_data.get_dataclass_function(t)

        fname = make_variable_name(f"{func_prefix}_{root_name}")
        serializer_data.namespace[fname] = maker_func
        return f"{fname}({expr_str})"

    if isinstance(t, type) and issubclass(t, enum.Enum):
        # For enum types, convert to the Enum.
        if func_prefix == "serialize":
            # To Dict
            return f"{expr_str}.value"

        # From Dict
        enum_name = t.__name__
        serializer_data.namespace[enum_name] = t  # Ensure the Enum type is in the namespace.

        # N.B. Doing `v if isinstance(v := {expr_str}, Enum) else Enum(v)` is slower than this.
        return f"{enum_name}({expr_str})"

    if t is datetime:
        if func_prefix == "serialize":
            # To dict
            return f"({expr_str}).isoformat()"

        # from dict
        fname = make_variable_name("_fromisoformat")
        serializer_data.namespace[fname] = datetime.fromisoformat
        return f"{fname}({expr_str})"

    # 3. Fallbacks
    return expr_str


def get_field_expression(
    f: dcs.Field,
    serializer_data: SerializerData,
    direction: tp.Literal["to_dict", "from_dict"] = "from_dict",
) -> str:
    """Create the expression to pack or unpack a dataclass field.

    This is mostly a convenience wrapper around `build_expr`.

    Args:
        f: The dataclasses.Field to parse.
        serializer_data: The structure to track information for parsing embedded dataclasses.
        direction: Whether to create an expression for serializing (to_dict) or deserializing (from_dict).
    """
    if direction == "from_dict":
        access_expr = f"dikt[{f.name!r}]"
        func_prefix = "deserialize"
    elif direction == "to_dict":
        access_expr = f"inst.{f.name}"
        func_prefix = "serialize"
    else:
        msg = f"Unknown {direction=}. Expected 'to_dict' or 'from_dict'."
        raise ValueError(msg)

    return build_expr(
        f.type, access_expr, serializer_data=serializer_data, func_prefix=func_prefix
    )
