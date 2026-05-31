"""Functional interface to the library, as an alternative to using IOMixin"""

import typing_extensions as tp

from dataclassio.core._shared_codegen import validate_type_hints

from .config2 import CallOptions, ResolvedConfig
from .constants import CYCLE_DETECTED
from .core import from_dict as load_core
from .core import to_dict as dump_core
from .types import DataclassInstance, TDataclass

__all__ = (
    "from_dict",
    "make_from_dict",
    "print_from_dict_source_code",
    "to_dict",
    "make_to_dict",
    "print_to_dict_source_code",
)


def from_dict(
    cls: type[TDataclass],
    dikt: tp.Mapping[str, tp.Any],
    *,
    options: CallOptions | None = None,
    **kw: tp.Unpack[CallOptions],
) -> TDataclass:
    """Load a dictionary into a Dataclass.

    Args:
        cls: The type of the dataclass to generate
        dikt: The mapping of data used to populate the dataclass.
        options: `CallOptions` to use to customize the code generation process. These may also
            be provided via **kwargs.

    Returns:
        A dataclass instance.
    """
    loader = make_from_dict(cls, options=options, **kw)
    return loader(dikt)


def make_from_dict(
    cls: type[TDataclass], *, options: CallOptions | None = None, **kw: tp.Unpack[CallOptions]
) -> tp.Callable[[tp.Mapping[str, tp.Any]], TDataclass]:
    opts = options or {}
    opts.update(kw)
    cfg = ResolvedConfig.from_call(opts)

    loader = load_core.make_from_dict(cls, inherited_config=cfg)
    if loader is CYCLE_DETECTED:
        msg = "Could not build deserializer due to reference cycle"
        raise RuntimeError(msg)
    return loader


def to_dict(
    obj: DataclassInstance,
    *,
    options: CallOptions | None = None,
    **kw: tp.Unpack[CallOptions],
):
    """Convert a dataclass into a dictionary, recursively.

    Args:
        cls: The Dataclass instance to dump.
        options: `CallOptions` to use to customize the code generation process. These may also
            be provided via **kwargs. These propagate through to the fields of this dataclass
            type.

    Returns:
        A dictionary representation of the instance.
    """
    dumper = make_to_dict(type(obj), options=options, **kw)
    return dumper(obj)


def make_to_dict(
    cls: type[TDataclass], *, options: CallOptions | None = None, **kw: tp.Unpack[CallOptions]
) -> tp.Callable[[TDataclass], dict[str, tp.Any]]:
    """Generate a function to dump a dataclass to a nested dictionary structure.

    Args:
        cls: The Dataclass instance to dump.
        options: `CallOptions` to use to customize the code generation process. These may also
            be provided via **kwargs. These propagate through to the fields of this dataclass
            type.

    Returns:
        A function which converts a Dataclass instance to a nested dictionary structure.
    """
    opts = options or {}
    opts.update(kw)
    cfg = ResolvedConfig.from_call(opts)
    dumper = dump_core.make_to_dict(cls, inherited_config=cfg)
    if dumper is CYCLE_DETECTED:
        msg = "Could not generate a serializer due to a unresolved reference cycle."
        raise RuntimeError(msg)
    return dumper


def print_to_dict_source_code(
    cls: type[DataclassInstance],
    *,
    options: CallOptions | None = None,
    **kw: tp.Unpack[CallOptions],
) -> dict:
    opts = options or {}
    opts.update(kw)
    cfg = ResolvedConfig.from_call(opts).build_frame_config(cls)

    ns = {}
    validate_type_hints(cls)
    src = dump_core.make_to_dict_source_code(cls, frame_config=cfg, _ns=ns)
    print(src)
    return ns


def print_from_dict_source_code(
    cls: type[DataclassInstance],
    *,
    options: CallOptions | None = None,
    **kw: tp.Unpack[CallOptions],
) -> dict:
    opts = options or {}
    opts.update(kw)
    cfg = ResolvedConfig.from_call(opts).build_frame_config(cls)

    ns = {}
    validate_type_hints(cls)
    src = load_core.make_from_dict_source_code(cls, frame_config=cfg, _ns=ns)
    print(src)
    return ns
