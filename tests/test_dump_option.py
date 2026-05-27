from dataclasses import dataclass, field

from dataclassio import functional as F
from dataclassio.config2 import FieldOptions


class TestDump:
    def test_dump_true_by_default(self):
        @dataclass
        class MyClass:
            x: int
            y: int

        obj = MyClass(x=1, y=2)
        assert F.to_dict(obj) == {"x": 1, "y": 2}

    def test_dump_false_excludes_field(self):
        @dataclass
        class MyClass:
            x: int
            y: int = field(metadata=FieldOptions(dump=False))

        obj = MyClass(x=1, y=2)
        assert F.to_dict(obj) == {"x": 1}

    def test_dump_false_on_all_fields(self):
        """Test that all fields can be disabled without issue."""

        @dataclass
        class MyClass:
            x: int = field(metadata=FieldOptions(dump=False))
            y: int = field(metadata=FieldOptions(dump=False))
            z: str = field(metadata=FieldOptions(dump=False))

        obj = MyClass(x=1, y=2, z="hello")
        assert F.to_dict(obj) == {}
