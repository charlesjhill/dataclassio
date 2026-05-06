# DataclassIO

`DataclassIO` is a simple package to enable nested dictionary conversion of dataclass hierarchies with explicit support for handling extra fields round trip, and exluding default-valued fields on export.

This project is in its early stages, but it is has minimum viable functionality for my use-cases.

## Supported Types and Constructs

Currently, the following types are supported:

- Optional expressions: `Optional[T]`, `T | None`, or `Union[T, None]`
- Embedded dataclasses: `DataclassType` (exports as `dict`)
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
- Class variables (no impact).

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

## Dataclass -> Dictionary
dikt = actual.to_dict(skip_defaults=True)
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
