import dataclasses as dcs
import sys
from pathlib import Path

import msgspec
from pybench import Bench, BenchContext

import dataclassio._example_schemas as sch

sys.path.append("..")

from coco_model import CocoDW, CocoMashumaro, CocoMsgSpec, CocoPyd


def load_coco_obj() -> tuple[sch.Coco, bytes]:
    pth = (__file__ / Path("../../test_data/instances_val2017.json")).resolve()

    with pth.open("rb") as fp:
        buf = fp.read()
    return msgspec.json.decode(buf, type=sch.Coco), buf


loaders = Bench("coco_to_dict")

obj, bytestring = load_coco_obj()
literal = msgspec.json.decode(bytestring)
pyd_obj = CocoPyd.model_validate_json(bytestring)
msg_obj = msgspec.json.decode(bytestring, type=CocoMsgSpec)
mash_obj = CocoMashumaro.from_dict(literal)
dw_obj = CocoDW.from_dict(literal)


@loaders.bench(name="dataclassio", baseline=True)
def test_dio(b: BenchContext):
    b.start()
    obj.to_dict()
    b.end()


@loaders.bench(name="native")
def test_native(b: BenchContext):
    b.start()
    dcs.asdict(obj)
    b.end()


@loaders.bench(name="pydantic")
def test_pyd(b: BenchContext):
    b.start()
    pyd_obj.model_dump()
    b.end()


@loaders.bench(name="msgspec_from_dataclass")
def test_msgspec_from_dataclass(b: BenchContext):
    b.start()
    msgspec.to_builtins(obj)
    b.end()


@loaders.bench(name="msgspec_from_struct")
def test_msgspec_from_struct(b: BenchContext):
    b.start()
    msgspec.to_builtins(msg_obj)
    b.end()


@loaders.bench(name="mashumaro")
def test_mashumaro(b: BenchContext):
    b.start()
    mash_obj.to_dict()
    b.end()


@loaders.bench(name="dataclass-wizard")
def test_dw(b: BenchContext):
    b.start()
    dw_obj.to_dict()
    b.end()
