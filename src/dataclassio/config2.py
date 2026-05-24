import dataclasses as dcs
from enum import Enum, auto

import typing_extensions as tp

from dataclassio.sentinels import NO_VALUE, NoValueOr
from dataclassio.types import EFS

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

    CALL = 10
    TYPE = 20
    FIELD = 30


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
    to_str=lambda _: "skip_if_default",
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
    to_str=lambda _: "skip_defaults",
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

    value: tp.Any
    source: Scope

    # Flag if this entry arrived via a DEEP_ONCE hop and should be dropped
    #  on the next projection. While "consumed", it can participate in
    #  codegen of the current frame and continues to override CALL-sourced values.
    consumed: bool = False

    @property
    def precedence(self):
        if self.consumed:
            return 40
        return self.source.value


def _make_entries(mapping: tp.Mapping[str, tp.Any] | None, source: Scope):
    if not mapping:
        return {}
    out: dict[str, ConfigEntry] = {}
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
        out[opt_name] = ConfigEntry(value=opt_value, source=source)
    return out


@dcs.dataclass(frozen=True)
class ResolvedConfig:
    """An immutable, fully-resolved view of options for a single codegen frame."""

    call_layer: tp.Mapping[str, ConfigEntry] = dcs.field(default_factory=dict)
    overlay_layer: tp.Mapping[str, ConfigEntry] = dcs.field(default_factory=dict)

    @classmethod
    def from_call(cls, call_options: CallOptions | None = None) -> tp.Self:
        entries = _make_entries(call_options, Scope.CALL)
        # CALL-sourced options with LOCAL propagation (if any ever exist)
        # belong in the overlay, not the persistent base. Today all CALL
        # options are DEEP, but we encode the rule explicitly:
        call_layer: dict[str, ConfigEntry] = {}
        overlay: dict[str, ConfigEntry] = {}
        for name, entry in entries.items():
            prop = REGISTRY[name].scopes[Scope.CALL]
            if prop is Propagation.DEEP:
                call_layer[name] = entry
            else:
                overlay[name] = entry
        return cls(call_layer, overlay)

    def _effective_entry(self, name: str):
        return self.overlay_layer.get(name) or self.call_layer.get(name)

    def __getitem__(self, key: str) -> tp.Any:
        entry = self._effective_entry(key)
        if entry is None:
            spec = REGISTRY[key]
            return spec.default
        return entry.value

    def __contains__(self, name: str) -> bool:
        return name in self.overlay_layer or name in self.call_layer

    def as_dict(self) -> DioOptions:
        return DioOptions(
            extra_field_strategy=self["extra_field_strategy"],
            discriminator=self["discriminator"],
            skip_defaults=self["skip_defaults"],
            skip_if_default=self["skip_if_default"],
            include_src_in_docstring=self["include_src_in_docstring"],
        )

    @property
    def cache_key(self) -> str:
        def freeze(layer: tp.Mapping[str, ConfigEntry]):
            str_data = []

            for opt_name, entry in sorted(layer.items()):
                option_spec = REGISTRY[opt_name]

                if entry.value != option_spec.default:
                    str_data.append(option_spec.to_str(entry.value))

                    if entry.consumed:
                        str_data.append("used")

            return str_data

        call_opts = freeze(self.call_layer)
        overlay_opts = freeze(self.overlay_layer)

        if call_opts:
            call_opts.append("call")
        if overlay_opts:
            overlay_opts.append("overlay")

        all_opts = [*call_opts, *overlay_opts]

        if len(all_opts) >= 2:
            return f"_{'__'.join(all_opts)}"

        if len(all_opts) == 1:
            return f"_{all_opts[0]}"

        return ""

    @property
    def legacy_cache_key(self) -> tuple[tp.Hashable, str]:
        k = self.cache_key
        return k, k

    def _with_overlay(self, new_entries: tp.Mapping[str, ConfigEntry]) -> "ResolvedConfig":
        """Merge new entries into the overlay using precedence rules.

        The call layer is untouched.
        """
        merged: dict[str, ConfigEntry] = dict(self.overlay_layer)
        for name, entry in new_entries.items():
            existing = merged.get(name)
            if existing is None or entry.precedence >= existing.precedence:
                merged[name] = entry

        return ResolvedConfig(self.call_layer, merged)

    def project_for_child(self) -> "ResolvedConfig":
        """Compute config that should be inherited by codegen frame of a nested type.

        This method will:
        - Drop LOCAL
        """
        kept: dict[str, ConfigEntry] = {}
        for name, entry in self.overlay_layer.items():
            # A consumed (i.e., DEEP_ONCE survivor) entry has already used its
            #  hop. It does not propagate further regardless of its original
            #  source's declared propagation.
            if entry.consumed:
                continue
            spec = REGISTRY[name]

            prop = spec.scopes.get(entry.source)
            if prop is P.DEEP:
                kept[name] = entry
            elif prop is P.DEEP_ONCE:
                kept[name] = dcs.replace(entry, consumed=True)
            # Unknown or LOCAL propagation gets dropped
        return ResolvedConfig(self.call_layer, kept)

    def build_frame_config(
        self,
        type_opts_for_target: TypeOptions | None,
    ) -> "ResolvedConfig":
        """Build the config for this codegen frame based on this "inherited" config.

        Composition rules:
        - `inherited` carries CALL-sourced DEEP options, plus any DEEP_ONCE survivors
          (consumed) from a parent field.
        - type-level options for `kls` are loaded fresh; they do not propagate to nested types.
        - Within the frame precedence:
              DEEP_ONCE > FIELD > TYPE > CALL > DEFAULTS
          which is enforced by ConfigEntry.precendence()
        """
        type_entries = _make_entries(type_opts_for_target, Scope.TYPE)

        # overlay handles precedence: DEEP_ONCE survivor > TYPE > CALL
        return self._with_overlay(type_entries)

    def build_field_config(
        self,
        field_opts: _FieldOptions | None,
    ) -> "ResolvedConfig":
        """Overlay field-level options onto this frame config.

        Field-sourced entries have precedence between DEEP_ONCE survivors.
        """

        field_entries = _make_entries(field_opts, Scope.FIELD)
        return self._with_overlay(field_entries)


def get_type_options(kls: type) -> TypeOptions | None:
    # TODO: Implement type options (https://github.com/charlesjhill/dataclassio/issues/13)
    return None
