import dataclasses as dcs

import typing_extensions as tp

from ..types import EFS, DataclassInstance
from .common import (
    SerializerData,
    field_has_default,
    get_field_expression,
    get_fields,
    indent,
)

__all__ = (
    "make_from_dict_source_code",
    "make_from_dict",
)

_KNOWN_DESERIALIZERS: dict[tuple[type, EFS], tp.Callable[[tp.Mapping], tp.Any]] = {}
_EXTRA_FIELD_ATTR_NAME = "_extra_fields"


def make_from_dict_source_code(
    cls: type[DataclassInstance],
    funcname: str = "",
    extra_field_strategy=EFS.IGNORE,
    include_src_in_docstring: bool = True,
) -> tuple[str, dict[str, tp.Any]]:
    """Generate the source code and necessary namespace for a from_dict deserialization method."""
    funcname = funcname or f"deserialize_{cls.__name__}"
    lines = [
        f"def {funcname}(dikt):",
        f'  """Deserialize a {cls.__name__} instance from a dictionary."""',
        "  kw = {}",
    ]
    ns: dict[str, tp.Any] = {"kls": cls}

    fields = get_fields(cls)
    for f in fields:
        # Check if this field is itself a dataclass.
        field_expr = get_field_expression(
            f,
            serializer_data=SerializerData(
                registry=_KNOWN_DESERIALIZERS,
                namespace=ns,
                maker_func=lambda t: make_from_dict(t, extra_field_strategy=extra_field_strategy),
                cache_args=(extra_field_strategy,),
            ),
            direction="from_dict",
        )

        if field_has_default(f):
            # a little trickier. We want to add to kw if and only if it exists in the dikt
            strs = (
                f"if {f.name!r} in dikt:",
                f"  kw[{f.name!r}] = {field_expr}",
            )
            lines.extend(indent(strs))
        else:
            err_msg = f"{f.name!r} is a required attribute for {cls.__name__}, but was missing from {{dikt=}}."
            strs = (
                "try:",
                f"  kw[{f.name!r}] = {field_expr}",
                "except KeyError as exc:",
                f"  raise KeyError(f{err_msg!r}) from exc",
            )
            lines.extend(indent(strs))

    lines.append("  inst = kls(**kw)")
    lines.extend(
        indent(
            _handle_extra_fields(
                fields, extra_field_strategy, ns=ns, attribute_name=_EXTRA_FIELD_ATTR_NAME
            )
        )
    )
    lines.append("  return inst")

    # Generate a docstring
    if include_src_in_docstring:
        docstring_src = "\n".join(indent(lines[2:]))
        docstring = f'  """Deserialize a {cls.__name__} instance from a dictionary.\n\n{docstring_src}\n"""'
        lines[1] = docstring  # replace the existing docstring with this new one.

    f_src = "\n".join(lines)
    return f_src, ns


def make_from_dict(cls: type[DataclassInstance], extra_field_strategy: EFS = EFS.IGNORE):
    """Make a from_dict deserialization method for the given dataclass."""
    if (f := _KNOWN_DESERIALIZERS.get((cls, extra_field_strategy), None)) is not None:
        return f

    fname = f"deserialize_{cls.__name__}"
    src, ns = make_from_dict_source_code(
        cls, funcname=fname, extra_field_strategy=extra_field_strategy
    )
    exec(src, ns)
    return ns[fname]


def _handle_extra_fields(
    fields: tp.Iterable[dcs.Field],
    strategy: EFS,
    *,
    ns: dict,
    dict_name: str = "dikt",
    instance_name: str = "inst",
    attribute_name: str = "_extra_fields",
) -> list[str]:
    if strategy == EFS.IGNORE:
        # Excluding extra fields is the easiest thing known to man.
        return []

    # Precompute a lookup table with the known fields for this class.
    field_names_set_varname = "_KNOWN_FIELDS"
    ns[field_names_set_varname] = frozenset(f.name for f in fields)

    extra_field_expr = (
        f"{{k: v for k, v in {dict_name}.items() if k not in {field_names_set_varname}}}"
    )

    if strategy == EFS.STRICT:
        err_msg = f"Extra fields are strictly prohibited for {{{instance_name}=}}"
        return [
            f"extra_kw = {extra_field_expr}",
            "if extra_kw:",
            f"  msg = (f'{err_msg}, but the the input dictionary had'",
            "         f' the following extra fields: {list(extra_kw)}')",
            "  raise ValueError(msg)",
            f"{instance_name}.{attribute_name} = extra_kw",
        ]

    if strategy == EFS.CAPTURE:
        return [f"{instance_name}.{attribute_name} = {extra_field_expr}"]

    msg = f"Unexpected {strategy=}. Must be an ExtraFieldStrategy enumeration."
    raise ValueError(msg)
