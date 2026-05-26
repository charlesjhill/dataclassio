import copy
import dataclasses as dcs

import pytest

from dataclassio import EFS
from dataclassio import functional as diof
from dataclassio.config2 import FieldOptions
from dataclassio.io_mixin import IOMixin


@dcs.dataclass
class InnerMost(IOMixin):
    core: str


@dcs.dataclass
class Inner(IOMixin):
    innermost: InnerMost


@dcs.dataclass
class Outer(IOMixin):
    inner: Inner = dcs.field(metadata=FieldOptions(extra_field_strategy=EFS.CAPTURE))
    inner2: Inner = dcs.field(metadata=FieldOptions(extra_field_strategy=EFS.STRICT))
    inner3: Inner


class TestExtraFieldPropagation:
    def test_capture_strategy_propagation(self):
        """inner (EFS.CAPTURE) captures extras and does not propagate to child."""
        payload = {
            "inner": {
                "extra_at_inner": "captured",
                "innermost": {"core": "c1", "extra_at_innermost": "not_captured"},
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
        """inner2 (EFS.STRICT) raises ValueError if any extras exist on inner2 only."""
        # Payload with extra field only in the STRICT branch
        safe_payload: dict = {
            "inner": {"innermost": {"core": "c1"}},
            "inner2": {"innermost": {"core": "c2", "extra_key": "not_a_problem"}},
            "inner3": {"innermost": {"core": "c3"}},
        }

        # The STRICT rule does not apply to `inner2.innermost`
        obj = Outer.from_dict(safe_payload)
        assert not obj.inner2.innermost.extra_fields

        # It still applies to the `inner2` member
        bad_payload = copy.deepcopy(safe_payload)
        bad_payload["inner2"]["extra_key"] = "a_big_problem"

        with pytest.raises(ValueError, match="extra fields"):
            Outer.from_dict(bad_payload)

    def test_ignore_strategy_silence(self):
        """inner3 (Default/IGNORE) silently drops extra fields."""
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

        bad_payload = {
            "inner": {"extra": "captured", "innermost": {"core": "v", "extra": "BAD"}},
            "inner2": {"innermost": {"core": "v"}},
            "inner3": {"innermost": {"core": "v"}},
        }

        with pytest.raises(ValueError, match="extra fields"):
            Outer.from_dict(bad_payload, extra_field_strategy=EFS.STRICT)

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
    child: Child = dcs.field(default_factory=Child, metadata=FieldOptions(skip_if_default=True))
    # Control field to ensure field-level doesn't leak sideways
    other_child: Child = dcs.field(default_factory=Child)


@dcs.dataclass
class SpecificRoot(IOMixin):
    # Explicitly force-include defaults for this field only
    child: Child = dcs.field(default_factory=Child, metadata=FieldOptions(skip_if_default=False))


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
        result = obj.to_dict(skip_defaults=True)

        # Since the object is completely default-valued, this should be the empty dict.
        assert result == {}

    def test_field_level_precedence_inverse(self):
        """If field-level is False but call-level is True, field-level wins."""

        obj = SpecificRoot()
        result = obj.to_dict(skip_defaults=True)

        # Even though child has a default value, it is kept. It's members are both
        #  default valued though, and thus discarded.
        assert result == {"child": {}}

        obj = SpecificRoot(Child(name="new_name"))
        result = obj.to_dict(skip_defaults=True)

        assert result == {"child": {"name": "new_name"}}


class TestSkipDefaultsSemantics:
    """
    Precedence rules under test:

      * `skip_if_default` is FIELD/LOCAL: only affects the field it's set on,
        in the current frame. Never propagates.
      * `skip_defaults` is CALL/DEEP and FIELD/DEEP_ONCE: at call site it
        propagates everywhere; at field level it applies to the *nested*
        frame for that field's type, one level only.
      * `skip_if_default` takes precedence over `skip_defaults` in the
        current frame when both would apply.
      * Neither set => field is emitted.
    """

    # ---- shared fixtures -------------------------------------------------

    @dcs.dataclass
    class Leaf:
        a: int = 0
        b: int = 0

    @dcs.dataclass
    class Mid:
        x: int = 0
        leaf: "TestSkipDefaultsSemantics.Leaf" = dcs.field(
            default_factory=lambda: TestSkipDefaultsSemantics.Leaf()
        )

    # ---- baseline: no options => nothing is skipped ----------------------

    def test_no_options_emits_all_fields(self):
        @dcs.dataclass
        class Root:
            m: "TestSkipDefaultsSemantics.Mid" = dcs.field(
                default_factory=lambda: TestSkipDefaultsSemantics.Mid()
            )

        assert diof.to_dict(Root()) == {"m": {"x": 0, "leaf": {"a": 0, "b": 0}}}

    # ---- skip_if_default at field level, current frame only --------------

    def test_skip_if_default_field_level_only_affects_that_field(self):
        @dcs.dataclass
        class Root:
            x: int = dcs.field(default=0, metadata=FieldOptions(skip_if_default=True))
            y: int = 0  # no option => emitted even though it's default

        assert diof.to_dict(Root()) == {"y": 0}

    def test_skip_if_default_does_not_propagate_into_nested(self):
        # Setting skip_if_default on a field whose type is a dcs.dataclass must
        # NOT cause the *nested* dcs.dataclass's default fields to be skipped.
        @dcs.dataclass
        class Root:
            m: "TestSkipDefaultsSemantics.Mid" = dcs.field(
                default_factory=lambda: TestSkipDefaultsSemantics.Mid(),
                metadata=FieldOptions(skip_if_default=True),
            )

        # Root.m equals its default => Root-frame skips it entirely.
        assert diof.to_dict(Root()) == {}

        # But if Root.m is non-default, the nested Mid frame must still emit
        # its own default fields (skip_if_default is LOCAL, didn't propagate).
        r = Root(m=TestSkipDefaultsSemantics.Mid(x=1))
        assert diof.to_dict(r) == {"m": {"x": 1, "leaf": {"a": 0, "b": 0}}}

    # ---- skip_defaults at call site: DEEP --------------------------------

    def test_skip_defaults_call_site_propagates_to_all_frames(self):
        @dcs.dataclass
        class Root:
            m: "TestSkipDefaultsSemantics.Mid" = dcs.field(
                default_factory=lambda: TestSkipDefaultsSemantics.Mid()
            )

        # Every frame sees skip_defaults=True; every default-valued field
        # is dropped at every depth. Root.m == default => dropped entirely.
        assert diof.to_dict(Root(), skip_defaults=True) == {}

        # Non-default at the top, defaults below: nested defaults are dropped.
        r = Root(m=TestSkipDefaultsSemantics.Mid(x=5))
        assert diof.to_dict(r, skip_defaults=True) == {"m": {"x": 5}}

    # ---- skip_defaults at field level: DEEP_ONCE -------------------------

    def test_skip_defaults_field_level_applies_to_nested_frame_only(self):
        # FIELD/DEEP_ONCE: skip_defaults=True on Root.m means:
        #   - Root frame: NOT affected (skip_defaults doesn't apply here;
        #     the field's own skip_if_default is <NO_VALUE>).
        #   - Mid frame (one hop): skip_defaults=True applies to Mid's fields.
        #   - Leaf frame (two hops): skip_defaults expired; defaults emitted.
        @dcs.dataclass
        class Root:
            m: "TestSkipDefaultsSemantics.Mid" = dcs.field(
                default_factory=TestSkipDefaultsSemantics.Mid,
                metadata=FieldOptions(skip_defaults=True),
            )

        # Root.m == default but skip_if_default is unset on this field, and
        # skip_defaults is FIELD-scoped => it doesn't apply to *this* frame.
        # The Mid value is emitted, but inside Mid, x=0 and leaf=default are
        # both dropped (skip_defaults active in Mid frame). However, Leaf
        # itself would be dropped as a default of Mid... so result is {}.
        assert diof.to_dict(Root()) == {"m": {}}

        # Make Leaf non-default so it survives Mid's skipping, its default values
        #  (b) are kept
        r = Root(m=TestSkipDefaultsSemantics.Mid(leaf=TestSkipDefaultsSemantics.Leaf(a=1)))
        assert diof.to_dict(r) == {"m": {"leaf": {"a": 1, "b": 0}}}

    # ---- the headline distinction: both options on the same field --------

    def test_both_options_on_same_field_have_independent_meanings(self):
        """
        This is the case that motivates the LOCAL vs DEEP_ONCE split.

          - skip_if_default=False  : controls THIS frame -> always emit
                                     the field even if it equals its default.
          - skip_defaults=True     : controls the NESTED frame -> inside Mid,
                                     drop default-valued fields.
        """

        @dcs.dataclass
        class Root:
            m: "TestSkipDefaultsSemantics.Mid" = dcs.field(
                default_factory=lambda: TestSkipDefaultsSemantics.Mid(),
                metadata=FieldOptions(skip_if_default=False, skip_defaults=True),
            )

        # Root.m equals its default. skip_if_default=False => emit anyway.
        # Inside Mid: skip_defaults=True => drop x=0 and leaf=default.
        assert diof.to_dict(Root()) == {"m": {}}

    def test_both_options_inverse_case(self):
        # The flip side: skip THIS field if default, but inside its nested
        # frame, do NOT skip defaults.
        @dcs.dataclass
        class Root:
            m: "TestSkipDefaultsSemantics.Mid" = dcs.field(
                default_factory=lambda: TestSkipDefaultsSemantics.Mid(),
                metadata=FieldOptions(skip_if_default=True, skip_defaults=False),
            )
            sentinel: int = 1  # so the dict isn't empty in the default case

        # Root.m == default => dropped at Root frame.
        assert diof.to_dict(Root()) == {"sentinel": 1}

        # Non-default Mid: emitted, and inside Mid nothing is skipped
        # (skip_defaults=False explicitly).
        r = Root(m=TestSkipDefaultsSemantics.Mid(x=2))
        assert diof.to_dict(r) == {
            "m": {"x": 2, "leaf": {"a": 0, "b": 0}},
            "sentinel": 1,
        }

    # ---- precedence: skip_if_default wins over skip_defaults in-frame ----

    def test_skip_if_default_overrides_call_level_skip_defaults(self):
        # Per the semantics: skip_defaults only consults if skip_if_default
        # is <NO_VALUE>. Here skip_if_default=False explicitly.
        @dcs.dataclass
        class Root:
            x: int = dcs.field(default=0, metadata=FieldOptions(skip_if_default=False))
            y: int = 0

        # Call-site skip_defaults=True would normally drop both x and y.
        # But x has skip_if_default=False, which overrides => x kept, y dropped.
        assert diof.to_dict(Root(), skip_defaults=True) == {"x": 0}

    # ---- DEEP_ONCE expiration verified by depth --------------------------

    def test_field_level_skip_defaults_expires_after_one_hop(self):
        @dcs.dataclass
        class Deep:
            leaf: "TestSkipDefaultsSemantics.Leaf" = dcs.field(
                default_factory=lambda: TestSkipDefaultsSemantics.Leaf()
            )
            n: int = 0

        @dcs.dataclass
        class Root:
            d: Deep = dcs.field(
                default_factory=lambda: Deep(n=1),  # non-default so Deep survives
                metadata=FieldOptions(skip_defaults=True),
            )

        # Deep frame (1 hop): skip_defaults active => leaf=default dropped,
        #   n=1 kept (not default).
        # Leaf frame (2 hops): would be reached only if leaf weren't dropped;
        #   we verify expiration by making leaf non-default too.
        r = Root(d=Deep(leaf=TestSkipDefaultsSemantics.Leaf(a=2), n=1))
        # Deep frame: leaf is non-default => kept; n=1 kept.
        # Leaf frame: skip_defaults expired => b=0 (default) STILL emitted.
        assert diof.to_dict(r) == {"d": {"leaf": {"a": 2, "b": 0}, "n": 1}}

    # ---- call + field interaction: field-level DEEP_ONCE overlays CALL ---

    def test_field_skip_defaults_false_shields_one_level_from_call_true(self):
        # Call site says "skip defaults everywhere"; one field says
        # "but not in my immediate subtree (one level)".
        @dcs.dataclass
        class Root:
            m: "TestSkipDefaultsSemantics.Mid" = dcs.field(
                default_factory=lambda: TestSkipDefaultsSemantics.Mid(),
                metadata=FieldOptions(skip_defaults=False),
            )

        # Mid frame: field-level skip_defaults=False shadows call-level True.
        #   => leaf=default is KEPT inside Mid.
        # Leaf frame: DEEP_ONCE expired, call-level skip_defaults=True
        #   re-emerges => Leaf's defaults a=0, b=0 would be dropped.
        assert diof.to_dict(Root(TestSkipDefaultsSemantics.Mid(x=1)), skip_defaults=True) == {
            "m": {"x": 1, "leaf": {}}
        }
