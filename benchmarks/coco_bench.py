from pathlib import Path

import msgspec
from pybench import Bench, BenchContext

import dataclassio._example_schemas as sch
from dataclassio.types import EFS


def load_coco_dict() -> dict:
    pth = (__file__ / Path("../../test_data/instances_val2017.json")).resolve()

    with pth.open("rb") as fp:
        buf = fp.read()
    return msgspec.json.decode(buf)


loaders = Bench("coco_roundtrip")

coco_data = load_coco_dict()


@loaders.bench(group="from_dict", name="from_dict_ignore")
def test_dio():
    sch.Coco.from_dict(coco_data)


@loaders.bench(group="from_dict", name="from_dict_strict")
def test_dio_strict():
    sch.Coco.from_dict(coco_data, extra_field_strategy=EFS.STRICT)


@loaders.bench(group="from_dict", name="from_dict_capture")
def test_dio_capture():
    sch.Coco.from_dict(coco_data, extra_field_strategy=EFS.CAPTURE)


@loaders.bench(group="to_dict", name="to_dict_no_skip")
def test_dio_to(b: BenchContext):
    obj = sch.Coco.from_dict(coco_data)
    b.start()
    obj.to_dict(skip_if_default=False)
    b.end()


@loaders.bench(group="to_dict", name="to_dict_skip_defaults")
def test_dio_to_skip(b: BenchContext):
    obj = sch.Coco.from_dict(coco_data)
    b.start()
    obj.to_dict(skip_if_default=True)
    b.end()
