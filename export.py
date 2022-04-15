import argparse
import os

from abc import ABC, abstractmethod
from json import dumps, load
from pathlib import Path
from queue import Queue
from random import randrange, shuffle
from typing import Any, Dict, Generator, List, Tuple, Union

from _export.export_yolov4_config import get_yolo_config

# check unused parameters in annotation files
CHECK_UNUSED_PARAMS = True

# argument defaults
DEFAULT_CONVERSION_FORMAT = "yolo"
DEFAULT_EXEC_PATH = ".."
DEFAULT_OUTPUT_PATH = "_data"
DEFAULT_BACKUP_PATH = "backup"
DEFAULT_INPUT_PATH = "."
DEFAULT_EVALUATION_PERCENT = 10
DEFAULT_DATA_PREFIX = "!"
DEFAULT_DATA_EXTENSION = "json"
DEFAULT_ABSOLUTE_PATH = False
DEFAULT_ALLOW_LEGACY = False


# type definition to get intellisense
class Args(argparse.Namespace):
    format: str
    input: str
    data_extension: str
    prefix: str
    output: str
    backup: str
    exec: str
    val: int
    absolute: bool
    legacy: bool


class Finder:
    def __init__(self, search_root: str, data_prefix: str, data_extension: str) -> None:
        self.search_root = search_root
        self.data_prefix = data_prefix
        self.data_extension = data_extension

    def _is_data_dir(self, item: os.DirEntry) -> bool:
        return item.is_dir() and item.name.startswith(self.data_prefix)

    def _is_data_file(self, item: os.DirEntry, extension) -> bool:
        return item.is_file() and item.name.endswith(f".{extension}")

    def find_all(self, data_extension=None) -> Generator[str, None, None]:
        if data_extension is None:
            data_extension = self.data_extension
        unsearched_dirs: Queue[str] = Queue()
        # * we do not want to search root dir for input files
        # put ./<dir> in
        for item in os.scandir(self.search_root):
            if self._is_data_dir(item):
                unsearched_dirs.put(item.path)

        while not unsearched_dirs.empty():
            _dir = unsearched_dirs.get()  # dir shadows a builtin
            for item in os.scandir(_dir):
                if self._is_data_file(item, data_extension):
                    yield item.path
                elif self._is_data_dir(item):
                    unsearched_dirs.put(item.path)


class Converter(ABC):
    def __init__(self, finder: Finder, output_path: str, exec_path: str, eval_percent: int, allow_legacy: bool, absolute_paths: bool):
        self.finder = finder
        self.output_path = output_path
        self.exec_path = exec_path
        self.eval_percent = eval_percent
        self.allow_legacy = allow_legacy
        self.absolute_paths = absolute_paths

        self._set_types()

    def _set_types(self):
        # from current file to _labelme
        with open(os.path.join(Path(os.path.abspath(__file__)).parent, "_labelme/labelflags.json")) as f:
            json = load(f)
            self.vehicle_types = json["vehicle"]
            self.colors = json["color"]

    def _handle_files_exist(self, paths: List[str]):
        not_present = True
        for path in paths:
            if os.path.isfile(path):
                not_present = False
                break
        if not_present:
            return

        ui = input("Current config will be overwritten!\n" +
                   "Do you want to proceed? (Y/n): ").lower()
        if ui != "y":
            raise FileExistsError("Can't override current files")
        for path in paths:
            if os.path.isfile(path):
                os.remove(path)
                print(f"Deleted {path}")

    def _type_from_flags(self, shape: Dict[str, Dict[str, bool]], selection):
        for flag, value in shape["flags"].items():
            if value and flag in selection:
                return flag
        raise ValueError("No known flag specified")

    def _is_annotation_file(self, file: Dict[str, Any]):
        try:
            secondary_data = []
            if CHECK_UNUSED_PARAMS:
                secondary_data.append(file["version"])
                secondary_data.append(file["flags"])
                secondary_data.append(file["imageData"])
            secondary_data.append(file["shapes"])
            secondary_data.append(file["imagePath"])
            secondary_data.append(file["imageHeight"])
            secondary_data.append(file["imageWidth"])
            del secondary_data
            return True
        except KeyError:
            return False

    @abstractmethod
    def convert_file(self, path):
        pass

    @abstractmethod
    def convert(self) -> None:
        pass


class YoloConverter(Converter):
    def __init__(self, finder: Finder, output_path: str, exec_path: str,
                 eval_percent: int, allow_legacy: bool, absolute_paths: bool, backup_path: str):
        super().__init__(finder, output_path, exec_path,
                         eval_percent, allow_legacy, absolute_paths)

        # output files
        self.config_path = f"{self.output_path}/yolov4.cfg"
        self.data_path = f"{self.output_path}/obj.data"
        self.train_path = f"{self.output_path}/train.txt"
        self.eval_path = f"{self.output_path}/test.txt"
        self.names_path = f"{self.output_path}/names.txt"
        self.backup_path = backup_path

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
        if (self.allow_legacy and shape["label"] in self.vehicle_types):
            return self.classes[shape["label"]]
        elif (shape["label"] == "vehicle"):
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
        for path in self.finder.find_all():
            try:
                self.convert_file(path)
            except ValueError as e:
                print(f"Bad format, skipping {path} ({e})")
        # write config files
        with open(self.data_path, "w") as data_file:
            data_file.write("\n".join([
                f"classes={len(self.classes)}",
                f"train={self._get_data_path(self.train_path)}",
                f"valid={self._get_data_path(self.eval_path)}",
                f"names={self._get_data_path(self.names_path)}",
                f"backup={self.backup_path}"
            ]))
        with open(self.names_path, "w") as names_file:
            names_file.write(
                "\n".join([name for name, id in self.classes.items()]))
        with open(self.config_path, "w") as config_file:
            config_file.write(get_yolo_config(len(self.classes)))
        # write to train and eval files, expecting other than our data
        to_eval = 100 / self.eval_percent
        # offset counter to alter run results
        counter: float = randrange(0, int(to_eval))
        for path in self.finder.find_all("txt"):
            write_path = os.path.abspath(
                path) if self.absolute_paths else get_relpath(self.exec_path, path)
            if counter < to_eval:
                with open(self.train_path, "a") as train_file:
                    train_file.write(f"{write_path}\n")
            else:
                with open(self.eval_path, "a") as eval_file:
                    eval_file.write(f"{write_path}\n")
                counter -= to_eval
            counter += 1


class AttributesConverter(Converter):
    def __init__(self, finder: Finder, output_path: str, exec_path: str, eval_percent: int, allow_legacy: bool, absolute_paths: bool):
        super().__init__(finder, output_path, exec_path,
                         eval_percent, allow_legacy, absolute_paths)

        # output paths
        self.train_path = f"{self.output_path}/train.json"
        self.eval_path = f"{self.output_path}/test.json"

        # list of vehicles to put to final files
        self.vehicles: List[Dict[str, Any]] = []

        # parameters that might be needed in files but we are not changing
        self.label: str = "vehicle"
        self.is_occluded: bool = False
        self.view: str = "front"
        self.dataset: str = "cars"

    def _parse_shapes(self, shapes: List[Dict[str, Any]]) -> Tuple[str, str, List[float], List[float]]:
        if len(shapes) > 2:
            raise ValueError(
                "More than one vehicle per file is currently unsupported")
        for shape in shapes:
            if shape["label"] == "vehicle":
                veh_type = self._type_from_flags(shape, self.vehicle_types)
                obj_bbox = self._parse_bbox(shape)
            elif shape["label"] == "color":
                color = self._type_from_flags(shape, self.colors)
                color_bbox = self._parse_bbox(shape, round_digits=0)
            elif self.allow_legacy and shape["label"] in self.vehicle_types:
                veh_type = shape["label"]
                obj_bbox = self._parse_bbox(shape)
            elif self.allow_legacy and shape["label"] in self.colors:
                color = shape["label"]
                color_bbox = self._parse_bbox(shape, round_digits=0)
            else:
                raise ValueError("unknown label")
        return (veh_type, color, obj_bbox, color_bbox)

    def _parse_bbox(self, shape: Dict[str, Any], round_digits=1) -> List[float]:
        bbox = shape["points"][0] + shape["points"][1]
        for i in range(len(bbox)):
            bbox[i] = round_to_digits(bbox[i], round_digits)
        # change bbox to format Xmin, Ymin, Xmax, Ymax
        bbox[0], bbox[2] = min(bbox[0], bbox[2]), max(bbox[0], bbox[2])
        bbox[1], bbox[3] = min(bbox[1], bbox[3]), max(bbox[1], bbox[3])
        return bbox

    def convert_file(self, path: str) -> Dict[str, Any]:
        # TODO: allow multiple vehicles in one file
        with open(path) as file:
            old: Dict[str, Any] = load(file)
        if not self._is_annotation_file(old):
            raise ValueError("Not in labelme format")
        new: Dict[str, Any] = {}
        veh_type, color, obj_bbox, color_bbox = self._parse_shapes(
            old["shapes"])
        new["image_size"] = [old["imageWidth"], old["imageHeight"]]
        new["objects"] = [{
            "label": self.label,
            "is_occluded": self.is_occluded,
            "attributes": {
                "type": veh_type,
                "color_bbox": [color_bbox],
                "view": self.view,
                "color": color
            },
            "bbox": obj_bbox
        }]
        new["dataset"] = self.dataset
        path_to_img = os.path.join(Path(path).parent, old["imagePath"])
        new["image"] = os.path.abspath(path_to_img) if self.absolute_paths \
            else get_relpath(self.exec_path, path_to_img)
        return new

    def convert(self) -> None:
        self._handle_files_exist([self.train_path, self.eval_path])
        for path in self.finder.find_all():
            try:
                self.vehicles.append(self.convert_file(path))
            except ValueError as e:
                print(f"Bad format, skipping {path} ({e})")
        # write files
        split_num = int(len(self.vehicles) * self.eval_percent / 100)
        shuffle(self.vehicles)
        # ENHANCE: append to files instead of writing all (memory)
        with open(self.train_path, "w") as train_file:
            train_file.write(dumps(self.vehicles[split_num:]))
        with open(self.eval_path, "w") as test_file:
            test_file.write(dumps(self.vehicles[:split_num]))


def round_to_digits(num: float, digits: int) -> Union[int, float]:
    return round(num, digits) if digits > 0 else round(num)


def get_relpath(_from: str, to: str):
    __from = Path(_from)
    __from = __from.parent if __from.is_file() else __from
    return os.path.relpath(to, __from)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Convert car annotation files from labelme to different format")

    parser.add_argument(
        "-f", "--format", default=DEFAULT_CONVERSION_FORMAT, choices=["yolo", "attributes"],
        help="Which format to convert to")
    parser.add_argument(
        "-e", "--exec", metavar="PATH", default=DEFAULT_EXEC_PATH,
        help="Path to network learning executable")
    parser.add_argument(
        "-o", "--output", default=DEFAULT_OUTPUT_PATH, metavar="PATH",
        help="Directory to output config files")
    parser.add_argument(
        "-b", "--backup", default=DEFAULT_BACKUP_PATH, metavar="PATH",
        help="YOLO-only: Directory to store training weights")
    parser.add_argument(
        "-i", "--input", default=DEFAULT_INPUT_PATH, metavar="PATH",
        help="Directory with input files")
    parser.add_argument(
        "-v", "--val", "--evaluation-percent", type=int, default=DEFAULT_EVALUATION_PERCENT,
        help="Percentage of all files to add into evaluation file")
    parser.add_argument(
        "-p", "--prefix", default=DEFAULT_DATA_PREFIX,
        help="Prefix to folders with data")
    parser.add_argument(
        "--data-extension", default=DEFAULT_DATA_EXTENSION, metavar="EXTENSION",
        help="Data files extension")
    parser.add_argument(
        "-a", "--absolute", action="store_true", default=DEFAULT_ABSOLUTE_PATH,
        help="Whether to have absolute paths to images in output files")
    parser.add_argument(
        "-l", "--legacy", action="store_true", default=DEFAULT_ALLOW_LEGACY,
        help="Allow legacy annotation style (see README.md)"
    )

    return parser.parse_args()


def main():
    args: Args = parse_args()
    input_finder = Finder(args.input, args.prefix, args.data_extension)
    if args.format == "yolo":
        converter = YoloConverter(
            input_finder, args.output, args.exec, args.val, args.legacy, args.absolute, args.backup)
    # can use else becaues argparse is guarding arguments
    else:
        converter = AttributesConverter(
            input_finder, args.output, args.exec, args.val, args.legacy, args.absolute)
    converter.convert()


if __name__ == "__main__":
    main()
