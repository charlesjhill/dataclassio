import json
import sys
from pathlib import Path

import msgspec
from pybench import Bench

import dataclassio._example_schemas as sch

sys.path.append("..")

from coco_model import CocoDW, CocoMashumaro, CocoMsgSpec, CocoPyd


def load_coco_dict() -> dict:
    pth = (__file__ / Path("../../test_data/instances_val2017.json")).resolve()

    with pth.open("rb") as fp:
        return json.load(fp)


loaders = Bench("coco_comparsion")


coco_data = load_coco_dict()


@loaders.bench(name="dataclassio", baseline=True)
def test_dio():
    return sch.Coco.from_dict(coco_data)


@loaders.bench(name="dio_fast")
def test_locals():
    return sch.Coco.fast_from_dict(coco_data)


@loaders.bench(name="pydantic")
def test_pyd():
    return CocoPyd.model_validate(coco_data)


@loaders.bench(name="msgspec_into_dataclass")
def test_msgspec_into_dataclass():
    return msgspec.convert(coco_data, sch.Coco)


@loaders.bench(name="msgspec_into_native")
def test_msgspec_into_native():
    return msgspec.convert(coco_data, CocoMsgSpec)


@loaders.bench(name="mashumaro")
def test_mashumaro():
    return CocoMashumaro.from_dict(coco_data)


@loaders.bench(name="dataclass-wizard")
def test_dw():
    return CocoDW.from_dict(coco_data)
