import bisect
import dataclasses as dcs
from enum import Enum, auto

import typing_extensions as tp

from .sentinels import NO_VALUE, NoValueOr
from .types import EFS

__all__ = (
    "CallOptions",
    "TypeOptions",
    "FieldOptions",
    "ResolvedConfig",
    "get_type_options",
)

## ----------------------------------------------------
## OptionSpecs
## ----------------------------------------------------


class Scope(Enum):
    """Option scopes. Defines where options may be set."""

    # Precedence rankings (lower is higher precedence)
    CALL = 3
    TYPE = 2
    FIELD = 1


class Propagation(Enum):
    """Propagation options."""

    LOCAL = auto()
    """Affects only the immediate codegen frame."""
    DEEP = auto()
    """Propagates into nested type codegen."""
    DEEP_ONCE = auto()
    """Propagates to immediate child only (field-deep semantics)"""
    # PARENT = auto()
    # """Propagates _up_ to parents which contain this type. Only valid for the TYPE scope."""


T = tp.TypeVar("T")


@dcs.dataclass(frozen=True)
class OptionSpec(tp.Generic[T]):
    name: str
    type_str: str
    default: T
    scopes: tp.Mapping[Scope, Propagation]
    to_str: tp.Callable[[T], str]


S = Scope
P = Propagation

EXTRA_FIELD_STRATEGY = OptionSpec(
    name="extra_field_strategy",
    type_str="EFS",
    default=EFS.IGNORE,
    scopes={S.CALL: P.DEEP, S.TYPE: P.LOCAL, S.FIELD: P.DEEP_ONCE},
    to_str=lambda x: f"efs_{x.value}",
)

DISCRIMINATOR = OptionSpec(
    name="discriminator",
    type_str="NoValueOr[str]",
    default=NO_VALUE,
    scopes={
        S.FIELD: P.LOCAL,
        # Conside r adding S.TYPE: P.LOCAL for default discriminators for a type.
    },
    to_str=lambda x: f"discriminator_{x}",
)

SKIP_IF_DEFAULT = OptionSpec(
    name="skip_if_default",
    type_str="NoValueOr[bool]",
    default=NO_VALUE,
    scopes={
        # S.TYPE: P.PARENT,
        S.FIELD: P.LOCAL,
    },
    to_str=lambda x: f"skip_if_default_{x}",
)

SKIP_DEFAULTS = OptionSpec(
    name="skip_defaults",
    type_str="NoValueOr[bool]",
    default=NO_VALUE,
    scopes={
        S.CALL: P.DEEP,
        S.TYPE: P.LOCAL,
        S.FIELD: P.DEEP_ONCE,
    },
    to_str=lambda x: f"skip_defaults_{x}",
)

INCLUDE_SRC_IN_DOCSTRING = OptionSpec(
    name="include_src_in_docstring",
    type_str="bool",
    default=False,
    scopes={S.CALL: P.DEEP},
    to_str=lambda _: "incl_src",
)

ALL_OPTIONS: tuple[OptionSpec, ...] = (
    EXTRA_FIELD_STRATEGY,
    DISCRIMINATOR,
    SKIP_IF_DEFAULT,
    SKIP_DEFAULTS,
    INCLUDE_SRC_IN_DOCSTRING,
)

REGISTRY: dict[str, OptionSpec] = {o.name: o for o in ALL_OPTIONS}

## ----------------------------------------------------
## User-facing APIs for Call/Type/Field Options
## ----------------------------------------------------

# See scripts/generate_option_typed_dicts.py to generate these from `ALL_OPTIONS`.


class CallOptions(tp.TypedDict, total=False):
    extra_field_strategy: EFS
    skip_defaults: NoValueOr[bool]
    include_src_in_docstring: bool


class TypeOptions(tp.TypedDict, total=False):
    extra_field_strategy: EFS
    skip_defaults: NoValueOr[bool]


class _FieldOptions(tp.TypedDict, total=False):
    extra_field_strategy: EFS
    discriminator: NoValueOr[str]
    skip_if_default: NoValueOr[bool]
    skip_defaults: NoValueOr[bool]


class DioOptions(tp.TypedDict, total=True):
    extra_field_strategy: EFS
    discriminator: NoValueOr[str]
    skip_if_default: NoValueOr[bool]
    skip_defaults: NoValueOr[bool]
    include_src_in_docstring: bool


def FieldOptions(**kw: tp.Unpack[_FieldOptions]):
    return {"dio": _FieldOptions(kw)}


## ----------------------------------------------------
## Field Management
## ----------------------------------------------------


@dcs.dataclass(frozen=True)
class ConfigEntry:
    """A single, resolved option value, tagged with its origin."""

    N_OBJECTS: tp.ClassVar[int] = 0

    name: str
    value: tp.Hashable
    scope: Scope
    propagation: Propagation

    # Flag if this entry arrived via a DEEP_ONCE hop and should be dropped
    #  on the next projection. While "consumed", it can participate in
    #  codegen of the current frame and continues to override CALL-sourced values.
    consumed: bool = False

    # Tiebreaker
    seq: int = dcs.field(init=False, default_factory=lambda: ConfigEntry.N_OBJECTS)

    def __post_init__(self):
        # TODO: Threadsafety
        ConfigEntry.N_OBJECTS += 1

    @property
    def precedence(self):
        # use -self.seq so that newer entries come first in sorted order.
        if self.consumed:
            return (0, -self.seq)
        return (self.scope.value, -self.seq)

    def cache_key(self) -> tp.Hashable:
        return (self.name, self.value, self.scope, self.consumed)


def _yield_entries(
    mapping: tp.Mapping[str, tp.Any] | None, source: Scope
) -> tp.Generator[ConfigEntry]:
    if not mapping:
        return

    for opt_name, opt_value in mapping.items():
        spec = REGISTRY.get(opt_name)
        if spec is None:
            msg = f"Unknown option: {opt_name!r}"
            raise ValueError(spec)
        if source not in spec.scopes:
            msg = (
                f"Option {opt_name!r} cannot be set at scope {source.name}; "
                f"allowed scopes: {[s.name for s in spec.scopes]}"
            )
            raise ValueError(msg)

        yield ConfigEntry(
            name=opt_name,
            value=opt_value,
            scope=source,
            propagation=spec.scopes[source],
        )


class ResolvedConfig:
    """A fully-resolved view of options for a single codegen frame."""

    __slots__ = ("_entries",)

    def __init__(self, entries: tp.Mapping[str, tp.Sequence[ConfigEntry]] | None = None) -> None:
        # _entries is a mapping of option names to a list of values provided for that
        #  option, sorted by precedence order (high precendence first).
        self._entries: tp.Mapping[str, tp.Sequence[ConfigEntry]] = entries or {}

    @classmethod
    def from_call(cls, call_options: CallOptions | None = None) -> tp.Self:
        inst = cls()

        entries = _yield_entries(call_options, Scope.CALL)
        return inst._with_overlay(entries)

    def __getitem__(self, key: str) -> tp.Any:
        entry = self._entries.get(key)
        if entry is None:
            return REGISTRY[key].default
        return entry[0].value

    def __contains__(self, name: str) -> bool:
        return name in self._entries

    def as_dict(self):
        return DioOptions(
            extra_field_strategy=self["extra_field_strategy"],
            discriminator=self["discriminator"],
            skip_defaults=self["skip_defaults"],
            skip_if_default=self["skip_if_default"],
            include_src_in_docstring=self["include_src_in_docstring"],
        )

    def cache_key(self):
        return tuple(
            (name, tuple(e.cache_key() for e in bucket))
            for name, bucket in sorted(self._entries.items())
        )

    def func_postfix(self, key: NoValueOr[tuple] = NO_VALUE) -> str:
        if key is NO_VALUE:
            key = self.cache_key()

        if not key:
            return ""

        digest = str(abs(hash(key)))[:6]
        return f"_{digest!s}"

    def get_func_name(self, kls: type, direction: tp.Literal["deserialize", "serialize"]):
        return f"{direction}_{kls.__name__}{self.func_postfix()}"

    @property
    def legacy_cache_key(self) -> tuple[tp.Hashable, str]:
        k = self.cache_key()
        return k, self.func_postfix(k)

    def _with_overlay(self: tp.Self, new_entries: tp.Iterable[ConfigEntry]) -> tp.Self:
        """Merge new entries into the config"""
        kls = type(self)

        # Functionally a deep copy.
        out = {k: list(v) for k, v in self._entries.items()}
        for new_entry in new_entries:
            bucket = out.setdefault(new_entry.name, [])
            bisect.insort(bucket, new_entry, key=lambda x: x.precedence)

        return kls({k: tuple(v) for k, v in out.items()})

    def project_for_child(self) -> tp.Self:
        """Compute config that should be inherited by codegen frame of a nested type.

        This method will:
        - Keep DEEP or unconsumed DEEP_ONCE options, marking them as consumed.
        - Drop DEEP_ONCE options that were consumed already.
        - Drop LOCAL or unknown propagation options
        """
        kls = self.__class__
        out = {}
        for name, bucket in self._entries.items():
            kept = []
            for e in bucket:
                if e.propagation is P.DEEP:
                    kept.append(e)
                elif e.propagation is P.DEEP_ONCE and not e.consumed:
                    kept.append(dcs.replace(e, consumed=True))
                # Ignore everything else: LOCAL + consumed DEEP_ONCE.
            if kept:
                out[name] = tuple(kept)

        return kls(out)

    def build_frame_config(
        self,
        target_type: type,
    ) -> "ResolvedConfig":
        """Build the config for this codegen frame based on this "inherited" config."""
        type_opts_for_target = get_type_options(target_type)
        if not type_opts_for_target:
            return self

        type_entries = _yield_entries(type_opts_for_target, Scope.TYPE)
        return self._with_overlay(type_entries)

    def build_field_config(
        self,
        field_opts: _FieldOptions | None,
    ) -> "ResolvedConfig":
        """Overlay field-level options onto this frame config.

        Field-sourced entries have precedence between DEEP_ONCE survivors.
        """
        if not field_opts:
            return self

        field_entries = _yield_entries(field_opts, Scope.FIELD)
        return self._with_overlay(field_entries)


def get_type_options(kls: type) -> TypeOptions | None:
    # TODO: Implement type options (https://github.com/charlesjhill/dataclassio/issues/13)
    return None
