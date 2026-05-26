"""Module with example schemas for testing or demonstrations."""

import enum
from dataclasses import InitVar, dataclass, field

import typing_extensions as tp

from dataclassio.io_mixin import IOMixin


@dataclass
class CocoInfo(IOMixin):
    year: int | None = None
    version: str | None = None
    description: str | None = None
    contributor: str | None = None
    url: str | None = None
    date_created: str | None = None

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
        return cls(**kw)

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
    width: int | None = None
    height: int | None = None
    license: int | None = None
    flickr_url: str | None = None
    coco_url: str | None = None
    date_captured: str | None = None

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
        return cls(**kw)

    @classmethod
    def fast_from_dict(cls, dikt):
        """Deserialize a CocoImage instance from a dictionary."""
        try:
            v_id = dikt["id"]
        except KeyError as exc:
            raise KeyError(
                f"'id' is a required attribute for CocoImage, but was missing from {dikt=}."
            ) from exc

        try:
            v_file_name = dikt["file_name"]
        except KeyError as exc:
            raise KeyError(
                f"'file_name' is a required attribute for CocoImage, but was missing from {dikt=}."
            ) from exc

        v_width = dikt.get("width", None)
        v_height = dikt.get("height", None)
        v_license = dikt.get("license", None)
        v_flickr_url = dikt.get("flickr_url", None)
        v_coco_url = dikt.get("coco_url", None)
        v_date = dikt.get("date_captured", None)

        return cls(
            v_id, v_file_name, v_width, v_height, v_license, v_flickr_url, v_coco_url, v_date
        )

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
    url: str | None = None

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
        return cls(**kw)

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
    supercategory: str | None = None

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
        return cls(**kw)

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
    area: float | None = None
    iscrowd: int = 0
    segmentation: tp.Any | None = None

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
                "'image_id' is a required attribute for CocoAnnotation, but was "
                f"missing from {dikt=}."
            ) from exc

        try:
            kw["category_id"] = dikt["category_id"]
        except KeyError as exc:
            raise KeyError(
                "'category_id' is a required attribute for CocoAnnotation, but "
                f"was missing from {dikt=}."
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
        return cls(**kw)

    @classmethod
    def fast_from_dict(cls, dikt):
        """Deserialize a CocoAnnotation instance from a dictionary."""
        try:
            v_id = dikt["id"]
        except KeyError as exc:
            raise KeyError(
                f"'id' is a required attribute for CocoAnnotation, but was missing from {dikt=}."
            ) from exc

        try:
            v_image_id = dikt["image_id"]
        except KeyError as exc:
            raise KeyError(
                "'image_id' is a required attribute for CocoAnnotation, but was "
                f" missing from {dikt=}."
            ) from exc

        try:
            v_category_id = dikt["category_id"]
        except KeyError as exc:
            raise KeyError(
                "'category_id' is a required attribute for CocoAnnotation, but was "
                f" missing from {dikt=}."
            ) from exc

        try:
            v_bbox = dikt["bbox"]
        except KeyError as exc:
            raise KeyError(
                f"'bbox' is a required attribute for CocoAnnotation, but was missing from {dikt=}."
            ) from exc

        v_area = dikt.get("area", None)
        v_iscrowd = dikt.get("iscrowd", 0)
        v_segmentation = dikt.get("segmentation", None)

        return cls(v_id, v_image_id, v_category_id, v_bbox, v_area, v_iscrowd, v_segmentation)

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
            dikt.update(self.extra_fields)
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

    def __repr__(self) -> str:
        n_images = len(self.images)
        n_anns = len(self.annotations)
        n_cats = len(self.categories)
        return f"<Coco images={n_images} annotations={n_anns} categories={n_cats}>"

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
        return cls(**kw)

    @classmethod
    def fast_from_dict(
        cls,
        dikt,
        _cinfo=CocoInfo.from_dict,
        _cinfo_cls=CocoInfo,
        _cimage=CocoImage.fast_from_dict,
        _cannot=CocoAnnotation.fast_from_dict,
        _ccategory=CocoCategory.from_dict,
        _clic=CocoLicense.from_dict,
    ):
        c_info = _cinfo(dikt["info"]) if "info" in dikt else _cinfo_cls()
        c_images = [_cimage(d) for d in dikt["images"]] if "images" in dikt else []
        c_annotations = [_cannot(d) for d in dikt["annotations"]] if "annotations" in dikt else []
        c_categories = [_ccategory(d) for d in dikt["categories"]] if "categories" in dikt else []
        c_licences = [_clic(d) for d in dikt["licenses"]] if "licenses" in dikt else []

        return cls(c_info, c_images, c_annotations, c_categories, c_licences)

    def manual_to_dict(self, skip_defaults=False):
        """Serialize a Coco instance into a dictionary."""
        if skip_defaults:
            dikt = {}
            if (v := CocoInfo.manual_to_dict(self.info, skip_defaults=True)) != CocoInfo():
                dikt["info"] = v
            if v := [CocoImage.manual_to_dict(d, skip_defaults=True) for d in self.images]:
                dikt["images"] = v
            if v := [
                CocoAnnotation.manual_to_dict(d, skip_defaults=True) for d in self.annotations
            ]:
                dikt["annotations"] = v
            if v := [CocoCategory.manual_to_dict(d, skip_defaults=True) for d in self.categories]:
                dikt["categories"] = v
            if v := [CocoLicense.manual_to_dict(d, skip_defaults=True) for d in self.licenses]:
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
    zip_code: str | None = None


@dataclass
class User(IOMixin):
    id: int
    name: str
    is_admin: bool = False
    address: Address | None = None
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
        super().__post_init__()


@dataclass
class InitFalseDC(IOMixin):
    a: float
    b: float
    c: float = field(init=False)

    def __post_init__(self):
        self.c = self.a + self.b
        super().__post_init__()


class Role(enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


@dataclass
class Team(IOMixin):
    team_name: str
    access_level: Role
