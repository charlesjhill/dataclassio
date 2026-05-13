import typing_extensions as tp

from ..config import DioOptions, _TotalDioOptions, get_composite_options, get_options_cache_key
from ..core import (
    SerializerData,
    TextLines,
    field_has_default,
    get_field_expression,
    get_fields,
    parse_default_expression,
)
from ..types import DataclassInstance
from ._shared import cache_source_code
from .from_dict import _EXTRA_FIELD_ATTR_NAME

_KNOWN_SERIALIZERS: dict[tuple[type, tp.Hashable], tp.Callable[[DataclassInstance], dict]] = {}
_SPACER = "  "


def make_to_dict_source_code(
    cls: type[DataclassInstance],
    funcname: str = "",
    options: _TotalDioOptions | DioOptions | None = None,  # call_options
) -> tuple[TextLines, dict[str, tp.Any]]:
    funcname = funcname or f"serialize_{cls.__name__}"
    ns: dict[str, tp.Any] = {}

    call_options = get_composite_options(call_options=options)

    # Start building up the output.
    # We are going to serialize objects. We also need to check if they
    #  have extra fields. We can assume we have fully-formed instances.
    # N.B., We initialize the dictionary with any extra fields. By construction, they
    #  are disjoint with the dataclass fields
    default_check_lines = TextLines(spacer=_SPACER)
    literal_lines = TextLines(spacer=_SPACER)
    for f in get_fields(cls):
        # Form the expression itself that gets the value.

        field_options = get_composite_options(
            field_options=f.metadata.get("dio"), call_options=options
        )

        field_expr = get_field_expression(
            f,
            direction="to_dict",
            serializer_data=SerializerData(
                registry=_KNOWN_SERIALIZERS,
                namespace=ns,
                maker_func=lambda t: make_to_dict(t, options=field_options),
                cache_key=get_options_cache_key(field_options, "to_dict"),
                options=field_options,
            ),
        )

        # Now on to the big leagues. so, invoked `field_expr` should get us the value to use
        #  for this field. Now, we just have to pack it up into a dictionary. We need to handle
        #  defaults, though. If we are skipping defaults, we need to include field defaults
        #  in the namespace so we can compare against them later.

        # We need an explicit check for `has_default` since `get_default` cannot distinguish between
        # "no default" and "default=None".
        if call_options["skip_defaults"] and field_has_default(f):
            # Add a hardcoded gate that checks if we have a default value. If so, don't
            #  add anything to the dict.
            default_expression = parse_default_expression(f, ns, precompute_factory=False)
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

    return lines, ns


def make_to_dict(
    cls: type[DataclassInstance],
    *,
    include_src_in_docstring: bool = True,
    options: _TotalDioOptions | DioOptions | None = None,
    **kw: tp.Unpack[DioOptions],
):
    """Make a to_dict serialization method for the given dataclass."""
    options = options or {}
    options.update(kw)

    opts = get_composite_options(call_options=options)
    key, str_key = get_options_cache_key(opts, "to_dict")

    if (f := _KNOWN_SERIALIZERS.get((cls, key), None)) is not None:
        return f

    func_name = f"serialize_{cls.__name__}{str_key}"
    file_name = f"dataclassio/generated/{func_name}{str_key}.py"
    src, ns = make_to_dict_source_code(cls=cls, funcname=func_name, options=options)

    code_obj = cache_source_code(src, file_name)
    exec(code_obj, ns)

    func = ns[func_name]
    if include_src_in_docstring:
        func.__doc__ += f"\n\n{src[2:]!s}\n"

    return func
