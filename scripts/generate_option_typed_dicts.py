from dataclassio.config2 import ALL_OPTIONS, Scope
from dataclassio.core.lines import TextLines


def make_typed_dict_spec(name: str, d: dict[str, str], total=False):
    L = TextLines()
    with L.indent(f"class {name}(tp.TypedDict, total={total}):"):
        for k, v in d.items():
            L.append(f"{k}: {v}")
    return L


print(
    make_typed_dict_spec(
        "CallOptions", {o.name: o.type_str for o in ALL_OPTIONS if Scope.CALL in o.scopes}
    )
)
print()
print(
    make_typed_dict_spec(
        "TypeOptions", {o.name: o.type_str for o in ALL_OPTIONS if Scope.TYPE in o.scopes}
    )
)
print()
print(
    make_typed_dict_spec(
        "_FieldOptions", {o.name: o.type_str for o in ALL_OPTIONS if Scope.FIELD in o.scopes}
    )
)
print()
print(make_typed_dict_spec("DioOptions", {o.name: o.type_str for o in ALL_OPTIONS}, total=True))
