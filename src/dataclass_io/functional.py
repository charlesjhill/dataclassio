import dataclasses as dcs
import logging
import types
from enum import Enum, auto

import typing_extensions as tp

_logger = logging.getLogger("dataclass_io")


class ExtraFieldStrategy(Enum):
    STRICT = auto()
    EXCLUDE = auto()
    CAPTURE = auto()


class DataclassInstance(tp.Protocol):
    __dataclass_fields__: tp.ClassVar


EFS = ExtraFieldStrategy


def _get_fields(cls: type):
    try:
        return dcs.fields(cls)
    except TypeError:
        pass

    msg = f"Unsupported type: {cls}. Currently, just `dataclasses.dataclass` is supported."
    raise ValueError(msg)


def _has_default(f: dcs.Field):
    return (f.default is not dcs.MISSING) or (f.default_factory is not dcs.MISSING)


def _is_plain_optional(t: type):
    return (
        tp.get_origin(t) is tp.Union
        and types.NoneType in (args := tp.get_args(t))
        and len(args) == 2
    )


def _get_dataclass_from_field_type(f: dcs.Field) -> tp.Optional[type[DataclassInstance]]:
    # the field type is f: Dataclass or f: Optional[Dataclass] if
    # the type is directly a dataclass OR has the form Union[Dataclass, NoneType]
    t = f.type

    if isinstance(t, str):
        _logger.warning("Got str for the type of %s", f.name)
        return None

    if dcs.is_dataclass(t):
        return t

    # Check for Optional[Dataclass]
    origin = tp.get_origin(t)
    args = tp.get_args(t)

    if isinstance(origin, str) or any(isinstance(a, str) for a in args):
        _logger.warning("Got str in origin/args for the field %s", f.name)

    if _is_plain_optional(t):
        # Optional[X]
        if dcs.is_dataclass(args[0]):
            return args[0]
        else:
            return None

    # Check for list[Dataclass]
    if origin is list and len(args) == 1 and dcs.is_dataclass(args[0]):
        return args[0]

    # Unsupported for now. Do not parse
    return None


def _get_field_expression(f: dcs.Field, field_converter_name: str = ""):
    if field_converter_name:
        field_container_type = tp.get_origin(f.type)
        if field_container_type is None or _is_plain_optional(f.type):
            # Ez.
            return f"{field_converter_name}(dikt[{f.name!r}])"

        if field_container_type is list:
            return f"[{field_converter_name}(d) for d in dikt[{f.name!r}]]"

        if field_container_type is dict:
            msg = f"dictionaries with field converters are not yet supported! field={f}."
            raise NotImplementedError(msg)

        # It is not list, dict, none or OPTIONAL[...]
        msg = f"Unsupported field_container_type={field_container_type} for field={f}."
        raise NotImplementedError(msg)

    # no field_converter. This is simple.
    return f"dikt[{f.name!r}]"


def make_from_dict_source_code(
    cls: type,
    fname: str = "",
    extra_field_strategy=EFS.EXCLUDE,
    include_src_in_docstring: bool = True,
) -> tuple[str, dict[str, tp.Any]]:
    """Generate the source code and necessary namespace for a from_dict deserialization method."""
    fname = fname or f"deserialize_{cls.__name__}"
    lines = [
        f"def {fname}(cls, dikt):",
        "  if not dikt: return cls()",
        "  kw = {}",
    ]
    ns = {}

    fields = _get_fields(cls)
    for f in fields:
        # Check if this field is itself a dataclass.
        parsed_annotation = _get_dataclass_from_field_type(f)
        field_is_dataclass = parsed_annotation is not None
        field_parser_name = ""

        if field_is_dataclass:
            if hasattr(parsed_annotation, "from_dict"):
                # ez.
                f_parser = parsed_annotation.from_dict
            else:
                cfg_obj = getattr(parsed_annotation, "Config", None)
                strategy = getattr(cfg_obj, "extra_key_strategy", extra_field_strategy)
                f_parser = make_from_dict(parsed_annotation, strategy)
            field_parser_name = f"deserialize_{cls.__name__}_{f.name}"
            ns[field_parser_name] = f_parser

        field_expr = _get_field_expression(f, field_parser_name)

        if _has_default(f):
            # a little trickier. We want to add to kw if and only if it exists in the dikt
            lines.extend(
                [
                    f"  if {f.name!r} in dikt:",
                    f"    kw[{f.name!r}] = {field_expr}",
                ]
            )
        else:
            err_msg = f"{f.name!r} is a required attribute for {cls.__name__}, but was missing from {{dikt=}}."
            lines.extend(
                [
                    "  try:",
                    f"    kw[{f.name!r}] = {field_expr}",
                    "  except KeyError as exc:",
                    f"    raise KeyError(f{err_msg!r}) from exc",
                ]
            )

    lines.append("  inst = cls(**kw)")
    lines.extend(handle_extra_fields(fields, extra_field_strategy))
    lines.append("  return inst")

    # Generate a docstring
    if include_src_in_docstring:
        docstring_src = "\n".join(("  " + L) for L in lines)
        docstring = f'  """Deserialize a {cls.__name__} instance from a dictionary.\n\n{docstring_src}\n  """'
    else:
        docstring = f'  """Deserialize a {cls.__name__} instance from a dictionary."""'

    lines.insert(1, docstring)
    f_src = "\n".join(lines)
    return f_src, ns


def make_from_dict(cls: type, extra_field_strategy: EFS = EFS.EXCLUDE):
    """Make a from_dict deserialization method for the given dataclass."""
    fname = f"deserialize_{cls.__name__}"
    src, ns = make_from_dict_source_code(
        cls, fname=fname, extra_field_strategy=extra_field_strategy
    )
    exec(src, ns)
    return ns[fname]


def handle_extra_fields(
    fields: tp.Iterable[dcs.Field],
    strategy: EFS,
    *,
    dict_name: str = "dikt",
    instance_name: str = "inst",
    attribute_name: str = "_extra_fields",
) -> list[str]:
    if strategy == EFS.EXCLUDE:
        # Excluding extra fields is the easiest thing known to man.
        return []

    field_names = tuple(f.name for f in fields)
    lines = [f"  extra_kw = {{k: v for k, v in {dict_name}.items() if k not in {field_names!r}}}"]
    if strategy == EFS.STRICT:
        err_msg = f"Extra fields are strictly prohibited for {{{instance_name}=}}"
        lines.extend(
            (
                "  if extra_kw:",
                f"    msg = (f'{err_msg}, but the the input dictionary had'",
                "           f' the following extra fields: {list(extra_kw)}')",
                "    raise ValueError(msg)",
            )
        )
    elif strategy == EFS.CAPTURE:
        lines.append(f"  {instance_name}.{attribute_name} = extra_kw")
    else:
        msg = f"Unexpected {strategy=}. Must be an ExtraFieldStrategy enumeration."
        raise ValueError(msg)

    return lines
