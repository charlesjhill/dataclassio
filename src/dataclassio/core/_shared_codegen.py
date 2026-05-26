import linecache

import typing_extensions as tp

from dataclassio.config2 import ResolvedConfig
from dataclassio.sentinels import CYCLE_DETECTED, IN_PROGRESS, CycleOr
from dataclassio.types import DataclassInstance, SourceCodeMaker, TNamespace

from .field_methods import get_fields
from .lines import TextLines


def maker_core(
    cls: type[DataclassInstance],
    registry: dict,
    maker_func: SourceCodeMaker,
    func_prefix: tp.Literal["serialize", "deserialize"],
    *,
    inherited_config: ResolvedConfig,
    _ns: TNamespace | None = None,
) -> CycleOr[tp.Callable]:
    if _ns is None:
        # DO NOT use `_ns = _ns or {}` since we don't want to
        #  change the reference when _ns is merely the empty dict.
        _ns = tp.cast("TNamespace", {})

    config = inherited_config.build_frame_config(cls)
    cache_key = config.cache_key()
    key = (cls, cache_key)

    # Look for the function in the registry. If it doesn't exist, mark it as IN_PROGRESS.
    # When the function is fully generated, we will overwrite it later.
    func = registry.get(key)
    if func is IN_PROGRESS:
        return CYCLE_DETECTED
    if func is not None:
        return func
    registry[key] = IN_PROGRESS

    validate_type_hints(cls)

    src = maker_func(
        cls,
        frame_config=config,
        _ns=_ns,
    )

    func_name = config.get_func_name(cls, func_prefix)

    file_name = f"dataclassio/generated/{func_name}.py"
    code_obj = cache_source_code(src, file_name)

    # exec requires a real dictionary!
    exec(code_obj, _ns)
    func = _ns[func_name]

    if config["include_src_in_docstring"]:
        func.__doc__ = func.__doc__ or ""
        func.__doc__ += f"\n\n{src[2:]!s}\n"

    # Store the generated function in the global registry
    registry[key] = func
    return func


def cache_source_code(src_code: TextLines, file_name: str):
    """Store generated source code in python's `linecache`.

    This is necessary to make stack traces and `inspect.getsource` work.
    """
    src_str = src_code.export()
    code_obj = compile(src_str, file_name, "exec")

    linecache.cache[file_name] = (len(src_str), None, src_str.splitlines(True), file_name)

    return code_obj


def validate_type_hints(kls: type[DataclassInstance]):
    # Check if fields were forward reference
    fields = get_fields(kls, include_all=True)

    forward_ref_fields = [f for f in fields if isinstance(f.type, str)]
    if forward_ref_fields:
        resolved_annotations = tp.get_annotations(kls, eval_str=True, format=tp.Format.VALUE)
        for f in forward_ref_fields:
            f.type = resolved_annotations[f.name]
