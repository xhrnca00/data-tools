import logging as _logging

from .util import base_off_cwd as _base_off_cwd

# default logger level
LOG_LEVEL = _logging.DEBUG

# check unused parameters in annotation files
CHECK_UNUSED_PARAMS = True

#! paths are based off cwd (not this file)
# argument defaults
SAVE_ARGS = False
EXEC_PATH = _base_off_cwd("../../..", __file__)
OUTPUT_PATH = _base_off_cwd("../../config", __file__)
INPUT_PATH = _base_off_cwd("../../data", __file__)
EVALUATION_PERCENT = 10
DATA_PREFIX = "!"
DATA_EXTENSION = "json"
ABSOLUTE_PATH = False
FORCE_OVERRIDE = False

# yolo
YOLO_BACKUP_PATH = _base_off_cwd("../../backup", __file__)
YOLO_BATCH_SIZE = 64
YOLO_SUBDIVISIONS = 16
YOLO_HEIGHT = YOLO_WIDTH = 416

# attributes
ATTR_MULTIPLE = True


def print_defaults() -> None:
    # print(f"cwd: {_path.abspath('.')}")
    print(
        LOG_LEVEL,
        CHECK_UNUSED_PARAMS,
        SAVE_ARGS,
        EXEC_PATH,
        OUTPUT_PATH,
        INPUT_PATH,
        EVALUATION_PERCENT,
        DATA_PREFIX,
        DATA_EXTENSION,
        ABSOLUTE_PATH,
        FORCE_OVERRIDE,
        YOLO_BACKUP_PATH,
        YOLO_BATCH_SIZE,
        YOLO_SUBDIVISIONS,
        YOLO_HEIGHT,
        YOLO_WIDTH,
        ATTR_MULTIPLE,
        sep="\n"
    )


if __name__ == "__main__":
    print_defaults()
