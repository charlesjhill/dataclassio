import linecache

from dataclassio.core.lines import TextLines


def cache_source_code(src_code: TextLines, file_name: str):
    src_str = src_code.export()
    code_obj = compile(src_str, file_name, "exec")

    linecache.cache[file_name] = (len(src_str), None, src_str.splitlines(True), file_name)

    return code_obj
