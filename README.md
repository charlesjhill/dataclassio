# DataclassIO

`DataclassIO` is a simple package to enable nested dictionary conversion of dataclass hierarchies with explicit support for handling extra fields.

This project is in its early stages, but it is has minimum viable functionality for my use-cases.

Up next would be:

- [ ] Supporting unions of Dataclasses (incl. discriminated unions)
- [ ] JSON import/export in `IOMixin`.
- [ ] Bug hunting and edge cases around the dataclass spec and typing system.

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
