import copy
import dataclasses as dcs

import pytest

from dataclassio import EFS
from dataclassio.config import FieldOpts
from dataclassio.io_mixin import IOMixin


@dcs.dataclass
class InnerMost(IOMixin):
    core: str


@dcs.dataclass
class Inner(IOMixin):
    innermost: InnerMost


@dcs.dataclass
class Outer(IOMixin):
    inner: Inner = dcs.field(metadata=FieldOpts(extra_field_strategy=EFS.CAPTURE))
    inner2: Inner = dcs.field(metadata=FieldOpts(extra_field_strategy=EFS.STRICT))
    inner3: Inner


class TestExtraFieldPropagation:
    def test_capture_strategy_propagation(self):
        """Test CASE 1: inner (EFS.CAPTURE) captures extras and propagates to child."""
        payload = {
            "inner": {
                "extra_at_inner": "captured",
                "innermost": {"core": "c1", "extra_at_innermost": "captured_too"},
            },
            "inner2": {"innermost": {"core": "c2"}},  # Clean to avoid STRICT error
            "inner3": {"innermost": {"core": "c3"}},
        }

        obj = Outer.from_dict(payload)

        # Verify capture on the field itself
        assert obj.inner.extra_fields["extra_at_inner"] == "captured"
        # Verify NO propagation is occuring to the inner dataclass
        assert not obj.inner.innermost.extra_fields

    def test_strict_strategy_failure(self):
        """Test CASE 2: inner2 (EFS.STRICT) raises ValueError if any extras exist."""
        # Payload with extra field only in the STRICT branch
        safe_payload: dict = {
            "inner": {"innermost": {"core": "c1"}},
            "inner2": {"innermost": {"core": "c2", "extra_key": "extra_value"}},
            "inner3": {"innermost": {"core": "c3"}},
        }

        # The STRICT rule does not apply to `inner2.innermost`
        obj = Outer.from_dict(safe_payload)
        assert not obj.inner2.innermost.extra_fields

        # It still applies to the `inner2` member
        bad_payload = copy.deepcopy(safe_payload)
        bad_payload["inner2"]["extra_key"] = "extra_value"

        with pytest.raises(ValueError, match="extra fields"):
            Outer.from_dict(bad_payload)

    def test_ignore_strategy_silence(self):
        """Test CASE 3: inner3 (Default/IGNORE) silently drops extra fields."""
        payload = {
            "inner": {"innermost": {"core": "c1"}},
            "inner2": {"innermost": {"core": "c2"}},
            "inner3": {"ignored_key": "bye", "innermost": {"core": "c3", "ignored_inner": "bye"}},
        }

        obj = Outer.from_dict(payload)

        # Ensure no error was raised and no capture occurred
        assert obj.inner3.innermost.core == "c3"
        assert not obj.inner3.extra_fields
        assert not obj.inner3.innermost.extra_fields

    def test_strategy_isolation(self):
        """Ensures strategies do not bleed between sibling fields."""
        # If inner2 is clean, the whole object should parse even if inner has extras
        payload = {
            "inner": {"extra": "val", "innermost": {"core": "c1"}},
            "inner2": {"innermost": {"core": "c2"}},
            "inner3": {"innermost": {"core": "c3"}},
        }

        # This should NOT raise ValueError because inner2's branch is clean
        obj = Outer.from_dict(payload)
        assert obj.inner2.innermost.core == "c2"

    def test_efs_hierarchy_precedence(self):
        """
        Ensures that Field-Level metadata takes highest priority over
        global or type-level settings.
        """
        # Even if we pass EFS.STRICT globally, 'inner' should still CAPTURE
        # because field-level metadata is Priority 1.
        payload = {
            "inner": {"extra": "captured", "innermost": {"core": "v"}},
            "inner2": {"innermost": {"core": "v"}},
            "inner3": {"innermost": {"core": "v"}},
        }

        # Providing a global override that would otherwise fail the whole call
        obj = Outer.from_dict(payload, extra_field_strategy=EFS.STRICT)

        # 'inner' should have succeeded despite global STRICT setting
        assert obj.inner.extra_fields["extra"] == "captured"


@dcs.dataclass
class GrandChild:
    name: str = "default_name"
    age: int = 0


@dcs.dataclass
class Child:
    name: str = "default_child"
    grand_child: GrandChild = dcs.field(default_factory=GrandChild)


@dcs.dataclass
class Root(IOMixin):
    id: int = 1
    # Field-level configuration target
    child: Child = dcs.field(default_factory=Child, metadata=FieldOpts(skip_if_default=True))
    # Control field to ensure field-level doesn't leak sideways
    other_child: Child = dcs.field(default_factory=Child)


@dcs.dataclass
class SpecificRoot(IOMixin):
    # Explicitly force-include defaults for this field only
    child: Child = dcs.field(default_factory=Child, metadata=FieldOpts(skip_if_default=False))


class TestSkipDefaultsPropagation:
    """
    Tests the precedence and propagation of the 'skip_if_default' option.
    Logic: Field > Call > Global (False)
    """

    def test_default_behavior(self):
        """By default, skip_if_default is False. All fields should be present."""
        obj = Root()
        result = obj.to_dict()

        # Everything should be present because global default is False
        assert "id" in result
        assert "name" in result["other_child"]
        assert "name" in result["other_child"]["grand_child"]

        # Child has a default value, so it is skipped.
        assert "child" not in result

    def test_call_level_propagation(self):
        """Call-level True should propagate to the entire tree."""
        obj = Root()
        # We explicitly set skip_if_default=True at the call level
        result = obj.to_dict(skip_if_default=True)

        # Since the object is completely default-valued, this should be the empty dict.
        assert result == {}

    def test_field_level_precedence_inverse(self):
        """If field-level is False but call-level is True, field-level wins."""

        obj = SpecificRoot()
        result = obj.to_dict(skip_if_default=True)

        # Even though child has a default value, it is kept. It's members are both
        #  default valued though, and thus discarded.
        assert result == {"child": {}}

        obj = SpecificRoot(Child(name="new_name"))
        result = obj.to_dict(skip_if_default=True)

        assert result == {"child": {"name": "new_name"}}
