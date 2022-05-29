import argparse
import os

from abc import ABCMeta, abstractmethod
from json import load
from typing import Any, Dict, List

from .. import defaults
from ..finder import Finder
from ..logger import get_logger
from ..util import base_off_cwd

logger = get_logger()


class ConverterArgs(argparse.Namespace):
    exec: str
    output: str
    input: str
    prefix: str
    data_extension: str
    absolute: bool
    force: bool
    val: int
    dedicated: str


class Converter(metaclass=ABCMeta):
    def __init__(self, finder: Finder, args: ConverterArgs):
        self.finder = finder
        self.output_path = args.output
        self.exec_path = args.exec
        self.absolute_paths = args.absolute

        self.force = args.force

        self.mode = "dedic" if args.dedicated is None else "perc"
        self.eval_percent = args.val
        self.dedic_eval_path = args.dedicated
        self._handle_output_noexist()

        self._set_types()

    def _handle_output_noexist(self):
        os.makedirs(self.output_path, exist_ok=True)

    def _set_types(self):
        # from current file to _labelme
        with open(base_off_cwd("../../_labelme/labelflags.json", __file__)) as f:
            json = load(f)
            self.vehicle_types = json["vehicle"]
            del json

    def _handle_files_exist(self, paths: List[str]):
        not_present = True
        for path in paths:
            if os.path.isfile(path):
                not_present = False
                break
        if not_present:
            return
        if not self.force:
            ui = input("Current config will be overwritten!\n" +
                       "Do you want to proceed? (Y/n): ").lower()
            if ui != "y":
                logger.error("Can't override current files")
                raise FileExistsError("Can't override current files")
        for path in paths:
            if os.path.isfile(path):
                os.remove(path)
                logger.info(f"Deleted {path}")

    def _type_from_flags(self, shape: Dict[str, Dict[str, bool]], selection):
        for flag, value in shape["flags"].items():
            if value and flag in selection:
                return flag
        raise ValueError("No known flag specified")

    def _is_annotation_file(self, file: Dict[str, Any]):
        try:
            secondary_data = []
            if defaults.CHECK_UNUSED_PARAMS:
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

    @classmethod
    def add_parser_arguments(cls, parser: argparse.ArgumentParser):
        parser.add_argument("-e", "--exec", metavar="PATH", default=defaults.EXEC_PATH,
                            help="Path to network learning executable")
        parser.add_argument("-o", "--output", default=defaults.OUTPUT_PATH, metavar="PATH",
                            help="Directory to output config files")
        parser.add_argument("-i", "--input", default=defaults.INPUT_PATH, metavar="PATH",
                            help="Directory with input files")
        parser.add_argument("-p", "--prefix", default=defaults.DATA_PREFIX,
                            help="Prefix to folders with data")
        parser.add_argument("--data-extension", default=defaults.DATA_EXTENSION, metavar="EXTENSION",
                            help="Data files extension")
        parser.add_argument("-a", "--absolute", action="store_const",
                            const=not defaults.ABSOLUTE_PATH, default=defaults.ABSOLUTE_PATH,
                            help="Whether to have absolute paths to images in output files")
        parser.add_argument("-f", "--force", action="store_const",
                            const=not defaults.FORCE_OVERRIDE, default=defaults.FORCE_OVERRIDE,
                            help="Force deletion of existing config files")

        eval_group = parser.add_mutually_exclusive_group()
        eval_group.add_argument("-v", "--val", "--evaluation-percent", type=int, default=defaults.EVALUATION_PERCENT,
                                help="Percentage of all files to add into evaluation file")
        eval_group.add_argument("-d", "--dedicated", "--dedicated-evaluation-path", metavar="PATH", default=None, type=str,
                                help="Whether to have dedicated evaluation images")
