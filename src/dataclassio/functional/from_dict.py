import dataclasses as dcs
import inspect

import typing_extensions as tp

from ..config import (
    DioOptions,
    _TotalDioOptions,
    get_composite_options,
    get_options_cache_key,
    get_passthrough_options,
)
from ..core import (
    SerializerData,
    TextLines,
    field_has_default,
    get_field_expression,
    get_fields,
    make_variable_name,
    parse_default_expression,
)
from ..types import EFS, DataclassInstance
from ._shared import maker_core

__all__ = (
    "make_from_dict_source_code",
    "make_from_dict",
)

_KNOWN_DESERIALIZERS: dict[tuple[type, tp.Any], tp.Callable[[tp.Mapping], tp.Any]] = {}
_EXTRA_FIELD_ATTR_NAME = "_extra_fields"
_SPACER = "  "


class FieldSpec(tp.NamedTuple):
    field: dcs.Field
    var_name: str
    expr: str
    has_default: bool

    @property
    def name(self):
        return self.field.name

    @property
    def kw_only(self):
        return self.field.kw_only


def make_from_dict_source_code(
    cls: type[DataclassInstance],
    *,
    funcname: str = "",
    call_options: _TotalDioOptions | DioOptions | None = None,
    _field_options: _TotalDioOptions | DioOptions | None = None,
) -> tuple[TextLines, dict[str, tp.Any]]:
    """Generate the source code and necessary namespace for a from_dict deserialization method."""
    funcname = funcname or f"deserialize_{cls.__name__}"
    cls_factory_name = make_variable_name("cls")
    ns: dict[str, tp.Any] = {cls_factory_name: cls}
    current_variable_names: set = {cls_factory_name, "dikt", "_exc"}

    fields = get_fields(cls, include_all=True)
    field_data: dict[str, FieldSpec] = {}

    for f in fields:
        if not f.init:
            # init=False field. Don't try to read it in.
            continue

        # extract and integrate field-options
        field_opts = f.metadata.get("dio")
        resolved_options = get_composite_options(field_opts, call_options)

        # Remove field-shallow configuration options before they (possibly) propagate.
        passthrough_field_opts = get_passthrough_options(field_opts)
        cache_key = get_options_cache_key(
            get_composite_options(
                passthrough_field_opts,
                call_options,
            ),
            "from_dict",
        )

        # Get the expression for parsing this field.
        field_expr = get_field_expression(
            f,
            direction="from_dict",
            serializer_data=SerializerData(
                registry=_KNOWN_DESERIALIZERS,
                namespace=ns,
                maker_func=lambda t, m=passthrough_field_opts: make_from_dict(
                    t, options=call_options, _field_options=m
                ),
                cache_key=cache_key,
                options=resolved_options,
            ),
        )

        var_name = make_variable_name(f.name, ns=current_variable_names.union(ns))
        current_variable_names.add(var_name)

        field_data[f.name] = FieldSpec(
            f,
            var_name,
            field_expr,
            field_has_default(f),
        )

    local_options = get_composite_options(call_options=call_options, field_options=_field_options)

    # Assemble the final function body
    lines = TextLines(spacer=_SPACER)
    with lines.indent(f"def {funcname}(dikt):"):
        lines.append(f'"""Deserialize a {cls.__name__} instance from a dictionary."""')
        for fs in field_data.values():
            if not fs.has_default:
                # Since there is no default, wrap in a try/except.
                err_msg = f"{fs.name!r} is a required attribute for {cls.__name__}, but was missing from {{dikt=}}."
                with lines.indent("try:"):
                    lines.append(f"{fs.var_name} = {fs.expr}")
                with lines.indent("except KeyError as _exc:"):
                    # Note the f-string!
                    lines.append(f"raise KeyError(f{err_msg!r}) from _exc")
            else:
                # There is a default value. Extract its value in the else
                with lines.indent(f"if {fs.name!r} in dikt:"):
                    lines.append(f"{fs.var_name} = {fs.expr}")
                with lines.indent("else:"):
                    default_expr = parse_default_expression(fs.field, ns)
                    lines.append(f"{fs.var_name} = {default_expr}")

        # Now we need to build the constructor string. At this point, we have a local variable
        #  for every initializable argument. We need to do two things:
        # 1. Get these in the same order as the __init__ function
        # 2. Ensure we are using keyword-argument for kw-only fields.
        init_parts = []
        for param in inspect.signature(cls).parameters.values():
            fs = field_data[param.name]
            if fs.kw_only:
                init_parts.append(f"{fs.name}={fs.var_name}")
            else:
                assert param.kind not in (
                    inspect.Parameter.KEYWORD_ONLY,
                    inspect.Parameter.VAR_KEYWORD,
                )
                init_parts.append(fs.var_name)
        data_str = ", ".join(init_parts)

        extras = _handle_extra_fields(
            fields,
            local_options["extra_field_strategy"],
            ns=ns,
            attribute_name=_EXTRA_FIELD_ATTR_NAME,
        )
        if extras:
            lines.append(f"inst = {cls_factory_name}({data_str})")
            lines.extend(extras)
            lines.append("return inst")
        else:
            lines.append(f"return {cls_factory_name}({data_str})")

    return lines, ns


def make_from_dict(
    cls: type[DataclassInstance],
    *,
    options: _TotalDioOptions | DioOptions | None = None,
    _field_options: _TotalDioOptions | DioOptions | None = None,
    **kw: tp.Unpack[DioOptions],
):
    """Make a from_dict deserialization method for the given dataclass.

    Args:
        cls: The Dataclass type to generate the deserializer for.
        options: `DioOptions` to use to customize the code generation process. These may also
            be provided via **kwargs. These propagate through to the fields of this dataclass
            type.
        _field_options: `DioOptions` that _do not_ propagate. Used for field-level configuration
            that is applying to this object shallowly.
    """
    return maker_core(
        cls,
        _KNOWN_DESERIALIZERS,
        make_from_dict_source_code,
        "deserialize",
        "from_dict",
        options=options,
        _field_options=_field_options,
        **kw,
    )


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
    #  N.B. This will include init=False fields, thus preventing them from being counted
    #       as an extra.
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
