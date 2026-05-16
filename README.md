# DataclassIO

`DataclassIO` is a *fast* package for rountrip conversion between python literals and dataclass hierarchies.

This project is in its early stages, but it is has minimum viable functionality for my use-cases.

## Supported Types and Constructs

Currently, the following types are supported:

- Optional expressions: `Optional[T]`, `T | None`, or `Union[T, None]`
- Embedded dataclasses: `DataclassType` (exports as `dict`)
    - Unions of multiple dataclasses are supported via a discriminator.
- Lists: `list[T]`
- Dicts: `dict[TK, TV]`
- Enums: `Enum` (exports as `str`)
- Datetimes: `datetime` (imports/exports to ISO-8601 string)
- fundamental types: e.g., `int`, `float`, `str`, `bool`

Where the `T`, `TK`, and `TV` type variables may be any other type listed in the table.
For instance, `dict[str, list[DataclassType | None]]` is supported.

The library also supports common dataclass features:

- Default values and default factories: `field(default=..., default_factory=...)`
- Init-only and `init=False` fields
  - Note that `init=False` fields are still exported as usual.
- `kw_only` fields and dataclasses.
- Class variables.

## Example

```python
from dataclasses import dataclass, field

from dataclassio import IOMixin, EFS

@dataclass
class Address(IOMixin):
    city: str
    zip_code: tp.Optional[str] = None


@dataclass
class User(IOMixin):
    id: int
    name: str
    is_admin: bool = False
    address: tp.Optional[Address] = None  # <-- Address need not derive from IOMixin!
    named_addresses: dict[str, Address] = field(default_factory=dict)

## Dictionary -> Dataclass

data = {
    "id": 1,
    "name": "Alice",
    "named_addresses": {"home": {"city": "Anytown"}, "work": {"city": "Coolsville"}},
}
actual = User.from_dict(data)
assert isinstance(actual.named_addresses, dict)
assert isinstance(actual.named_addresses["home"], Address)
assert actual.named_addresses["work"].city == "Coolsville"

## Dataclass -> Dictionary (note that the default-valued-fields are excluded)
dikt = actual.to_dict(skip_if_default=True)
assert dikt == data

## Extra Fields are captured:
address_data = {
    "city": "Anytown",
    "bonus": "extra",
}
address_obj = Address.from_dict(address_data, extra_field_strategy=EFS.CAPTURE)
assert address_obj.extra_fields == {"bonus": "extra"}
assert address_obj.to_dict() == address_data  # extra fields survive round trip.
```

## Configuration

A handful of configuration options are supported to customize serialization and deserialization. These can be provided either at time of a `to_dict` or `from_dict` call ("call-level config") or can be applied to individual dataclass fields statically ("field-level config"). The following options are supported:

* `discriminator`: The name of a field to use when discrimating between unions of dataclass types.
* `skip_if_default`: A flag to omit fields during the `to_dict` call if they have the default value.
* `extra_field_strategy`: The preferred method for handling unexpected fields during deserialization (`from_dict`). By default they are ignored. Alternatively, an exception can be raised (`STRICT`-mode) or they can be captured into a private attribute of the object (`CAPTURE`-mode). In `CAPTURE`-mode, the unexpected fields are yielded in the `to_dict` call, supporting full round-tripping.
* `include_src_in_docstring`: A flag to include `to_dict` and `from_dict` method source code in their corresponding docstrings. This is useful since their source code is dynamically generated.

### Propagation and Precedence

When a configuration option is specified at both the call- and field-level, the field-level option is preferred.

In addition to precedence differences, options propagate differently depending on where they are defined. Call-level config options always propagate through fields which are themselves dataclass-typed. Field-level config options do not.

Field-level options can be conceptually divided into "shallow" and "deep" categories. "Shallow" options (e.g., `discriminator`) affect the code-generation for their contained dataclass but not the nested dataclass. Meanwhile, "deep" options (e.g., `extra_field_strategy`) are the inverse - they _do not_ affect the code-generation for their contained dataclass but _do_ for the affected field. Most of the time, this distinction is natural and does not need to be top of mind.

## Benchmarks

### Dict -> Dataclass

We compare the deserialization (i.e., `from_dict`) methods for `dataclassio` and similar python libraries using the COCO2017 validation dataset (~20MB; 5000 images; 36781 annotations), which is a large but shallow JSON hierarchy. For benchmarking, the JSON file is first loaded and converted to python builtins. This dataset has no extra fields, so the equivalent of `extra_field_strategy=EFS.IGNORE` is utilized for all libraries.

We obtain the following times using `pybench run benchmarks/compare_with_other_libraries.py --profile thorough`:

| benchmark | time (avg) | p99 | vs base |
| --- | --- | --- | --- |
| dataclassio  ★ | 48.39 ms | 50.26 ms | baseline |
| pydantic v2 | 85.82 ms | 93.31 ms | 1.77× slower |
| msgspec_into_dataclass | 39.22 ms | 42.99 ms | 1.23× faster |
| msgspec_into_native | 19.97 ms | 20.80 ms | 2.42× faster |
| mashumaro | 62.42 ms | 63.09 ms | 1.29× slower |
| dataclass-wizard | 63.40 ms | 65.95 ms | 1.31× slower |

Only `msgspec` is significantly faster `dataclassio`, but it does not support capturing extra fields. As a key distinction, `dataclassio` **does not** try to validate or coerce types, which may explain some or all of the performance advantages relative to other libraries, which may be coercing by default. Other libraries are also more configurable, may support more types, and so forth. However, if all you need is fast dict -> dataclass conversion that supports capturing unexpected fields, then `dataclassio` may be a good fit.

### Dataclass -> Dict

Using the same large COCO2017 dataset, we also evaluate conversion back to python literals (e.g., `to_dict`) using the default settings for all libraries.

We obtain the following times using `pybench run benchmarks/compare_to_dict.py --profile smoke`:

| benchmark | time (avg) | p99 | vs base |
| --- | --- | --- | --- |
| dataclassio  ★ | 28.25 ms | 28.30 ms | baseline |
| native | 376.97 ms | 377.70 ms | 13.34× slower |
| pydantic | 130.21 ms | 130.70 ms | 4.61× slower |
| msgspec_from_dataclass | 92.68 ms | 93.50 ms | 3.28× slower |
| msgspec_from_struct | 86.26 ms | 87.91 ms | 3.05× slower |
| mashumaro | 29.74 ms | 30.14 ms | 1.05× slower |
| dataclass-wizard | 33.81 ms | 35.12 ms | 1.20× slower |

In this test, `dataclassio` was the fastest library available, though `mashumaro` is probably equivalent.
