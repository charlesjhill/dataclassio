from dataclasses import dataclass

import typing_extensions as tp

from .io_mixin import IOMixin


@dataclass
class Coco(IOMixin):
    info: "CocoInfo"
    images: list["CocoImage"]
    annotations: list["CocoAnnotation"]
    categories: list["CocoCategory"]
    licenses: list["CocoLicense"]


@dataclass
class CocoInfo(IOMixin):
    year: int
    version: str
    description: str
    contributor: str
    url: str
    date_created: str


@dataclass
class CocoImage(IOMixin):
    id: int
    width: int
    height: int
    file_name: str
    license: int
    flickr_url: str
    coco_url: str
    date_captured: str


@dataclass
class CocoLicense(IOMixin):
    id: int
    name: str
    url: str


@dataclass
class CocoCategory(IOMixin):
    id: int
    name: str
    supercategory: str


@dataclass
class CocoAnnotation(IOMixin):
    id: int
    image_id: int
    category_id: int
    segmentation: tp.Any
    area: float
    bbox: list[float]
    iscrowd: int
