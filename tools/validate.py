import os

from json import load
from pathlib import Path
from typing import Any, Dict, List

from datatools.defaults import DATA_PREFIX, INPUT_PATH
from datatools.finder import Finder
from genericpath import exists

ENABLE_CMD_PRINTING = True

if ENABLE_CMD_PRINTING:
    try:
        # zdroj: https://stackoverflow.com/q/36760127/1047788
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except AttributeError:
        pass


class Logger:
    reset_color = "\x1b[0m"
    red_color = "\x1b[31;1m"
    green_color = "\x1b[32;1m"
    yellow_color = "\x1b[33;1m"
    blue_color = "\x1b[34;1m"

    @classmethod
    def success(cls, message: str = ""):
        print(cls.green_color + "SUCCESS" +
              cls.reset_color + ": " + f"{message}")

    @classmethod
    def error(cls, message: str = ""):
        print(cls.red_color + "ERROR" + cls.reset_color + ": " + f"{message}")

    @classmethod
    def warn(cls, message: str = "") -> None:
        print(cls.yellow_color + "WARN" +
              cls.reset_color + ": " + f"{message}")

    @classmethod
    def info(cls, message: str = ""):
        print(cls.blue_color + "INFO" + cls.reset_color + ": " + f"{message}")


class Validator:
    def __init__(self) -> None:
        self.check_colors = True
        self.validation_search_path = INPUT_PATH
        self.finder = Finder(self.validation_search_path, DATA_PREFIX, "jpg")
        self._set_types()
        self.reannotate = "./open_broken_in_labelme.bat"
        self.add_blanks = "./add_empty_txt_to_broken.bat"
        self.delete_annotations = "./delete_empty_annotations.bat"
        self.batch_files = [self.reannotate,
                            self.add_blanks, self.delete_annotations]
        for file in self.batch_files:
            if exists(file):
                f = open(self.reannotate, "w")
                f.close()

    # TODO selection what to do
    def _warn_add_file(self, path_no_ext: str, message: str):
        Logger.warn(message)
        self._add_to_reannotate(path_no_ext)
        self._add_to_blanks(path_no_ext)

    def _add_to_reannotate(self, path_no_ext: str):
        with open(self.reannotate, "a") as file:
            file.write(f"call ./start_labelme.bat {path_no_ext}.jpg\n")

    def _add_to_blanks(self, path_no_ext: str):
        with open(self.add_blanks, "a") as file:
            file.write(f"echo '' > {path_no_ext}.txt\n")

    def _add_to_delete(self, path_no_ext: str):
        with open(self.delete_annotations, "a") as file:
            file.write(f"del {path_no_ext}.txt\n")
            file.write(f"del {path_no_ext}.json\n")

    def _set_types(self):
        # from current file to _labelme
        with open(
            os.path.join(
                Path(os.path.abspath(__file__)
                     ).parent, "_labelme/labelflags.json"
            )
        ) as f:
            json = load(f)
            self.vehicle_types = json["vehicle"]
            self.colors = json["color"]

    # FIXME: make this work
    def _type_from_flags(self, shape: Dict[str, Dict[str, bool]], selection):
        for flag, value in shape["flags"].items():
            if value and flag in selection:
                return flag
        raise ValueError("No known flag specified")

    # FIXME: make this work
    def _parse_shapes(self, shapes: List[Dict[str, Any]]) -> None:
        veh_num = 0
        col_num = 0
        for shape in shapes:
            if shape["label"] == "vehicle":
                veh_num += 1
            elif shape["label"] == "color":
                col_num += 1
            elif shape["label"] in self.vehicle_types:
                self._warn_add_file("<path>", "")
                veh_num += 1
            elif shape["label"] in self.colors:
                self._warn_add_file("<path>", "")
                col_num += 1
            else:
                raise ValueError("unknown label")

    # TODO better checking
    def _check_files_exist(self, path_no_extension: str) -> None:
        annotation_exists = exists(f"{path_no_extension}.json")
        yolo_exists = exists(f"{path_no_extension}.txt")
        if not annotation_exists:
            Logger.info(f"\nAnnotation file missing: {path_no_extension}.json")
            if yolo_exists:
                with open(f"{path_no_extension}.txt") as yolo:
                    if yolo.read() != "":
                        self._warn_add_file(
                            path_no_extension,
                            "Annotation file missing but .txt file not empty",
                        )
            else:
                # both yolo and annotation not present
                self._warn_add_file(
                    path_no_extension,
                    "No data file present. Annotate the picture or create an empty .txt file",
                )
        else:
            with open(f"{path_no_extension}.json") as file:
                if file.read() == "":
                    self._warn_add_file(
                        path_no_extension,
                        "Annotation file empty, please reannotate or delete it",
                    )

    def validate_file(self, path_no_extension: str) -> None:
        self._check_files_exist(path_no_extension)

    def validate_all(self):
        Logger.info("Expecting annotation extension = json\n")
        for path in self.finder.find_all():
            self.validate_file(path.rsplit(".", 1)[0])


if __name__ == "__main__":
    raise NotImplementedError(
        "This script should not be used, because it is old")
    try:
        validator = Validator()
        validator.validate_all()
    except Exception as e:
        Logger.error(str(e.with_traceback(None)))
