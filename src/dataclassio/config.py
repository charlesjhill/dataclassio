from collections import ChainMap

import typing_extensions as tp

from .types import EFS

__all__ = (
    "DioOptions",
    "FieldOpts",
    "get_composite_options",
    "get_options_cache_key",
    "NoValue",
)

T = tp.TypeVar("T", bound=type)


class _NoValue:
    def __repr__(self) -> str:
        return "<NoValueProvided>"

    def __str__(self) -> str:
        return "NoValueProvided"


NoValue: tp.Final = _NoValue()


class DioOptions(tp.TypedDict, total=False):
    discriminator: str | _NoValue
    extra_field_strategy: EFS
    skip_defaults: bool


class _TotalDioOptions(DioOptions):
    discriminator: str | _NoValue
    extra_field_strategy: EFS
    skip_defaults: bool


def FieldOpts(**kw: tp.Unpack[DioOptions]):
    """Make DioOptions for `field(metadata=...)`."""
    return {"dio": DioOptions(**kw)}


DIO_DEFAULT_OPTIONS = _TotalDioOptions(
    discriminator=NoValue, extra_field_strategy=EFS.IGNORE, skip_defaults=False
)


def get_composite_options(
    field_options: _TotalDioOptions | DioOptions | None = None,
    call_options: _TotalDioOptions | DioOptions | None = None,
    type_options: _TotalDioOptions | DioOptions | None = None,
) -> _TotalDioOptions:
    """Provide a config object that merges DioOptions at various precedence levels.

    The options are merged with the following predence level:

        # Top-Priority
        1. Field-level options (does not cascade)
        2. Call-level options (cascades)
        3. Type-level options (does not cascade)
        4. Global default options
        # Lowest-Priority

    Notes:
        The given priorities are based on conventions from other serialization libraries, like `mashumaro` or
        `pydantic`.

    Returns:
        A MutableMapping with the DioOptions
    """
    return tp.cast(
        _TotalDioOptions,
        ChainMap(
            field_options or {},
            call_options or {},
            type_options or {},
            DIO_DEFAULT_OPTIONS,
        ),
    )


_FROM_KEYS = frozenset(("discriminator", "extra_field_strategy"))
_TO_KEYS = frozenset(("discriminator", "skip_defaults"))


def _build_string(opts: DioOptions):
    str_data = []

    if "discriminator" in opts and opts["discriminator"] != DIO_DEFAULT_OPTIONS["discriminator"]:
        str_data.append(f"discriminator_{opts['discriminator']}")

    if (
        "extra_field_strategy" in opts
        and opts["extra_field_strategy"] != DIO_DEFAULT_OPTIONS["extra_field_strategy"]
    ):
        str_data.append(f"efs_{opts['extra_field_strategy'].value}")

    if "skip_defaults" in opts and opts["skip_defaults"] != DIO_DEFAULT_OPTIONS["skip_defaults"]:
        str_data.append(f"skip_defaults_{opts['skip_defaults']!s}")

    postfix = "__".join(str_data)
    if postfix:
        postfix = f"_{postfix}"
    return postfix


def get_options_cache_key(
    options: DioOptions | _TotalDioOptions, direction: tp.Literal["from_dict", "to_dict"]
) -> tuple[tp.Hashable, str]:
    relevant_keys = _FROM_KEYS if direction == "from_dict" else _TO_KEYS
    filtered_data = tp.cast(DioOptions, {k: v for k, v in options.items() if k in relevant_keys})

    data = tuple(sorted(filtered_data.items()))
    return data, _build_string(filtered_data)
