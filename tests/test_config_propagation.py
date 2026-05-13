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


# Assuming the library components are imported as follows:
# from dataclass_io import IOMixin, FieldOpts, EFS, from_dict


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
        # Verify propagation to the inner dataclass
        assert obj.inner.innermost.extra_fields["extra_at_innermost"] == "captured_too"

    def test_strict_strategy_failure(self):
        """Test CASE 2: inner2 (EFS.STRICT) raises ValueError if any extras exist."""
        # Payload with extra field only in the STRICT branch
        bad_payload = {
            "inner": {"innermost": {"core": "c1"}},
            "inner2": {"innermost": {"core": "c2", "forbidden": "error"}},
            "inner3": {"innermost": {"core": "c3"}},
        }

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
