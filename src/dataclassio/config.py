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
    skip_if_default: bool
    include_src_in_docstring: bool


class _TotalDioOptions(DioOptions):
    discriminator: str | _NoValue
    extra_field_strategy: EFS
    skip_if_default: bool
    include_src_in_docstring: bool


def FieldOpts(**kw: tp.Unpack[DioOptions]):
    """Make DioOptions for `field(metadata=...)`."""
    return {"dio": DioOptions(**kw)}


DIO_DEFAULT_OPTIONS = _TotalDioOptions(
    discriminator=NoValue,
    extra_field_strategy=EFS.IGNORE,
    skip_if_default=False,
    include_src_in_docstring=False,
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
        dict(
            ChainMap(
                field_options or {},
                call_options or {},
                type_options or {},
                DIO_DEFAULT_OPTIONS,
            )
        ),
    )


_BOTH_KEYS = frozenset(("discriminator", "include_src_in_docstring"))
_FROM_KEYS = _BOTH_KEYS.union(("extra_field_strategy",))
_TO_KEYS = _BOTH_KEYS.union(("skip_if_default",))
# _TO_KEYS = _BOTH_KEYS
_MISSING = object()


def _build_string(opts: DioOptions):
    str_data = []

    bundles: list[tuple[str, tp.Callable[[tp.Any], str]]] = [
        ("discriminator", lambda x: f"discriminator_{x}"),
        ("extra_field_strategy", lambda x: f"efs_{x.value}"),
        ("skip_if_default", lambda _: "skip_if_default"),
        ("include_src_in_docstring", lambda _: "incl_src"),
    ]

    for field_name, str_gen in bundles:
        v = opts.get(field_name, _MISSING)
        if v is not _MISSING and v != DIO_DEFAULT_OPTIONS[field_name]:
            str_data.append(str_gen(v))

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
