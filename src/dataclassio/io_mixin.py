import contextlib
import io
import json
from dataclasses import dataclass

import typing_extensions as tp

from . import functional as diof
from .config import DioOptions
from .functional.from_dict import _EXTRA_FIELD_ATTR_NAME
from .types import PathOrHandle


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
        *,
        load_kw: tp.Mapping[str, tp.Any] | None = None,
        options: DioOptions | None = None,
        **kw: tp.Unpack[DioOptions],
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

        return cls.from_dict(obj, options=options, **kw)

    @classmethod
    def from_dict(
        cls: type[tp.Self],
        dikt: tp.Mapping[str, tp.Any],
        *,
        options: DioOptions | None = None,
        **kw: tp.Unpack[DioOptions],
    ) -> tp.Self:
        """Initialize this class from a dictionary."""
        return diof.from_dict(cls, dikt, options=options, **kw)

    def to_dict(
        self,
        *,
        options: DioOptions | None = None,
        **kw: tp.Unpack[DioOptions],
    ) -> dict[str, tp.Any]:
        """Serialize this class to a dictionary.

        Returns:
            A dictionary representation of this class.
        """
        return diof.to_dict(self, options=options, **kw)

    def to_json_file(
        self,
        fname_or_handle: PathOrHandle,
        *,
        dump_kw: tp.Mapping[str, tp.Any] | None = None,
        options: DioOptions | None = None,
        **kw: tp.Unpack[DioOptions],
    ):
        """Serialize this instance to a JSON file.

        Args:
            fname_or_handle: Path to a file or a filepointer to write to. If a pointer is provided,
                it must support text-based writing.
            dump_kw: Kwargs to forward to `json.dump(...)`, such as `cls`.
        """
        obj = self.to_dict(options=options, **kw)

        dump_kw = dump_kw or {}
        with _fname_or_fpointer(fname_or_handle, mode="w", encoding="utf-8") as fp:
            json.dump(obj, fp, **dump_kw)
