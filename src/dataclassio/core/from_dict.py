import dataclasses as dcs
import inspect
from functools import partial
from itertools import chain

import typing_extensions as tp

from dataclassio.config2 import ResolvedConfig
from dataclassio.constants import (
    _EXTRA_FIELD_ATTR_NAME,
    _POST_FROM_DICT_HOOK,
    _PRE_FROM_DICT_HOOK,
    _SPACER,
    ALIAS_OBJ,
    NO_VALUE,
    CycleOr,
    NoValueOr,
)
from dataclassio.types import EFS, DataclassInstance, TDataclass, TNamespace

from ._shared_codegen import maker_core, overrides_hook
from .expression_builder import SerializerData, build_expr
from .field_methods import field_has_default, get_fields, parse_default_expression
from .lines import TextLines
from .variables import make_variable_name, set_variable_in_ns

__all__ = (
    "make_from_dict_source_code",
    "make_from_dict",
)

_KNOWN_DESERIALIZERS: dict[tuple[type, tp.Any], tp.Callable[[tp.Mapping], tp.Any]] = {}


class AliasRet(tp.NamedTuple):
    base_expr: str
    alias_statements: TextLines
    lookup_names: tuple[str, ...]
    sentinel_var_name: str = ""


class FieldSpec(tp.NamedTuple):
    field: dcs.Field
    var_name: str
    expr: str
    has_default: bool
    alias_data: AliasRet

    @property
    def name(self):
        return self.field.name

    @property
    def kw_only(self):
        return self.field.kw_only

    @property
    def extra_statements(self):
        return self.alias_data.alias_statements

    @property
    def lookup_names(self):
        return self.alias_data.lookup_names


def _get_alias_lookup(
    f: dcs.Field,
    opt: NoValueOr[str | tp.Sequence[str]],
    is_required: bool,
    _ns: TNamespace,
    target_var_name: str,
) -> AliasRet:
    text = TextLines(spacer=_SPACER)
    field_name = f.name

    if opt is NO_VALUE:
        return AliasRet(f"dikt[{field_name!r}]", text, (field_name,))

    if isinstance(opt, str):
        return AliasRet(f"dikt[{opt!r}]", text, (opt,))

    if isinstance(opt, tp.Sequence) and len(opt) == 1:
        return AliasRet(f"dikt[{opt[0]!r}]", text, tuple(opt))

    if not isinstance(opt, tp.Sequence):
        msg = f"load_alias={opt} should be a str or Sequence[str]. Got {type(opt)}."
        raise RuntimeError(msg)  # TODO: MisconfigurationException

    # Add a local sentinel value.
    sent_name = set_variable_in_ns("ALIAS_OBJ", value=ALIAS_OBJ, ns=_ns)

    # handle the first option
    vname = target_var_name
    val = opt[0]
    with text.indent(f"if ({vname} := dikt.get({val!r}, {sent_name})) is not {sent_name}:"):
        text.append("pass")

    # Anndddd the rest.
    for val in opt[1:-1]:
        with text.indent(f"elif ({vname} := dikt.get({val!r}, {sent_name})) is not {sent_name}:"):
            text.append("pass")

    val = opt[-1]
    with text.indent(f"elif ({vname} := dikt.get({val!r}, {sent_name})) is {sent_name}:"):
        if is_required:
            msg = f"No valid aliases for field={f.name} found. Expected one of {list(opt)}."
            text.append(f"raise KeyError({msg!r})")
        else:
            text.append("pass")

    return AliasRet(vname, text, tuple(opt), sent_name)


def make_from_dict_source_code(
    cls: type[DataclassInstance],
    *,
    frame_config: ResolvedConfig,
    _ns: TNamespace | None = None,
) -> TextLines:
    """Generate the source code and necessary namespace for a from_dict deserialization method."""

    if _ns is None:
        _ns = {}

    cls_factory_name = set_variable_in_ns("cls", cls, ns=_ns)
    current_variable_names: set[str] = {"dikt", "_exc"}  # reserved locals

    fields = get_fields(cls, include_all=True)
    field_data: dict[str, FieldSpec] = {}

    for f in fields:
        if not f.init:
            # init=False field. Don't try to read it in.
            continue

        # extract and integrate field-options
        field_opts = f.metadata.get("dio")
        field_config = frame_config.build_field_config(field_opts)
        field_config_dict = field_config.as_dict()

        child_inherited = field_config.project_for_child()
        cache_key = child_inherited.legacy_cache_key

        # This is the assignment target for our variable.
        var_name = make_variable_name(f.name, ns=current_variable_names.union(_ns))
        current_variable_names.add(var_name)

        # Handle aliases
        f_has_default = field_has_default(f)
        load_alias = field_config_dict["load_alias"]
        alias_ret = _get_alias_lookup(
            f,
            load_alias,
            not f_has_default,
            _ns=_ns,
            target_var_name=var_name,
        )

        # Get the expression for parsing this field.
        assert not isinstance(f.type, str)
        field_expr = build_expr(
            f.type,
            alias_ret.base_expr,
            serializer_data=SerializerData(
                registry=_KNOWN_DESERIALIZERS,
                namespace=_ns,
                maker_func=partial(
                    make_from_dict,
                    inherited_config=child_inherited,
                    _ns=_ns,
                ),
                cache_key=cache_key,
                options=field_config_dict,
                func_prefix="deserialize",
            ),
        )

        field_data[f.name] = FieldSpec(
            f,
            var_name,
            field_expr,
            f_has_default,
            alias_ret,
        )

    # Assemble the final function body
    # Start with the try/except block for required keys.
    body = TextLines(spacer=_SPACER)

    if overrides_hook(cls, _PRE_FROM_DICT_HOOK) and not frame_config["disable_hooks"]:
        body.append(f"dikt = {cls_factory_name}.{_PRE_FROM_DICT_HOOK}(dikt)")

    req_fields = [v for v in field_data.values() if not v.has_default]
    if req_fields:
        with body.indent("try:"):
            for fs in req_fields:
                body.extend(fs.extra_statements)
                if fs.var_name != fs.expr:
                    body.append(f"{fs.var_name} = {fs.expr}")
        with body.indent("except KeyError as _exc:"):
            # TODO: This is wrong for multi-aliased fields.
            req_names = ", ".join(
                f"{x!r}" for x in chain.from_iterable(f.lookup_names for f in req_fields)
            )
            body.append(f"missing = {{ {req_names} }} - dikt.keys()")
            with body.indent("raise KeyError("):
                body.append(
                    f"f'{{sorted(missing)}} required for {cls.__name__}, missing from {{dikt=}}'"
                )
            body.append(") from _exc")

    # Now a block for optional parameters
    opt_fields = [v for v in field_data.values() if v.has_default]
    for fs in opt_fields:
        lookup_name = fs.lookup_names[0]
        check_expr = f"{lookup_name!r} in dikt"
        if fs.extra_statements:
            check_expr = f"{fs.var_name} is not {fs.alias_data.sentinel_var_name}"
            body.extend(fs.extra_statements)
        default_expr = parse_default_expression(fs.field, _ns)
        body.append(f"{fs.var_name} = {fs.expr} if {check_expr} else {default_expr}")

    # Now we need to build the constructor string. At this point, we have a local variable
    #  for every initializable argument. We need to do two things:
    # 1. Get these in the same order as the __init__ function
    # 2. Ensure we are using keyword-argument for kw-only fields.
    init_parts = []
    for param in inspect.signature(cls).parameters.values():
        fs = field_data[param.name]
        if fs.kw_only:
            init_parts.append(f"{fs.name}={fs.var_name}")
        else:
            assert param.kind not in (
                inspect.Parameter.KEYWORD_ONLY,
                inspect.Parameter.VAR_KEYWORD,
            )
            init_parts.append(fs.var_name)
    data_str = ", ".join(init_parts)

    # Generate code to handle extra fields.
    all_field_names = chain(
        (f.name for f in fields if not f.init), *(fs.lookup_names for fs in field_data.values())
    )
    extras = _handle_extra_fields(
        cls,
        all_field_names,
        frame_config["extra_field_strategy"],
        ns=_ns,
        attribute_name=_EXTRA_FIELD_ATTR_NAME,
    )

    # We have extras, so save the inst
    body.append(f"inst = {cls_factory_name}({data_str})")
    # N.B. For EFS.STRICT, this _could_ go at the top of the function body to bail early
    body.extend(extras)

    if overrides_hook(cls, _POST_FROM_DICT_HOOK) and not frame_config["disable_hooks"]:
        body.append(f"inst.{_POST_FROM_DICT_HOOK}(dikt)")

    body.append("return inst")

    # Pack it all up!
    funcname = frame_config.get_func_name(cls, "deserialize")
    lines = TextLines(spacer=_SPACER)
    with lines.indent(f"def {funcname}(dikt):"):
        lines.append(f'"""Deserialize a {cls.__name__} instance from a dictionary."""')
        lines.extend(body)

    return lines


def make_from_dict(
    cls: type[TDataclass],
    *,
    inherited_config: ResolvedConfig,
    _ns: TNamespace | None = None,
) -> CycleOr[tp.Callable[[tp.Mapping[str, tp.Any]], TDataclass]]:
    """Make a from_dict deserialization method for the given dataclass.

    Args:
        cls: The Dataclass type to generate the deserializer for.
    """
    return maker_core(
        cls,
        _KNOWN_DESERIALIZERS,
        make_from_dict_source_code,
        "deserialize",
        inherited_config=inherited_config,
        _ns=_ns,
    )


def _handle_extra_fields(
    cls: type[DataclassInstance],
    field_names: tp.Iterable[str],
    strategy: EFS,
    *,
    ns: TNamespace,
    dict_name: str = "dikt",
    instance_name: str = "inst",
    attribute_name: str = "_extra_fields",
) -> TextLines:
    lines = TextLines(spacer=_SPACER)
    if strategy == EFS.IGNORE:
        # Excluding extra fields is the easiest thing known to man.
        return lines

    # Precompute a lookup table with the known fields for this class.
    #  N.B. This will include init=False fields, thus preventing them from being counted
    #       as an extra.
    possible_field_names = frozenset(field_names)
    n_expected_fields = len(possible_field_names)

    field_names_set_varname = set_variable_in_ns(
        f"_KNOWN_FIELDS_{cls.__name__}", possible_field_names, ns=ns
    )

    condition_check = (
        f"if len({dict_name}) > {n_expected_fields} "
        f"or not {field_names_set_varname}.issuperset({dict_name}):"
    )
    extra_field_expr = (
        f"{{k: v for k, v in {dict_name}.items() if k not in {field_names_set_varname}}}"
    )

    if strategy == EFS.CAPTURE:
        with lines.indent(condition_check):
            lines.append(f"{instance_name}.{attribute_name} = {extra_field_expr}")
        return lines

    if strategy == EFS.STRICT:
        err_msg = (
            f"Extra fields are strictly prohibited for {{{instance_name}=}} of type {cls.__name__}"
        )
        with lines.indent(condition_check):
            # N.B. We are not concerned with shadowing any pre-existing locals since we are
            #      raising at this point anyway.
            lines.append(f"extra_kw = {extra_field_expr}")
            lines.append(f"msg = (f'{err_msg}, but the the input dictionary had'")
            lines.append("       f' the following extra fields: {list(extra_kw)}')")
            lines.append("raise ValueError(msg)")

        return lines

    msg = f"Unexpected {strategy=}. Must be an ExtraFieldStrategy enumeration."
    raise ValueError(msg)
