"""Module with example schemas for testing or demonstrations."""

from dataclasses import InitVar, dataclass, field

import typing_extensions as tp

from dataclassio.io_mixin import IOMixin


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

    def manual_to_dict(self, skip_defaults=False):
        """Serialize a CocoInfo instance into a dictionary."""
        if skip_defaults:
            dikt = {}
            if (v := self.year) is not None:
                dikt["year"] = v
            if (v := self.version) is not None:
                dikt["version"] = v
            if (v := self.description) is not None:
                dikt["description"] = v
            if (v := self.contributor) is not None:
                dikt["contributor"] = v
            if (v := self.url) is not None:
                dikt["url"] = v
            if (v := self.date_created) is not None:
                dikt["date_created"] = v
            dikt.update(self.extra_fields)
        else:
            dikt = {
                "year": self.year,
                "version": self.version,
                "description": self.description,
                "contributor": self.contributor,
                "url": self.url,
                "date_created": self.date_created,
                **self.extra_fields,
            }
        return dikt


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

    def manual_to_dict(self, skip_defaults=False):
        """Serialize a CocoImage instance into a dictionary."""
        if skip_defaults:
            dikt = {
                "id": self.id,
                "file_name": self.file_name,
            }
            if (v := self.width) is not None:
                dikt["width"] = v
            if (v := self.height) is not None:
                dikt["height"] = v
            if (v := self.license) is not None:
                dikt["license"] = v
            if (v := self.flickr_url) is not None:
                dikt["flickr_url"] = v
            if (v := self.coco_url) is not None:
                dikt["coco_url"] = v
            if (v := self.date_captured) is not None:
                dikt["date_captured"] = v
            dikt.update(self.extra_fields)
        else:
            dikt = {
                "id": self.id,
                "file_name": self.file_name,
                "width": self.width,
                "height": self.height,
                "license": self.license,
                "flickr_url": self.flickr_url,
                "coco_url": self.coco_url,
                "date_captured": self.date_captured,
                **self.extra_fields,
            }
        return dikt


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

    def manual_to_dict(self, skip_defaults=False):
        """Serialize a CocoLicense instance into a dictionary."""
        if skip_defaults:
            dikt = {
                "id": self.id,
                "name": self.name,
            }
            if (v := self.url) is not None:
                dikt["url"] = v
            dikt.update(self.extra_fields)
        else:
            dikt = {
                "id": self.id,
                "name": self.name,
                "url": self.url,
                **self.extra_fields,
            }
        return dikt


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

    def manual_to_dict(self, skip_defaults=False):
        """Serialize a CocoCategory instance into a dictionary."""
        if skip_defaults:
            dikt = {
                "id": self.id,
                "name": self.name,
            }
            if (v := self.supercategory) is not None:
                dikt["supercategory"] = v
            dikt.update(self.extra_fields)
        else:
            dikt = {
                "id": self.id,
                "name": self.name,
                "supercategory": self.supercategory,
                **self.extra_fields,
            }
        return dikt


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

    def manual_to_dict(self, skip_defaults=False):
        """Serialize a CocoAnnotation instance into a dictionary."""
        if skip_defaults:
            dikt = {
                "id": self.id,
                "image_id": self.image_id,
                "category_id": self.category_id,
                "bbox": self.bbox,
            }
            if (v := self.area) is not None:
                dikt["area"] = v
            if (v := self.iscrowd) != 0:
                dikt["iscrowd"] = v
            if (v := self.segmentation) is not None:
                dikt["segmentation"] = v
            dikt.update(getattr(self, "_extra_fields", {}))
        else:
            dikt = {
                "id": self.id,
                "image_id": self.image_id,
                "category_id": self.category_id,
                "bbox": self.bbox,
                "area": self.area,
                "iscrowd": self.iscrowd,
                "segmentation": self.segmentation,
                **self.extra_fields,
            }
        return dikt


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

    def manual_to_dict(self, skip_defaults=False):
        """Serialize a Coco instance into a dictionary."""
        if skip_defaults:
            dikt = {}
            if (v := CocoInfo.manual_to_dict(self.info)) != CocoInfo():
                dikt["info"] = v
            if v := [CocoImage.manual_to_dict(d) for d in self.images]:
                dikt["images"] = v
            if v := [CocoAnnotation.manual_to_dict(d) for d in self.annotations]:
                dikt["annotations"] = v
            if v := [CocoCategory.manual_to_dict(d) for d in self.categories]:
                dikt["categories"] = v
            if v := [CocoLicense.manual_to_dict(d) for d in self.licenses]:
                dikt["licenses"] = v
            dikt.update(self.extra_fields)
        else:
            dikt = {
                "info": CocoInfo.manual_to_dict(self.info),
                "images": [CocoImage.manual_to_dict(d) for d in self.images],
                "annotations": [CocoAnnotation.manual_to_dict(d) for d in self.annotations],
                "categories": [CocoCategory.manual_to_dict(d) for d in self.categories],
                "licenses": [CocoLicense.manual_to_dict(d) for d in self.licenses],
                **self.extra_fields,
            }

        return dikt


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
    named_addresses: dict[str, Address] = field(default_factory=dict)


@dataclass
class TinyRow(IOMixin):
    id: int
    name: str
    metadata: dict = field(default_factory=dict)
    data: list = field(default_factory=list)


@dataclass
class TinyTable(IOMixin):
    id: int
    rows: list[TinyRow] = field(default_factory=list)


@dataclass
class Metric(IOMixin):
    value: float
    unit: str


@dataclass
class Dashboard(IOMixin):
    title: str
    data_points: dict[str, list[Metric | None]]


@dataclass
class MaybeMetric(IOMixin):
    metric: Metric | None


@dataclass
class ImputedMetric(IOMixin):
    unit: InitVar[str]
    value: InitVar[float] = 5.0
    metric: Metric = field(init=False)

    def __post_init__(self, unit, value):
        self.metric = Metric(value, unit)
        return super().__post_init__()


@dataclass
class InitFalseDC(IOMixin):
    a: float
    b: float
    c: float = field(init=False)

    def __post_init__(self):
        self.c = self.a + self.b
        return super().__post_init__()
