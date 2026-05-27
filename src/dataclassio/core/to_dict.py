from functools import partial

import typing_extensions as tp

from dataclassio.config2 import ResolvedConfig
from dataclassio.constants import (
    _EXTRA_FIELD_ATTR_NAME,
    _POST_TO_DICT_HOOK,
    _PRE_TO_DICT_HOOK,
    _SPACER,
    NO_VALUE,
    CycleOr,
)
from dataclassio.types import DataclassInstance, TDataclass, TNamespace

from ._shared_codegen import maker_core, overrides_hook
from .expression_builder import SerializerData, get_field_expression
from .field_methods import field_has_default, get_fields, parse_default_expression
from .lines import TextLines

_KNOWN_SERIALIZERS: dict[tuple[type, tp.Hashable], tp.Callable[[DataclassInstance], dict]] = {}


def make_to_dict_source_code(
    cls: type[DataclassInstance],
    *,
    frame_config: ResolvedConfig,
    _ns: TNamespace | None = None,
) -> TextLines:
    from dataclassio.io_mixin import IOMixin

    if _ns is None:
        _ns = {}

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
        field_config = frame_config.build_field_config(field_opts)
        field_config_dict = field_config.as_dict()

        if not field_config_dict["dump"]:
            continue

        child_inherited = field_config.project_for_child()
        cache_key = child_inherited.legacy_cache_key

        field_expr = get_field_expression(
            f,
            serializer_data=SerializerData(
                registry=_KNOWN_SERIALIZERS,
                namespace=_ns,
                maker_func=partial(make_to_dict, inherited_config=child_inherited, _ns=_ns),
                cache_key=cache_key,
                options=field_config_dict,
                func_prefix="serialize",
            ),
        )

        # Decide if we should try to skip this field if it has a default value.
        # There are two control knobs at play here:
        #  - skip_if_default  (FIELD-LOCAL; NoValueOr[bool])
        #  - skip_defaults    (CALL-DEEP, TYPE-LOCAL, FIELD-DEEP_ONCE; NoValueOr[bool])
        # If skip_if_default is in the field configuration, it is the highest precedence.
        # Otherwise, we insepct skip_defaults in the FRAME configuration. This is specifically
        #  becuase we want to ignore the skip_defaults opt set on this field directly since
        #  field(skip_defaults=...) is meant for the next frame, not this one.

        skip_this_field: bool = False
        if (s := field_config_dict["skip_if_default"]) is not NO_VALUE or (
            s := frame_config["skip_defaults"]
        ) is not NO_VALUE:
            skip_this_field = s

        if skip_this_field and field_has_default(f):
            default_expression = parse_default_expression(f, _ns, precompute_factory=False)
            assert isinstance(default_expression, str)
            comparator = "is not" if default_expression == "None" else "!="

            with default_check_lines.indent(
                f"if inst.{f.name} {comparator} {default_expression}:"
            ):
                default_check_lines.append(f"dikt[{f.name!r}] = {field_expr}")
        else:
            # Either this field has no default, or we are keeping all values. This easy.
            literal_lines.append(f"{f.name!r}: {field_expr},")

    if frame_config["dump_extras"]:
        # Handle the extra fields. If there are no "default checking" lines, we can pack this into
        #  the bottom of the literals. If we do check some fields for their default value,
        #  we include the extra field population right before export to try keeping the "real"
        #  fields in order in the resulting dictionary.
        if issubclass(cls, IOMixin):
            # Subclasses of IOMixin _always_ define an _EXTRA_FIELD_ATTR_NAME,
            #  so we don't need to use the get attr with a string literal.
            extras_expr = f"inst.{_EXTRA_FIELD_ATTR_NAME!s}"
            has_extras_attr = True
        else:
            # Otherwise, the object may not define the attribute, so use
            extras_expr = f"getattr(inst, {_EXTRA_FIELD_ATTR_NAME!r}, {{}})"
            has_extras_attr = False

        if not default_check_lines:
            # If there are no default value checks, we can bake this directly into the dict literal
            literal_lines.append(f"**{extras_expr},")
        elif has_extras_attr:
            # Need to call `dikt.update`. We have an extras_attr.
            default_check_lines.append(f"dikt.update({extras_expr})")
        else:
            # Need to call `dikt.update`. We may or may not have an extras_attr.
            #  It is faster to use getattr(..., None)
            default_check_lines.append(f"_extras = {extras_expr.format('None')}")
            with default_check_lines.indent("if _extras is not None:"):
                default_check_lines.append("dikt.update(_extras)")

    lines = TextLines(spacer=_SPACER)
    funcname = frame_config.get_func_name(cls, "serialize")

    if frame_config["skip_hooks"]:
        insert_pre = False
        insert_post = False
    else:
        insert_pre = overrides_hook(cls, _PRE_TO_DICT_HOOK)
        insert_post = overrides_hook(cls, _POST_TO_DICT_HOOK)

    with lines.indent(f"def {funcname}(inst):"):
        lines.append(f'"""Serialize a {cls.__name__} instance into a dictionary."""')
        if insert_pre:
            lines.append(f"inst.{_PRE_TO_DICT_HOOK}()")

        with lines.indent("dikt = {"):
            lines.extend(literal_lines)
        lines.append("}")
        lines.extend(default_check_lines)
        if insert_post:
            lines.append(f"dikt = inst.{_POST_TO_DICT_HOOK}(dikt)")
        lines.append("return dikt")
    return lines


def make_to_dict(
    cls: type[TDataclass],
    *,
    inherited_config: ResolvedConfig,
    _ns: TNamespace | None = None,
) -> CycleOr[tp.Callable[[TDataclass], dict[str, tp.Any]]]:
    """Make a to_dict serialization method for the given dataclass.

    Args:
        cls: The Dataclass type to generate the serializer for.
    """
    return maker_core(
        cls,
        _KNOWN_SERIALIZERS,
        make_to_dict_source_code,
        "serialize",
        inherited_config=inherited_config,
        _ns=_ns,
    )
