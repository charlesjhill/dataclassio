import uuid

import typing_extensions as tp

from dataclassio.sentinels import NO_VALUE, NoValueOr

__all__ = (
    "make_variable_name",
    "set_variable_in_ns",
)


def make_variable_name(
    base_name: str,
    prefix: str = "",
    ns: tp.Container[str] | None = None,
):
    """Generate a variable name that avoids shadowing any existing variable names."""
    var_name = f"{prefix}{base_name}"

    if not ns:
        return var_name

    while var_name in ns:
        random_chars = uuid.uuid4().hex[:2]
        var_name = f"{var_name}_{random_chars}"

    return var_name


def set_variable_in_ns(
    name: str,
    value: NoValueOr[tp.Any],
    *,
    ns: tp.MutableMapping[str, tp.Any],
) -> str:
    """Create a variable in a namespace.

    If `name` is already in the namespace, it will be assigned a new name if the desired
    value differs from the existing value.
    """
    existing_value = ns.get(name, NO_VALUE)
    if (
        existing_value is not NO_VALUE  # name was taken in the namespace already
        and value == existing_value  # The new value is the same as the existing one
    ):
        # no need to populate a new slot. Just use the current one.
        return name

    assigned_fname = make_variable_name(name, ns=ns)
    if value is not NO_VALUE:
        ns[assigned_fname] = value

    return assigned_fname
