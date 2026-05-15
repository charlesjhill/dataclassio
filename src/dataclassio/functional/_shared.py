import linecache

import typing_extensions as tp

from dataclassio.config import (
    DioOptions,
    _TotalDioOptions,
    get_composite_options,
    get_options_cache_key,
)
from dataclassio.core.lines import TextLines
from dataclassio.types import DataclassInstance


def cache_source_code(src_code: TextLines, file_name: str):
    """Store generated source code in python's `linecache`.

    This is necessary to make stack traces and `inspect.getsource` work.
    """
    src_str = src_code.export()
    code_obj = compile(src_str, file_name, "exec")

    linecache.cache[file_name] = (len(src_str), None, src_str.splitlines(True), file_name)

    return code_obj


def maker_core(
    cls: type[DataclassInstance],
    registry: dict,
    maker_func: tp.Callable,
    func_prefix: tp.Literal["serialize", "deserialize"],
    direction: tp.Literal["to_dict", "from_dict"],
    *,
    options: _TotalDioOptions | DioOptions | None = None,
    _field_options: _TotalDioOptions | DioOptions | None = None,
    **kw: tp.Unpack[DioOptions],
):
    call_options = options or {}
    call_options.update(kw)

    opts = get_composite_options(_field_options, call_options)
    key, str_key = get_options_cache_key(opts, direction)

    if (f := registry.get((cls, key), None)) is not None:
        return f

    func_name = f"{func_prefix}_{cls.__name__}{str_key}"
    src, ns = maker_func(
        cls, funcname=func_name, call_options=call_options, _field_options=_field_options
    )

    file_name = f"dataclassio/generated/{func_name}.py"
    code_obj = cache_source_code(src, file_name)
    exec(code_obj, ns)
    func = ns[func_name]

    if opts["include_src_in_docstring"]:
        func.__doc__ = func.__doc__ or ""
        func.__doc__ += f"\n\n{src[2:]!s}\n"

    registry[(cls, key)] = func
    return func
