import dataclasses as dcs

import typing_extensions as tp

from ..core import SerializerData, TextLines, field_has_default, get_field_expression, get_fields
from ..types import EFS, DataclassInstance

__all__ = (
    "make_from_dict_source_code",
    "make_from_dict",
)

_KNOWN_DESERIALIZERS: dict[tuple[type, EFS], tp.Callable[[tp.Mapping], tp.Any]] = {}
_EXTRA_FIELD_ATTR_NAME = "_extra_fields"
_SPACER = "  "


def make_from_dict_source_code(
    cls: type[DataclassInstance],
    funcname: str = "",
    extra_field_strategy=EFS.IGNORE,
) -> tuple[TextLines, dict[str, tp.Any]]:
    """Generate the source code and necessary namespace for a from_dict deserialization method."""
    funcname = funcname or f"deserialize_{cls.__name__}"
    ns: dict[str, tp.Any] = {"kls": cls}

    fields = get_fields(cls)
    field_expressions: list[tuple[str, str, bool]] = []
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
        field_expressions.append((f.name, field_expr, field_has_default(f)))

    # Assemble the final function body
    lines = TextLines(spacer=_SPACER)
    with lines.indent(f"def {funcname}(dikt):"):
        lines.append(f'"""Deserialize a {cls.__name__} instance from a dictionary."""')
        lines.append("kw = {}")
        for fname, field_expr, has_default in field_expressions:
            if has_default:
                # a little trickier. We want to add to kw if and only if it exists in the dikt
                with lines.indent(f"if {fname!r} in dikt:"):
                    lines.append(f"kw[{fname!r}] = {field_expr}")
            else:
                err_msg = f"{fname!r} is a required attribute for {cls.__name__}, but was missing from {{dikt=}}."
                with lines.indent("try:"):
                    lines.append(f"kw[{fname!r}] = {field_expr}")
                with lines.indent("except KeyError as exc:"):
                    # Note the f-string
                    lines.append(f"raise KeyError(f{err_msg!r}) from exc")

        extras = _handle_extra_fields(
            fields, extra_field_strategy, ns=ns, attribute_name=_EXTRA_FIELD_ATTR_NAME
        )
        if extras:
            lines.append("inst = kls(**kw)")
            lines.extend(extras)
            lines.append("return inst")
        else:
            lines.append("return kls(**kw)")

    return lines, ns


def make_from_dict(
    cls: type[DataclassInstance],
    extra_field_strategy: EFS = EFS.IGNORE,
    include_src_in_docstring: bool = False,
):
    """Make a from_dict deserialization method for the given dataclass."""
    if (f := _KNOWN_DESERIALIZERS.get((cls, extra_field_strategy), None)) is not None:
        return f

    fname = f"deserialize_{cls.__name__}"
    src, ns = make_from_dict_source_code(
        cls, funcname=fname, extra_field_strategy=extra_field_strategy
    )
    exec(src.export(), ns)
    func = ns[fname]
    if include_src_in_docstring:
        func.__doc__ += f"\n\n{src[2:]!s}\n"

    return func


def _handle_extra_fields(
    fields: tp.Iterable[dcs.Field],
    strategy: EFS,
    *,
    ns: dict,
    dict_name: str = "dikt",
    instance_name: str = "inst",
    attribute_name: str = "_extra_fields",
) -> TextLines:
    lines = TextLines(spacer=_SPACER)
    if strategy == EFS.IGNORE:
        # Excluding extra fields is the easiest thing known to man.
        return lines

    # Precompute a lookup table with the known fields for this class.
    field_names_set_varname = "_KNOWN_FIELDS"
    ns[field_names_set_varname] = frozenset(f.name for f in fields)

    extra_field_expr = (
        f"{{k: v for k, v in {dict_name}.items() if k not in {field_names_set_varname}}}"
    )

    if strategy == EFS.STRICT:
        err_msg = f"Extra fields are strictly prohibited for {{{instance_name}=}}"
        lines.append(f"extra_kw = {extra_field_expr}")
        with lines.indent("if extra_kw:"):
            lines.append(f"msg = (f'{err_msg}, but the the input dictionary had'")
            lines.append("       f' the following extra fields: {list(extra_kw)}')")
            lines.append("raise ValueError(msg)")
        return lines

    if strategy == EFS.CAPTURE:
        lines.append(f"{instance_name}.{attribute_name} = {extra_field_expr}")
        return lines

    msg = f"Unexpected {strategy=}. Must be an ExtraFieldStrategy enumeration."
    raise ValueError(msg)
