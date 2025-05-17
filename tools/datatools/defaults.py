import logging as _logging

from os.path import sep as _sep


# default logger level
# * on the beginning to avoid circular imports (all modules import logger)
# LOG_LEVEL = _logging.DEBUG
LOG_LEVEL = _logging.INFO

# * for printing defaults
if __name__ == "__main__":
    from util import base_off_cwd as _base_off_cwd  # type: ignore
else:
    from .util import base_off_cwd as _base_off_cwd


#! boolean flags should NOT be overriden, unless argument names are changed (--save_args flag disables saving etc.)

# * export.py
# check unused parameters in annotation files
CHECK_UNUSED_PARAMS = True

#! paths are based off cwd (not this file)
# argument defaults
SAVE_ARGS = False
EXEC_PATH = _base_off_cwd(f"..{_sep}..{_sep}..", __file__)
OUTPUT_PATH = _base_off_cwd(f"..{_sep}..{_sep}config", __file__)
INPUT_PATH = _base_off_cwd(f"..{_sep}..{_sep}data", __file__)
EVALUATION_PERCENT = 10
DATA_PREFIX = "!"
DATA_EXTENSION = "json"
ABSOLUTE_PATH = False
FORCE_OVERRIDE = False

# yolo
YOLO_BACKUP_PATH = _base_off_cwd(f"..{_sep}..{_sep}backup", __file__)
YOLO_BATCH_SIZE = 64
YOLO_SUBDIVISIONS = 16
YOLO_HEIGHT = YOLO_WIDTH = 416

# attributes
ATTR_MULTIPLE = True

# * organize.py
DATA_ROOT = INPUT_PATH
IMAGE_EXTENSION = "jpg"
USE_PREFIX = False
NO_SET_PREFIX = False
LEAVE_FOLDERS = False
TRANSFER_METHOD = "copy"


def _print_defaults() -> None:
    # print(f"cwd: {_path.abspath('.')}")
    print(
        f"LOG_LEVEL: {LOG_LEVEL}",
        f"CHECK_UNUSED_PARAMS: {CHECK_UNUSED_PARAMS}",
        f"SAVE_ARGS: {SAVE_ARGS}",
        f"EXEC_PATH: {EXEC_PATH}",
        f"OUTPUT_PATH: {OUTPUT_PATH}",
        f"INPUT_PATH: {INPUT_PATH}",
        f"EVALUATION_PERCENT: {EVALUATION_PERCENT}",
        f"DATA_PREFIX: {DATA_PREFIX}",
        f"DATA_EXTENSION: {DATA_EXTENSION}",
        f"ABSOLUTE_PATH: {ABSOLUTE_PATH}",
        f"FORCE_OVERRIDE: {FORCE_OVERRIDE}",
        f"YOLO_BACKUP_PATH: {YOLO_BACKUP_PATH}",
        f"YOLO_BATCH_SIZE: {YOLO_BATCH_SIZE}",
        f"YOLO_SUBDIVISIONS: {YOLO_SUBDIVISIONS}",
        f"YOLO_HEIGHT: {YOLO_HEIGHT}",
        f"YOLO_WIDTH: {YOLO_WIDTH}",
        f"ATTR_MULTIPLE: {ATTR_MULTIPLE}",
        f"DATA_ROOT: {DATA_ROOT}",
        f"USE_PREFIX: {USE_PREFIX}",
        f"NO_PREFIX: {NO_SET_PREFIX}",
        f"LEAVE_FOLDERS: {LEAVE_FOLDERS}",
        f"TRANSFER_METHOD: {TRANSFER_METHOD}",
        sep="\n"
    )


if __name__ == "__main__":
    _print_defaults()
