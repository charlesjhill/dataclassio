from dataclasses import MISSING, Field, fields

import typing_extensions as tp


def _get_fields(cls: type):
    try:
        return fields(cls)
    except TypeError:
        pass

    msg = f"Unsupported type: {cls}. Currently, just `dataclasses.dataclass` is supported."
    raise ValueError(msg)


def _has_default(f: Field):
    return (f.default is not MISSING) or (f.default_factory is not MISSING)


def make_from_dict_source_code(cls: type, fname: str = "") -> tuple[str, dict[str, tp.Any]]:
    """Generate the source code and necessary namespace for a from_dict deserialization method."""
    fname = fname or f"deserialize_{cls.__name__}"
    lines = [f"def {fname}(cls, dikt):"]
    lines.append("  if not dikt: return cls()")

    arg_parts = []
    kw_lines = []
    for f in _get_fields(cls):
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

    arg_str = ", ".join(arg_parts)
    lines.append(f"  return cls({arg_str})")

    # Generate a docstring
    docstring_src = "\n".join(("  " + L) for L in lines)

    docstring = (
        f'  """Deserialize a {cls.__name__} instance from a dictionary.\n\n{docstring_src}\n  """'
    )
    lines.insert(1, docstring)
    f_src = "\n".join(lines)
    return f_src, {}


def make_from_dict(cls: type):
    """Make a from_dict deserialization method for the given dataclass."""
    fname = f"deserialize_{cls.__name__}"
    src, ns = make_from_dict_source_code(cls, fname=fname)
    exec(src, ns)
    return ns[fname]
