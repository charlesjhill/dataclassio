from dataclasses import dataclass, field

import typing_extensions as tp

from dataclass_io.io_mixin import IOMixin


@dataclass
class CocoInfo(IOMixin):
    year: tp.Optional[int] = None
    version: tp.Optional[str] = None
    description: tp.Optional[str] = None
    contributor: tp.Optional[str] = None
    url: tp.Optional[str] = None
    date_created: tp.Optional[str] = None


@dataclass
class CocoImage(IOMixin):
    id: int
    file_name: str
    width: tp.Optional[int] = None
    height: tp.Optional[int] = None
    license: tp.Optional[int] = None
    flickr_url: tp.Optional[str] = None
    coco_url: tp.Optional[str] = None
    date_captured: tp.Optional[str] = None


@dataclass
class CocoLicense(IOMixin):
    id: int
    name: str
    url: tp.Optional[str] = None


@dataclass
class CocoCategory(IOMixin):
    id: int
    name: str
    supercategory: tp.Optional[str] = None


@dataclass
class CocoAnnotation(IOMixin):
    id: int
    image_id: int
    category_id: int
    bbox: list[float]
    area: tp.Optional[float] = None
    iscrowd: int = 0
    segmentation: tp.Optional[tp.Any] = None


@dataclass
class Coco(IOMixin):
    info: CocoInfo = field(default_factory=CocoInfo)
    images: list[CocoImage] = field(default_factory=list)
    annotations: list[CocoAnnotation] = field(default_factory=list)
    categories: list[CocoCategory] = field(default_factory=list)
    licenses: list[CocoLicense] = field(default_factory=list)


@dataclass
class Address(IOMixin):
    city: str
    zip_code: tp.Optional[str] = None


@dataclass
class User(IOMixin):
    id: int
    name: str
    is_admin: bool = False
    address: tp.Optional[Address] = None


@dataclass
class TinyRow(IOMixin):
    id: int
    name: str


@dataclass
class TinyTable(IOMixin):
    id: int
    fks: list[TinyRow] = field(default_factory=list)
