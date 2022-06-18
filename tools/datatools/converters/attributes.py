import argparse
import os

from json import dumps, load
from pathlib import Path
from random import shuffle
from time import time
from typing import Any, Dict, List, Tuple

from .. import defaults
from ..finder import Finder
from ..logger import get_logger
from ..util import get_relpath, round_to_digits
from .base_converter import Converter, ConverterArgs

logger = get_logger()

# type aliases (with comments to reference values)
Bbox = List[float]
"""[Xmin, Ymin, Xmax, Ymax]"""
Point = Bbox
"""[X, Y]"""
Vehicle = Tuple[str, Bbox]
"""(type, Bbox)"""


class AttributesArgs(ConverterArgs):
    multiple: bool


def _is_point_in_rect(point: Point, rect: Bbox) -> bool:
    # point: [x, y]
    # rect: [xmin, ymin, xmax, ymax]
    return point[0] > rect[0] and \
        point[0] < rect[2] and \
        point[1] > rect[1] and \
        point[1] < rect[3]


class AttributesConverter(Converter):
    def __init__(self, args: AttributesArgs):
        super().__init__(Finder(args.input, args.prefix, args.data_extension), args)
        self.allow_multiple = args.multiple

        # output paths
        self.train_path = f"{self.output_path}/train.json"
        self.eval_path = f"{self.output_path}/test.json"

        # list of vehicles to put to final files
        self.vehicles: List[Dict[str, Any]] = []

        # parameters that might be needed in files but we are not changing
        #! these could be changed, but probably won't
        self.label: str = "vehicle"

    def _parse_shapes(self, shapes: List[Dict[str, Any]]) -> List[Tuple[str, Bbox, Bbox]]:
        vehicles, colors = self._sort_labels(shapes)
        # * pair vehicles with colors
        objects: List[Tuple[str, Bbox, Bbox]] = []
        for color in colors:
            color_center: Point = [(color[0] + color[2]) / 2,
                                   (color[1] + color[3]) / 2]
            for vehicle in vehicles:
                if _is_point_in_rect(color_center, vehicle[1]):
                    objects.append(vehicle + (color,))
                    break  # vehicle loop
        # * raise errors if something went wrong
        if len(objects) < 1:
            if len(colors) < 1:
                raise ValueError("No colors in annotation file")
            elif len(vehicles) < 1:
                raise ValueError("No vehicles in annotation file")
            else:
                raise ValueError(
                    "Centers of all color bboxes are not in any vehicle")
        elif len(objects) > 1 and not self.allow_multiple:
            raise ValueError(
                "Multiple objects in one annotation file is disabled")
        return objects

    def _sort_labels(self, shapes: List[Dict[str, Any]]) -> Tuple[List[Vehicle], List[Bbox]]:
        vehicles: List[Tuple[str, Bbox]] = []
        colors: List[Bbox] = []
        for shape in shapes:
            if shape["label"] == "vehicle":
                vehicles.append((
                    self._type_from_flags(shape, self.vehicle_types),
                    self._parse_bbox(shape)
                ))
            elif shape["label"] == "color":
                colors.append(self._parse_bbox(shape, round_digits=0))
            else:
                raise ValueError("Unknown label")
        return (vehicles, colors)

    def _parse_bbox(self, shape: Dict[str, Any], round_digits=1) -> Bbox:
        bbox = shape["points"][0] + shape["points"][1]
        for i in range(len(bbox)):
            bbox[i] = round_to_digits(bbox[i], round_digits)
        # change bbox to format Xmin, Ymin, Xmax, Ymax
        bbox[0], bbox[2] = min(bbox[0], bbox[2]), max(bbox[0], bbox[2])
        bbox[1], bbox[3] = min(bbox[1], bbox[3]), max(bbox[1], bbox[3])
        return bbox

    def convert_file(self, path: str) -> Dict[str, Any]:
        with open(path) as file:
            old: Dict[str, Any] = load(file)
        if not self._is_annotation_file(old):
            raise ValueError("Not in labelme format")
        new: Dict[str, Any] = {}
        objects = self._parse_shapes(old["shapes"])
        new["objects"] = [{
            "label": self.label,
            "attributes": {
                "type": veh_type,
                "color_bbox": [color_bbox],
            },
            "bbox": obj_bbox
        } for veh_type, obj_bbox, color_bbox in objects]
        path_to_img = os.path.join(Path(path).parent, old["imagePath"])
        new["image"] = os.path.abspath(path_to_img) if self.absolute_paths \
            else get_relpath(self.exec_path, path_to_img)
        return new

    def convert(self) -> None:
        self._handle_files_exist([self.train_path, self.eval_path])
        start = time()
        read_files = 0
        converted_files = 0
        # * convert loop
        for path in self.finder.find_all():
            try:
                self.vehicles.append(self.convert_file(path))
                converted_files += 1
            except ValueError as e:
                logger.warning(f"Bad format, skipping {path} ({e})")
            read_files += 1
        # * write files
        shuffle(self.vehicles)
        if self.dedic_eval_path is None:
            split_num = int(len(self.vehicles) * self.eval_percent / 100)
            with open(self.train_path, "w") as train_file:
                train_file.write(dumps(self.vehicles[split_num:],
                                       separators=(",", ":")))
            with open(self.eval_path, "w") as test_file:
                test_file.write(dumps(self.vehicles[:split_num],
                                      separators=(",", ":")))
        else:
            logger.warning("This feature was not tested yet, be careful!")
            with open(self.train_path, "w") as train_file:
                train_file.write(dumps(self.vehicles, separators=(",", ":")))
            # we need to convert eval_path to config.json
            eval_vehicles: List[Dict[str, Any]] = []
            for eval_path in Finder(self.dedic_eval_path, "", "json").find_all():
                try:
                    eval_vehicles.append(self.convert_file(eval_path))
                except ValueError as e:
                    logger.warning(f"Bad format, skipping {eval_path} ({e})")
            shuffle(eval_vehicles)
            with open(self.eval_path, "w") as eval_file:
                eval_file.write(dumps(eval_vehicles, separators=(",", ":")))
        logger.success(
            f"Converted {converted_files} files ({read_files} read) in {round_to_digits(time() - start, 6)} s")

    @classmethod
    def add_parser_arguments(cls, parser: argparse.ArgumentParser):
        super().add_parser_arguments(parser)
        parser.add_argument("--multiple", action="store_const",
                            const=not defaults.ATTR_MULTIPLE, default=defaults.ATTR_MULTIPLE,
                            help="Whether to skip files with multiple vehicles")
