import dataclasses as dcs

from dataclassio import functional as diof


@dcs.dataclass
class A:
    a: "A | None" = None


@dcs.dataclass
class B:
    c: "C | None" = None


@dcs.dataclass
class C:
    b: B | None = None


class TestRecursion:
    def test_self_references(self):
        expected = A(a=A(a=A(a=None)))
        data = {"a": {"a": {"a": None}}}
        assert diof.from_dict(A, data) == expected

    def test_cyclic_references(self):
        expected = C(b=B(c=C(b=B())))
        data = {"b": {"c": {"b": {"c": None}}}}
        assert diof.from_dict(C, data) == expected
