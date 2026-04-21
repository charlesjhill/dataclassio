import typing_extensions as tp

from ..types import DataclassInstance
from .common import (
    SerializerData,
    field_get_default,
    field_has_default,
    get_field_expression,
    get_fields,
    indent,
)
from .from_dict import _EXTRA_FIELD_ATTR_NAME

_KNOWN_SERIALIZERS: dict[tuple[type, bool], tp.Callable[[DataclassInstance], dict]] = {}


def make_to_dict_source_code(
    cls: type[DataclassInstance],
    funcname: str = "",
    skip_defaults: bool = False,
    include_src_in_docstring: bool = True,
) -> tuple[str, dict[str, tp.Any]]:
    funcname = funcname or f"serialize_{cls.__name__}"
    lines = [
        f"def {funcname}(inst):",
        f'  """Serialize a {cls.__name__} instance into a dictionary."""',
        "  dikt = {",
    ]
    ns: dict[str, tp.Any] = {}

    # Start building up the output.
    # We are going to serialize objects. We also need to check if they
    #  have extra fields. We can assume we have fully-formed instances.
    # N.B., We initialize the dictionary with any extra fields. By construction, they
    #  are disjoint with the dataclass fields
    default_check_lines = []
    literal_lines = [f"**getattr(inst, {_EXTRA_FIELD_ATTR_NAME!r}, {{}}),"]
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
        if skip_defaults and field_has_default(f):
            # Add a hardcoded gate that checks if we have a default value. If so, don't
            #  add anything to the dict.
            field_default = field_get_default(f)
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

            strs = (
                f"if inst.{f.name} {comparator} {ns_key}:",
                f"  dikt[{f.name!r}] = {field_expr}",
            )
            default_check_lines.extend(strs)
        else:
            # Either this field has no default, or we are keeping all values. This easy.
            literal_lines.append(f"{f.name!r}: {field_expr},")

    lines.extend(indent(literal_lines, level=4))
    lines.append("  }")
    lines.extend(indent(default_check_lines, level=2))
    lines.append("  return dikt")

    if include_src_in_docstring:
        docstring_src = "\n".join(indent(lines[2:]))
        docstring = (
            f'  """Serialize a {cls.__name__} instance into a dictionary.\n\n{docstring_src}\n"""'
        )
        lines[1] = docstring

    f_src = "\n".join(lines)
    return f_src, ns


def make_to_dict(cls: type[DataclassInstance], skip_defaults: bool = False):
    if (f := _KNOWN_SERIALIZERS.get((cls, skip_defaults), None)) is not None:
        return f

    fname = f"serialize_{cls.__name__}"
    src, ns = make_to_dict_source_code(cls=cls, funcname=fname, skip_defaults=skip_defaults)
    exec(src, ns)
    return ns[fname]
