import contextlib
import io
import json
import types
from dataclasses import dataclass
from pathlib import Path

import typing_extensions as tp

from . import functional as diof
from .config2 import CallOptions
from .constants import _EXTRA_FIELD_ATTR_NAME
from .types import PathOrHandle


@contextlib.contextmanager
def _fname_or_fpointer(handle: PathOrHandle, mode="r", **kw):
    if isinstance(handle, io.IOBase):
        yield handle
        return

    with Path(handle).open(mode=mode, **kw) as f:
        yield f


@dataclass
class IOMixin:
    __slots__ = _EXTRA_FIELD_ATTR_NAME

    def __post_init__(self):
        setattr(self, _EXTRA_FIELD_ATTR_NAME, {})

    @property
    def extra_fields(self):
        """Readonly view of the extra fields stored in this instance from deserialization."""
        d = getattr(self, _EXTRA_FIELD_ATTR_NAME, {})
        return types.MappingProxyType(d)

    # IO methods

    @classmethod
    def from_json_file(
        cls: type[tp.Self],
        fname_or_handle: PathOrHandle,
        *,
        load_kw: tp.Mapping[str, tp.Any] | None = None,
        options: CallOptions | None = None,
        **kw: tp.Unpack[CallOptions],
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
        options: CallOptions | None = None,
        **kw: tp.Unpack[CallOptions],
    ) -> tp.Self:
        """Initialize this class from a dictionary."""
        return diof.from_dict(cls, dikt, options=options, **kw)

    def to_dict(
        self,
        *,
        options: CallOptions | None = None,
        **kw: tp.Unpack[CallOptions],
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
        options: CallOptions | None = None,
        **kw: tp.Unpack[CallOptions],
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

    # Hooks
    def __pre_to_dict__(self) -> None:
        """Hook invoked before serialization to a dictionary.

        Called on the instance prior to any field being read for ``to_dict``.
        Use this to normalize, validate, or otherwise mutate ``self`` in place
        so that the serialized output reflects the adjustments. To prevent serialization,
        raise any exception.

        The return value is ignored; this hook exists purely for its side effects on ``self``.
        """
        return

    def __post_to_dict__(self, dikt: dict) -> dict:
        """Hook invoked after serialization to a dict.

        Called with the produced dictionary representation of ``self`` as its only argument.
        This hook should return the desired dictionary to be returned from ``to_dict``, and that
        may be the input argument. You may mute the input dictionary or return a new/replacement
        dictionary to be used.

        Args:
            dikt: The dict produced by the generated ``to_dict`` method.

        Returns:
            The dictionary to return from ``to_dict``.
        """
        return dikt

    @classmethod
    def __pre_from_dict__(cls, dikt: dict) -> dict:
        """Hook invoked before deserialization from a dict.

        Called with the raw input dict before any field is read for
        ``from_dict``. You may mutate ``dikt``,
        or return a new/replacement dict to be used as the source for
        deserialization. Useful for migrating legacy objects, renaming keys,
        or filling in defaults.

        Args:
            dikt: The input dict passed to ``from_dict``.

        Returns:
            The dict to deserialize from.
        """
        return dikt

    def __post_from_dict__(self, dikt: dict) -> None:
        """Hook invoked after deserialization from a dict.

        Called on the newly constructed instance after all fields have been
        populated from ``dikt``. Use this to perform validation, derive
        computed attributes, or otherwise finalize ``self`` in place.

        Args:
            dikt: The dict that was used to construct ``self`` (including any processing from
                ``__pre_from_dict``, if implemented).
        """
        return
