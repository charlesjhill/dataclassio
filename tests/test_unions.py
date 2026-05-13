import dataclasses as dcs
import typing as tp

import pytest

from dataclassio import IOMixin
from dataclassio.config import FieldOpts


@dcs.dataclass
class HumanAnnotator:
    id: str
    type: tp.Literal["human_annotator", "human"] = "human_annotator"
    team: str | None = None


@dcs.dataclass
class MachineAnnotator:
    id: str
    type: tp.Literal["machine_annotator"] = "machine_annotator"
    algorithm_type: str | None = None


@dcs.dataclass
class AdminAnnotator:
    id: str
    type: tp.Literal["admin_annotator"] = "admin_annotator"
    level: int = 1


@dcs.dataclass
class Dataset(IOMixin):
    annotators: list[HumanAnnotator | MachineAnnotator | AdminAnnotator] = dcs.field(
        default_factory=list, metadata=FieldOpts(discriminator="type")
    )


class TestDiscriminatedUnions:
    def test_multiple_key_support(self):
        payload = {
            "annotators": [
                {"id": "John Smith", "type": "human_annotator", "team": "ACME Corp"},
                {"id": "Jane Doe", "type": "human", "team": "ACME Corp South"},
            ]
        }

        ds = Dataset.from_dict(payload)

        assert len(ds.annotators) == 2
        assert isinstance(ds.annotators[0], HumanAnnotator)
        assert ds.annotators[0].id == "John Smith"
        assert ds.annotators[0].team == "ACME Corp"

        assert isinstance(ds.annotators[1], HumanAnnotator)
        assert ds.annotators[1].id == "Jane Doe"
        assert ds.annotators[1].team == "ACME Corp South"

    def test_basic_union_deserialization(self):
        """Verify that a list with multiple types is correctly partitioned."""
        payload = {
            "annotators": [
                {"id": "John Smith", "type": "human_annotator", "team": "ACME Corp"},
                {"id": "COCO-Net", "type": "machine_annotator", "algorithm_type": "ResNet"},
            ]
        }

        ds = Dataset.from_dict(payload)

        assert len(ds.annotators) == 2
        assert isinstance(ds.annotators[0], HumanAnnotator)
        assert ds.annotators[0].id == "John Smith"
        assert ds.annotators[0].team == "ACME Corp"

        assert isinstance(ds.annotators[1], MachineAnnotator)
        assert ds.annotators[1].id == "COCO-Net"
        assert ds.annotators[1].algorithm_type == "ResNet"

    def test_multi_member_union_support(self):
        """Ensure more than two union members (e.g., 3) work as expected."""
        payload = {"annotators": [{"id": "A1", "type": "admin_annotator", "level": 5}]}
        ds = Dataset.from_dict(payload)
        assert isinstance(ds.annotators[0], AdminAnnotator)
        assert ds.annotators[0].level == 5

    def test_missing_discriminator_field(self):
        """Verify behavior when the required discriminator key is missing from the dictionary."""
        payload = {"annotators": [{"id": "Incomplete", "team": "MissingType"}]}
        # The generator should explicitly check for the discriminator
        with pytest.raises(KeyError):
            Dataset.from_dict(payload)

    def test_invalid_discriminator_value(self):
        """Verify behavior when the discriminator value doesn't match any Literal."""
        payload = {"annotators": [{"id": "Ghost", "type": "alien_annotator"}]}
        # Since 'type' is used to resolve the class, an unknown value should fail
        with pytest.raises(KeyError, match="alien_annotator"):
            Dataset.from_dict(payload)

    def test_round_trip_serialization(self):
        """Ensure to_dict produces a dictionary that can be re-parsed into the same union."""
        original = Dataset(
            annotators=[
                HumanAnnotator(id="H1", team="A-Team"),
                MachineAnnotator(id="M1", algorithm_type="YOLO"),
            ]
        )

        exported = original.to_dict()

        # Verify the 'type' field is correctly exported to enable the round-trip
        assert exported["annotators"][0]["type"] == "human_annotator"
        assert exported["annotators"][1]["type"] == "machine_annotator"

        # Round trip
        recovered = Dataset.from_dict(exported)
        assert recovered == original
