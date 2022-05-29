import argparse
import os

from json import load
from pathlib import Path
from random import shuffle
from typing import Any, Dict, List, Tuple, Union

from .. import defaults
from ..finder import Finder
from ..logger import get_logger
from ..util import get_relpath
from .base_converter import Converter, ConverterArgs
from .export_yolov4_config import get_yolo_config

logger = get_logger()


class YoloArgs(ConverterArgs):
    backup: str
    batch_size: int
    subdivisions: int
    height: int
    width: int


class YoloConverter(Converter):
    def __init__(self, args: YoloArgs):
        super().__init__(Finder(args.input, args.prefix, args.data_extension), args)

        # output files
        self.config_path = f"{self.output_path}/yolov4.cfg"
        self.data_path = f"{self.output_path}/obj.data"
        self.train_path = f"{self.output_path}/train.txt"
        self.eval_path = f"{self.output_path}/test.txt"
        self.names_path = f"{self.output_path}/names.txt"
        self.backup_path = args.backup

        # object classes
        self.classes: Dict[str, int] = {}
        for index, name in enumerate(self.vehicle_types):
            self.classes[name] = index
        # if path already exists, we may have a BIG problem
        if os.path.isfile(self.names_path):
            with open(self.names_path, "r") as names_file:
                if not self._are_existing_names_same(names_file.read()):
                    if input("A different names file already exists. A different learning process might be taking place.\n" +
                             "Do you REALLY want to proceed? (Y/n): ").lower() != "y":
                        raise FileExistsError("Different names already exists")
        # sort classes based off index (to write them later)
        # currently doesn't affect anything
        # * self.classes = dict(sorted(self.classes.items(), key=lambda item: item[1]))

        # network config
        self.batch_size = args.batch_size
        self.subdivisions = args.subdivisions
        self.height = args.height
        self.width = args.width

    def _are_existing_names_same(self, existing: str):
        old = existing.rstrip().split("\n")
        if (len(old) != len(self.classes.keys())):
            return False
        for index, name in enumerate(self.classes.keys()):
            if old[index] != name:
                return False
        del old
        return True

    def _get_data_path(self, path):
        return os.path.abspath(path) if self.absolute_paths else get_relpath(self.exec_path, path)

    def _get_vehicle_class(self, shape: Dict[str, Any]) -> Union[int, None]:
        if (shape["label"] == "vehicle"):
            return self.classes[self._type_from_flags(shape, self.vehicle_types)]
        else:
            return None

    def _parse_bbox(self, shape: Dict[str, Any], height: int, width: int) -> Tuple[float, float, float, float]:
        # x y x y
        bbox: List[float] = shape["points"][0] + shape["points"][1]
        # center of bbox relative to dimensions
        center_x = (bbox[0] + bbox[2]) / 2 / width
        center_y = (bbox[1] + bbox[3]) / 2 / height
        # length of bbox relativeto dimensions
        length_x = abs(bbox[0] - bbox[2]) / width
        length_y = abs(bbox[1] - bbox[3]) / height
        return (center_x, center_y, length_x, length_y)

    def _get_config(self):
        return get_yolo_config(len(self.classes), self.batch_size, self.subdivisions, self.height, self.width)

    def convert_file(self, path: str):
        with open(path) as file:
            old: Dict[str, Any] = load(file)
        if not self._is_annotation_file(old):
            raise ValueError("Not in labelme format")
        new: List[str] = []
        height: int = old["imageHeight"]
        width: int = old["imageWidth"]
        for shape in old["shapes"]:
            class_id = self._get_vehicle_class(shape)
            if class_id is not None:
                new.append(f"{class_id}" + " " +
                           " ".join([str(value) for value in self._parse_bbox(shape, height, width)]))

        output_path = os.path.join(
            Path(path).parent, old['imagePath']).rsplit('.', 1)[0] + ".txt"
        with open(output_path, "w") as file:
            file.write("\n".join(new))

    def convert(self) -> None:
        self._handle_files_exist([self.data_path, self.config_path,
                                  self.train_path, self.eval_path])
        # * convert loop
        for path in self.finder.find_all():
            try:
                self.convert_file(path)
            except ValueError as e:
                logger.warning(f"Bad format, skipping {path} ({e})")
        # * write config files
        # * obj.data
        with open(self.data_path, "w") as data_file:
            data_file.write("\n".join([
                f"classes={len(self.classes)}",
                f"train={self._get_data_path(self.train_path)}",
                f"valid={self._get_data_path(self.eval_path)}",
                f"names={self._get_data_path(self.names_path)}",
                f"backup={self.backup_path}"
            ]))
        # * names.txt
        with open(self.names_path, "w") as names_file:
            names_file.write(
                "\n".join([name for name in self.classes.keys()]))
        # * yolov4.cfg
        with open(self.config_path, "w") as config_file:
            # to easily add yolo-tiny
            config_file.write(self._get_config())
        # * test.txt and train.txt
        images = self.finder.find_all_list("jpg")
        shuffle(images)
        if self.dedic_eval_path is None:
            # split images randomly
            for path in images:
                path = os.path.abspath(path) if self.absolute_paths \
                    else get_relpath(self.exec_path, path)
            split_num = int(len(images) * self.eval_percent / 100)
            with open(self.train_path, "w") as train_file:
                train_file.write("\n".join(images[split_num:]))
            with open(self.eval_path, "w") as eval_file:
                eval_file.write("\n".join(images[:split_num]))
        else:
            # dedicated eval path
            logger.warning("This feature was not tested yet, be careful!")
            with open(self.train_path, "w") as train_file:
                train_file.write("\n".join(images))
            eval_images = Finder(self.dedic_eval_path,
                                 "", "jpg").find_all_list()
            shuffle(eval_images)
            with open(self.eval_path, "w") as eval_file:
                eval_file.write("\n".join(eval_images))

    @classmethod
    def add_parser_arguments(cls, parser: argparse.ArgumentParser):
        super().add_parser_arguments(parser)
        parser.add_argument("-b", "--backup", default=defaults.YOLO_BACKUP_PATH, metavar="PATH",
                            help="Directory to store training weights")

        network_group = parser.add_argument_group(
            "network settings",
            description="It is not recommended to mess with these,\
                unless your GPU is running out of memory\
                or the learning process is crashing")
        network_group.add_argument("--batch-size", metavar="SIZE", type=int, default=defaults.YOLO_BATCH_SIZE,
                                   help="How many images are in a batch")
        network_group.add_argument("--subdivisions", type=int, default=defaults.YOLO_SUBDIVISIONS,
                                   help="To how many subidivisions is a batch split to\
                                       (saves GPU memory, but increases training time")
        network_group.add_argument("--height", type=int, default=defaults.YOLO_HEIGHT,
                                   help="What height is the image resized to (=network height)")
        network_group.add_argument("--width", type=int, default=defaults.YOLO_WIDTH,
                                   help="What width is the image resized to (=network width)")
