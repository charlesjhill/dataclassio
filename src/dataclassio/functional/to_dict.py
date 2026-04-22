import typing_extensions as tp

from ..core import (
    SerializerData,
    TextLines,
    get_field_default,
    get_field_expression,
    get_fields,
)
from ..types import NO_DEFAULT, DataclassInstance
from .from_dict import _EXTRA_FIELD_ATTR_NAME

_KNOWN_SERIALIZERS: dict[tuple[type, bool], tp.Callable[[DataclassInstance], dict]] = {}
_SPACER = "  "


def make_to_dict_source_code(
    cls: type[DataclassInstance],
    funcname: str = "",
    skip_defaults: bool = False,
) -> tuple[TextLines, dict[str, tp.Any]]:
    funcname = funcname or f"serialize_{cls.__name__}"
    ns: dict[str, tp.Any] = {}

    # Start building up the output.
    # We are going to serialize objects. We also need to check if they
    #  have extra fields. We can assume we have fully-formed instances.
    # N.B., We initialize the dictionary with any extra fields. By construction, they
    #  are disjoint with the dataclass fields
    default_check_lines = TextLines(spacer=_SPACER)
    literal_lines = TextLines(spacer=_SPACER)
    for f in get_fields(cls):
        # Form the expression itself that gets the value.
        field_expr = get_field_expression(
            f,
            direction="to_dict",
            serializer_data=SerializerData(
                registry=_KNOWN_SERIALIZERS,
                namespace=ns,
                maker_func=lambda t: make_to_dict(t, skip_defaults=skip_defaults),
                cache_args=(skip_defaults,),
            ),
        )

        # Now on to the big leagues. so, invoked `field_expr` should get us the value to use
        #  for this field. Now, we just have to pack it up into a dictionary. We need to handle
        #  defaults, though. If we are skipping defaults, we need to include field defaults
        #  in the namespace so we can compare against them later.

        # We need an explicit check for `has_default` since `get_default` cannot distinguish between
        # "no default" and "default=None".
        if skip_defaults and (field_default := get_field_default(f)) is not NO_DEFAULT:
            # Add a hardcoded gate that checks if we have a default value. If so, don't
            #  add anything to the dict.
            comparator = "is not" if field_default is None else "!="

            # TODO: Consider adding handler for boolean cases?
            if field_default is None or isinstance(field_default, (int, float, str)):
                ns_key = repr(field_default)
            elif field_default == []:
                ns_key = "[]"
            elif field_default == {}:
                ns_key = "{}"
            else:
                ns_key = f"{f.name}_default"
                ns[ns_key] = field_default

            with default_check_lines.indent(f"if inst.{f.name} {comparator} {ns_key}:"):
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
    skip_defaults: bool = False,
    include_src_in_docstring: bool = True,
):
    if (f := _KNOWN_SERIALIZERS.get((cls, skip_defaults), None)) is not None:
        return f

    fname = f"serialize_{cls.__name__}"
    src, ns = make_to_dict_source_code(cls=cls, funcname=fname, skip_defaults=skip_defaults)
    exec(src.export(), ns)
    func = ns[fname]
    if include_src_in_docstring:
        func.__doc__ += f"\n\n{src[2:]!s}\n"
    return func
