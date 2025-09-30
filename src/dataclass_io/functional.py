from dataclasses import MISSING, Field, fields
from enum import Enum, auto

import typing_extensions as tp


class ExtraFieldStrategy(Enum):
    STRICT = auto()
    EXCLUDE = auto()
    CAPTURE = auto()


EFS = ExtraFieldStrategy


def _get_fields(cls: type):
    try:
        return fields(cls)
    except TypeError:
        pass

    msg = f"Unsupported type: {cls}. Currently, just `dataclasses.dataclass` is supported."
    raise ValueError(msg)


def _has_default(f: Field):
    return (f.default is not MISSING) or (f.default_factory is not MISSING)


def make_from_dict_source_code(
    cls: type,
    fname: str = "",
    extra_field_strategy=EFS.EXCLUDE,
    include_src_in_docstring: bool = True,
) -> tuple[str, dict[str, tp.Any]]:
    """Generate the source code and necessary namespace for a from_dict deserialization method."""
    fname = fname or f"deserialize_{cls.__name__}"
    lines = [f"def {fname}(cls, dikt):"]
    lines.append("  if not dikt: return cls()")

    arg_parts = []  # segments that arguments to the final cls(...) call.
    kw_lines = []  # Any lines that are added to accomodate optional arguments
    fields = _get_fields(cls)
    for f in fields:
        if _has_default(f):
            # a little trickier. We want to add to kw if and only if it exists in the dikt
            kw_lines.append(f"  if {f.name!r} in dikt:")
            kw_lines.append(f"    kw[{f.name!r}] = dikt[{f.name!r}]")
        else:
            lines.append(f"  if {f.name!r} not in dikt:")
            lines.append(
                f"    raise KeyError('\"{f.name}\" is a required value, but was missing from dikt.')"
            )
            arg_parts.append(f"{f.name}=dikt[{f.name!r}]")

    if kw_lines:
        arg_parts.append("**kw")
        lines.append("  kw = {}")
        lines.extend(kw_lines)
        del kw_lines

    arg_str = ", ".join(arg_parts)
    lines.append(f"  inst = cls({arg_str})")
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
    return f_src, {}


def make_from_dict(cls: type, extra_field_strategy: EFS = EFS.EXCLUDE):
    """Make a from_dict deserialization method for the given dataclass."""
    fname = f"deserialize_{cls.__name__}"
    src, ns = make_from_dict_source_code(
        cls, fname=fname, extra_field_strategy=extra_field_strategy
    )
    exec(src, ns)
    return ns[fname]


def handle_extra_fields(
    fields: tp.Iterable[Field],
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
        lines.extend(
            (
                "  if extra_kw:",
                "    msg = ('Extra fields are strictly prohibited, but the the input dictionary had'",
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
