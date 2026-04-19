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

    @classmethod
    def manual_from_dict(cls, dikt):
        """Deserialize a CocoInfo instance from a dictionary."""
        kw = {}
        if "year" in dikt:
            kw["year"] = dikt["year"]
        if "version" in dikt:
            kw["version"] = dikt["version"]
        if "description" in dikt:
            kw["description"] = dikt["description"]
        if "contributor" in dikt:
            kw["contributor"] = dikt["contributor"]
        if "url" in dikt:
            kw["url"] = dikt["url"]
        if "date_created" in dikt:
            kw["date_created"] = dikt["date_created"]
        inst = cls(**kw)
        return inst


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

    @classmethod
    def manual_from_dict(cls, dikt):
        """Deserialize a CocoImage instance from a dictionary."""
        kw = {}
        try:
            kw["id"] = dikt["id"]
        except KeyError as exc:
            raise KeyError(
                f"'id' is a required attribute for CocoImage, but was missing from {dikt=}."
            ) from exc
        try:
            kw["file_name"] = dikt["file_name"]
        except KeyError as exc:
            raise KeyError(
                f"'file_name' is a required attribute for CocoImage, but was missing from {dikt=}."
            ) from exc
        if "width" in dikt:
            kw["width"] = dikt["width"]
        if "height" in dikt:
            kw["height"] = dikt["height"]
        if "license" in dikt:
            kw["license"] = dikt["license"]
        if "flickr_url" in dikt:
            kw["flickr_url"] = dikt["flickr_url"]
        if "coco_url" in dikt:
            kw["coco_url"] = dikt["coco_url"]
        if "date_captured" in dikt:
            kw["date_captured"] = dikt["date_captured"]
        inst = cls(**kw)
        return inst


@dataclass
class CocoLicense(IOMixin):
    id: int
    name: str
    url: tp.Optional[str] = None

    @classmethod
    def manual_from_dict(cls, dikt):
        """Deserialize a CocoLicense instance from a dictionary."""
        kw = {}
        try:
            kw["id"] = dikt["id"]
        except KeyError as exc:
            raise KeyError(
                f"'id' is a required attribute for CocoLicense, but was missing from {dikt=}."
            ) from exc
        try:
            kw["name"] = dikt["name"]
        except KeyError as exc:
            raise KeyError(
                f"'name' is a required attribute for CocoLicense, but was missing from {dikt=}."
            ) from exc
        if "url" in dikt:
            kw["url"] = dikt["url"]
        inst = cls(**kw)
        return inst


@dataclass
class CocoCategory(IOMixin):
    id: int
    name: str
    supercategory: tp.Optional[str] = None

    @classmethod
    def manual_from_dict(cls, dikt):
        """Deserialize a CocoCategory instance from a dictionary."""
        kw = {}
        try:
            kw["id"] = dikt["id"]
        except KeyError as exc:
            raise KeyError(
                f"'id' is a required attribute for CocoCategory, but was missing from {dikt=}."
            ) from exc
        try:
            kw["name"] = dikt["name"]
        except KeyError as exc:
            raise KeyError(
                f"'name' is a required attribute for CocoCategory, but was missing from {dikt=}."
            ) from exc
        if "supercategory" in dikt:
            kw["supercategory"] = dikt["supercategory"]
        inst = cls(**kw)
        return inst


@dataclass
class CocoAnnotation(IOMixin):
    id: int
    image_id: int
    category_id: int
    bbox: list[int | float]
    area: tp.Optional[float] = None
    iscrowd: int = 0
    segmentation: tp.Optional[tp.Any] = None

    @classmethod
    def manual_from_dict(cls, dikt):
        """Deserialize a CocoAnnotation instance from a dictionary."""
        kw = {}

        try:
            kw["id"] = dikt["id"]
        except KeyError as exc:
            raise KeyError(
                f"'id' is a required attribute for CocoAnnotation, but was missing from {dikt=}."
            ) from exc

        try:
            kw["image_id"] = dikt["image_id"]
        except KeyError as exc:
            raise KeyError(
                f"'image_id' is a required attribute for CocoAnnotation, but was missing from {dikt=}."
            ) from exc

        try:
            kw["category_id"] = dikt["category_id"]
        except KeyError as exc:
            raise KeyError(
                f"'category_id' is a required attribute for CocoAnnotation, but was missing from {dikt=}."
            ) from exc

        try:
            kw["bbox"] = dikt["bbox"]
        except KeyError as exc:
            raise KeyError(
                f"'bbox' is a required attribute for CocoAnnotation, but was missing from {dikt=}."
            ) from exc

        if "area" in dikt:
            kw["area"] = dikt["area"]
        if "iscrowd" in dikt:
            kw["iscrowd"] = dikt["iscrowd"]
        if "segmentation" in dikt:
            kw["segmentation"] = dikt["segmentation"]
        inst = cls(**kw)
        return inst


@dataclass
class Coco(IOMixin):
    info: CocoInfo = field(default_factory=CocoInfo)
    images: list[CocoImage] = field(default_factory=list)
    annotations: list[CocoAnnotation] = field(default_factory=list)
    categories: list[CocoCategory] = field(default_factory=list)
    licenses: list[CocoLicense] = field(default_factory=list)

    @classmethod
    def manual_from_dict(cls, dikt):
        """Deserialize a Coco instance from a dictionary."""
        kw = {}
        if "info" in dikt:
            kw["info"] = CocoInfo.manual_from_dict(dikt["info"])
        if "images" in dikt:
            kw["images"] = [CocoImage.manual_from_dict(d) for d in dikt["images"]]
        if "annotations" in dikt:
            kw["annotations"] = [CocoAnnotation.manual_from_dict(d) for d in dikt["annotations"]]
        if "categories" in dikt:
            kw["categories"] = [CocoCategory.manual_from_dict(d) for d in dikt["categories"]]
        if "licenses" in dikt:
            kw["licenses"] = [CocoLicense.manual_from_dict(d) for d in dikt["licenses"]]
        inst = cls(**kw)
        return inst


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
