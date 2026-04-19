"""Functional interface to the DataclassIO library.

The main entrypoint is `make_from_dict` or `make_from_dict_source_code` for deserialization,
and `make_to_dict` and `make_to_dict_source_code` for serialization.
"""

__all__ = (
    "make_from_dict",
    "make_from_dict_source_code",
    "make_to_dict",
    "make_to_dict_source_code",
)

from .from_dict import make_from_dict, make_from_dict_source_code
from .to_dict import make_to_dict, make_to_dict_source_code
