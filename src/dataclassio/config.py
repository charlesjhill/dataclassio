import typing_extensions as tp
from collections import ChainMap

from .types import EFS


__all__ = ("DioOptions", "NoValue", "get_composite_options")


class _NoValue:
    def __repr__(self) -> str:
        return "<NoValueProvided>"


NoValue: tp.Final = _NoValue()


class DioOptions(tp.TypedDict, total=False):
    discriminator: str | _NoValue
    """Key to use for discriminating unions.

    E.g., if each member of the Union has a "type: str" field, then if `discriminator: "type"`, DIO will parse the
    `type` member of each object to decide what call to use.
    """
    extra_field_strategy: EFS
    """Method for handling the presence of extra fields in an object."""


DIO_DEFAULT_OPTIONS = DioOptions(discriminator=NoValue, extra_field_strategy=EFS.IGNORE)


def get_composite_options(
    field_options: DioOptions | None = None,
    call_options: DioOptions | None = None,
    type_options: DioOptions | None = None,
) -> DioOptions:
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
        DioOptions,
        ChainMap(
            field_options or {},
            call_options or {},
            type_options or {},
            DIO_DEFAULT_OPTIONS,
        ),
    )
