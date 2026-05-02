import contextlib
import io
import json
from dataclasses import dataclass

import typing_extensions as tp

from .functional import make_from_dict, make_to_dict
from .functional.from_dict import _EXTRA_FIELD_ATTR_NAME
from .types import EFS, PathOrHandle


@contextlib.contextmanager
def _fname_or_fpointer(handle: PathOrHandle, mode="r", **kw):
    if isinstance(handle, io.IOBase):
        yield handle
        return

    with open(handle, mode=mode, **kw) as f:
        yield f


@dataclass
class IOMixin:
    __slots__ = _EXTRA_FIELD_ATTR_NAME

    def __post_init__(self):
        setattr(self, _EXTRA_FIELD_ATTR_NAME, {})

    @property
    def extra_fields(self):
        """Shallow copy of the extra fields stored in this instance from deserialization."""
        return dict(getattr(self, _EXTRA_FIELD_ATTR_NAME))

    @classmethod
    def from_json_file(
        cls: type[tp.Self],
        fname_or_handle: PathOrHandle,
        extra_field_strategy: EFS = EFS.IGNORE,
        load_kw: tp.Mapping[str, tp.Any] | None = None,
    ):
        """Initialize this class from a JSON file.

        Args:
            fname_or_handle: Path to a JSON file or a file-like object where mode="r" or "rb".
            extra_field_strategy: Strategy for handling unexpected fields in the JSON file.
            load_kw: Kwargs forwarded to `json.load(...)`, such as `cls`.
        """
        load_kw = load_kw or {}

        with _fname_or_fpointer(fname_or_handle, mode="rb") as fp:
            obj = json.load(fp, **load_kw)

        return cls.from_dict(obj, extra_field_strategy=extra_field_strategy)

    @classmethod
    def from_dict(
        cls: type[tp.Self], dikt: tp.Mapping[str, tp.Any], extra_field_strategy: EFS = EFS.IGNORE
    ) -> tp.Self:
        """Initialize this class from a dictionary."""

        # Cache based on desired extra field strategy
        meth_name = f"_dict_deserializer_method_ef_{extra_field_strategy.name}"
        method = getattr(cls, meth_name, None)
        if method is None:
            method = make_from_dict(cls, extra_field_strategy=extra_field_strategy)
            setattr(cls, meth_name, method)
        return method(dikt)

    def to_dict(self, skip_defaults: bool = False) -> dict[str, tp.Any]:
        """Serialize this class to a dictionary.

        Args:
            skip_defaults: Flag to skip serialization of default-valued entries in this instance.

        Returns:
            A dictionary representation of this class.
        """

        # Cache based on if we are skipping defaults.
        cls = self.__class__
        meth_name = f"_dict_serializer_method_skip_{skip_defaults}"
        method = getattr(cls, meth_name, None)
        if method is None:
            method = make_to_dict(cls, skip_defaults=skip_defaults)
            setattr(cls, meth_name, method)
        return method(self)

    def to_json_file(
        self,
        fname_or_handle: PathOrHandle,
        skip_defaults: bool = False,
        dump_kw: tp.Mapping[str, tp.Any] | None = None,
    ):
        """Serialize this instance to a JSON file.

        Args:
            fname_or_handle: Path to a file or a filepointer to write to. If a pointer is provided,
                it must support text-based writing.
            skip_defaults: Flag to skip serialization of default-valued entries in this instance.
            dump_kw: Kwargs to forward to `json.dump(...)`, such as `cls`.
        """
        obj = self.to_dict(skip_defaults=skip_defaults)

        dump_kw = dump_kw or {}
        with _fname_or_fpointer(fname_or_handle, mode="w", encoding="utf-8") as fp:
            json.dump(obj, fp, **dump_kw)
