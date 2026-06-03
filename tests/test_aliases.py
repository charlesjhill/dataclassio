import dataclasses as dcs

import pytest

from dataclassio import FieldOptions, IOMixin
from dataclassio.types import EFS


@dcs.dataclass
class SingleLoadAlias(IOMixin):
    x: int = dcs.field(metadata=FieldOptions(load_alias="x_alias"))


@dcs.dataclass
class MultipleLoadAliases(IOMixin):
    x: int = dcs.field(metadata=FieldOptions(load_alias=("x_alias_1", "x_alias_2", "x")))


@dcs.dataclass
class DumpAlias(IOMixin):
    x: int = dcs.field(metadata=FieldOptions(dump_alias="x_alias"))


@dcs.dataclass
class LoadAndDumpAlias(IOMixin):
    x: int = dcs.field(metadata=FieldOptions(load_alias=("x_alias", "x"), dump_alias="x_alias"))


@dcs.dataclass
class NoAlias(IOMixin):
    x: int


class TestLoadAlias:
    def test_load_alias_single_string(self):
        obj = SingleLoadAlias.from_dict({"x_alias": 1})
        assert obj.x == 1

    def test_load_alias_default_name_not_recognized_if_not_in_aliases(self):
        """If the default name is not in the alias list, it should not be recognized."""
        with pytest.raises(KeyError, match="required"):
            SingleLoadAlias.from_dict({"x": 1})

    def test_load_alias_multiple_strings_first_alias_used(self):
        obj = MultipleLoadAliases.from_dict({"x_alias_1": 1})
        assert obj.x == 1

    def test_load_alias_multiple_strings_second_alias_used(self):
        obj = MultipleLoadAliases.from_dict({"x_alias_2": 1})
        assert obj.x == 1

    def test_load_alias_multiple_strings_default_name_recognized(self):
        """The default name is explicitly provided in the alias tuple."""
        obj = MultipleLoadAliases.from_dict({"x": 1})
        assert obj.x == 1

    def test_load_alias_multiple_present_first_encountered_wins(self):
        """If multiple aliases are in the input dict, the first one encountered is used."""
        obj = MultipleLoadAliases.from_dict({"x_alias_1": 1, "x_alias_2": 99, "x": 42})
        assert obj.x == 1

    def test_load_alias_multiple_present_no_extra_field_error(self):
        """Other aliases in the input should not be treated as extra/unknown fields."""
        dikt = {"x_alias_1": 1, "x_alias_2": 99}

        # No raise
        obj = MultipleLoadAliases.from_dict(dikt, extra_field_strategy=EFS.STRICT)
        assert obj.x == 1

        obj = MultipleLoadAliases.from_dict(dikt, extra_field_strategy=EFS.CAPTURE)
        assert obj.x == 1
        assert not obj.extra_fields  # Not captured.


class TestDumpAlias:
    def test_dump_alias_used_in_to_dict(self):
        obj = DumpAlias(x=1)
        # Note that the default name is NOT used, and the alias is.
        assert obj.to_dict() == {"x_alias": 1}

    def test_no_dump_alias_uses_default_name(self):
        obj = NoAlias(x=1)
        assert obj.to_dict() == {"x": 1}


class TestLoadAndDumpAlias:
    def test_roundtrip_with_alias(self):
        obj = LoadAndDumpAlias(x=1)
        d = obj.to_dict()
        assert d == {"x_alias": 1}
        restored = LoadAndDumpAlias.from_dict(d)
        assert restored.x == 1

    def test_load_default_name_also_works(self):
        obj = LoadAndDumpAlias.from_dict({"x": 1})
        assert obj.x == 1
