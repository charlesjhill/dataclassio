import typing_extensions as tp

from dataclassio.sentinels import CYCLE_DETECTED, CYCLE_DETECTED_T

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
    parse_default_expression,
)
from ..types import DataclassInstance, TDataclass
from ._shared import maker_core
from .from_dict import _EXTRA_FIELD_ATTR_NAME

_KNOWN_SERIALIZERS: dict[tuple[type, tp.Hashable], tp.Callable[[DataclassInstance], dict]] = {}
_SPACER = "  "


def make_to_dict_source_code(
    cls: type[DataclassInstance],
    funcname: str = "",
    call_options: _TotalDioOptions | DioOptions | None = None,
    _field_options: _TotalDioOptions | DioOptions | None = None,
    _ns: dict | None = None,
) -> TextLines:
    funcname = funcname or f"serialize_{cls.__name__}"
    if _ns is None:
        _ns = {}

    # Currently unused. Maybe in the future?
    # local_options = get_composite_options(_field_options, call_options)

    # Start building up the output.
    # We are going to serialize objects. We also need to check if they
    #  have extra fields. We can assume we have fully-formed instances.
    # N.B., We initialize the dictionary with any extra fields. By construction, they
    #  are disjoint with the dataclass fields
    default_check_lines = TextLines(spacer=_SPACER)
    literal_lines = TextLines(spacer=_SPACER)

    for f in get_fields(cls):
        # Form the expression itself that gets the value.
        field_opts = f.metadata.get("dio")
        resolved_options = get_composite_options(field_opts, call_options)

        # Remove field-shallow configuration options before they (possibly) propagate.
        passthrough_field_opts = get_passthrough_options(field_opts)
        cache_key = get_options_cache_key(
            get_composite_options(
                passthrough_field_opts,
                call_options,
            ),
            "to_dict",
        )

        field_expr = get_field_expression(
            f,
            serializer_data=SerializerData(
                registry=_KNOWN_SERIALIZERS,
                namespace=_ns,
                maker_func=lambda t, m=passthrough_field_opts: make_to_dict(
                    t, options=call_options, _field_options=m
                ),
                cache_key=cache_key,
                options=resolved_options,
                func_prefix="serialize",
            ),
        )

        # Now on to the big leagues. so, invoked `field_expr` should get us the value to use
        #  for this field. Now, we just have to pack it up into a dictionary. We need to handle
        #  defaults, though. If we are skipping defaults, we need to include field defaults
        #  in the namespace so we can compare against them later.

        # We need an explicit check for `has_default` since `get_default` cannot distinguish between
        # "no default" and "default=None".
        if resolved_options["skip_if_default"] and field_has_default(f):
            # Add a hardcoded gate that checks if we have a default value. If so, don't
            #  add anything to the dict.
            default_expression = parse_default_expression(f, _ns, precompute_factory=False)
            comparator = "is not" if default_expression == "None" else "!="

            with default_check_lines.indent(
                f"if inst.{f.name} {comparator} {default_expression}:"
            ):
                default_check_lines.append(f"dikt[{f.name!r}] = {field_expr}")
        else:
            # Either this field has no default, or we are keeping all values. This easy.
            literal_lines.append(f"{f.name!r}: {field_expr},")

    # Handle the extra fields. If there are no "default checking" lines, we can pack this into
    #  the bottom of the literals. If we do check some fields for their default value,
    #  we include the extra field population right before export to try keeping the "real"
    #  fields in order in the resulting dictionary.

    if not default_check_lines:
        literal_lines.append(f"**getattr(inst, {_EXTRA_FIELD_ATTR_NAME!r}, {{}}),")
    else:
        with default_check_lines.indent(f"if hasattr(inst, {_EXTRA_FIELD_ATTR_NAME!r}):"):
            default_check_lines.append(f"dikt.update(inst.{_EXTRA_FIELD_ATTR_NAME})")

    lines = TextLines(spacer=_SPACER)
    with lines.indent(f"def {funcname}(inst):"):
        lines.append(f'"""Serialize a {cls.__name__} instance into a dictionary."""')
        if literal_lines:
            with lines.indent("dikt = {"):
                lines.extend(literal_lines)
            lines.append("}")
        else:
            lines.append("dikt = {}")
        lines.extend(default_check_lines)
        lines.append("return dikt")

    return lines


def make_to_dict(
    cls: type[TDataclass],
    *,
    options: _TotalDioOptions | DioOptions | None = None,
    _field_options: _TotalDioOptions | DioOptions | None = None,
    _ns: dict | None = None,
    **kw: tp.Unpack[DioOptions],
) -> tp.Callable[[TDataclass], dict[str, tp.Any]] | CYCLE_DETECTED_T:
    """Make a to_dict serialization method for the given dataclass.

    Args:
        cls: The Dataclass type to generate the serializer for.
        options: `DioOptions` to use to customize the code generation process. These may also
            be provided via **kwargs. These propagate through to the fields of this dataclass
            type.
        _field_options: `DioOptions` that _do not_ propagate. Used for field-level configuration
            that is applying to this object shallowly.
    """
    return maker_core(
        cls,
        _KNOWN_SERIALIZERS,
        make_to_dict_source_code,
        "serialize",
        "to_dict",
        options=options,
        _field_options=_field_options,
        _ns=_ns,
        **kw,
    )


def to_dict(
    obj: DataclassInstance,
    *,
    options: _TotalDioOptions | DioOptions | None = None,
    **kw: tp.Unpack[DioOptions],
):
    """Convert a dataclass into a dictionary, recursively.

    Args:
        cls: The Dataclass instance to dump.
        options: `DioOptions` to use to customize the code generation process. These may also
            be provided via **kwargs. These propagate through to the fields of this dataclass
            type.

    Returns:
        A dictionary representation of the instance.
    """
    dumper = make_to_dict(type(obj), options=options, **kw)
    if dumper is CYCLE_DETECTED:
        msg = "Could not generate a serializer due to a unresolved reference cycle."
        raise RuntimeError(msg)
    return dumper(obj)
