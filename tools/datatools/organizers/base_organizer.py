import argparse

from abc import abstractmethod
from glob import glob
from os import makedirs
from os.path import sep
from shutil import SameFileError, copy2, move
from typing import Any, Callable, List, Optional

from .. import defaults
from ..finder import Finder
from ..logger import get_logger


logger = get_logger()


class OrganizerArgs(argparse.Namespace):
    data: str
    new_data_root: Optional[str]
    prefix: str
    image_extension: str
    use_prefix: bool
    no_set_prefix: bool
    leave_folders: bool
    transfer_method: str


class BaseOrganizer():
    def __init__(self, args: OrganizerArgs) -> None:
        self.data_root = args.data
        self.new_data_root = args.new_data_root if args.new_data_root is not None else self.data_root
        self.data_prefix = args.prefix
        self.image_extension = args.image_extension
        self.search_prefix = self.data_prefix if args.use_prefix else ""
        self.new_folder_prefix = "" if args.no_set_prefix else self.data_prefix
        self.delete_folders = not args.leave_folders
        self.transfer_func: Callable[[str, str], Any] = copy2
        if args.transfer_method == "move":
            self.transfer_func = move

        self.finder = Finder(
            self.data_root, self.search_prefix, self.image_extension)
        # we do not want to check existence every time
        self.dir_exist_cache: List[str] = []

    def _ensure_existance(self, dirname) -> None:
        if dirname not in self.dir_exist_cache:
            # ENHANCE: might be better to write our own function, as makedirs checks parents as well (they are in the cache)
            makedirs(dirname, exist_ok=True)
            self.dir_exist_cache.append(dirname)

    def _transfer(self, src: str, dst: str) -> None:
        self._ensure_existance(dst)
        self.transfer_func(src, dst)

    def organize(self) -> None:
        self.transfered_files = 0
        self.read_files = 0
        for im_path in self.finder.find_all():
            files = glob(im_path.rsplit(".", 1)[0] + ".*")
            self.read_files += 1
            if self._should_transfer(files):
                self.transfer_group(files)
            else:
                logger.warning(
                    f"Didn't move group {files}, falied transfer check")
        logger.success(
            f"Finished organizing, transfered {self.transfered_files}/{self.read_files}")

    def transfer_group(self, group_paths: List[str]) -> None:
        folder = self.new_data_root \
            + self._get_transfer_folder(group_paths)
        try:
            for path in group_paths:
                self._transfer(path, folder)
                self.transfered_files += 1
        except (SameFileError, OSError) as e:
            # TODO: test this
            logger.error(
                f"Couldn't finish moving {group_paths} to {folder} ({e})")
            logger.important(
                f"Please check for existing files in the folder {folder}"
                + f"or remaining files in {group_paths[0].rsplit(sep, 1)[0]}")

    @abstractmethod
    def _should_transfer(self, group_paths: List[str]) -> bool:
        return True

    @abstractmethod
    def _get_transfer_folder(self, group_paths: List[str]) -> str:
        ...

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        parser.add_argument("-d", "--data", "--data_root", default=defaults.DATA_ROOT,
                            type=str, metavar="PATH", help="Root of the data to be sorted")
        parser.add_argument("-n", "--new_data_root", default=None, type=str, metavar="PATH",
                            help="New data root, leave as None for the same value as data root")
        parser.add_argument("-p", "--prefix", default=defaults.DATA_PREFIX,
                            help="Prefix to folders with data (leave as None for all subfolders to be included)")
        parser.add_argument("--image_extension", default=defaults.IMAGE_EXTENSION, metavar="EXTENSION",
                            help="Image files extension (might not be used)")
        parser.add_argument("--use_prefix", action="store_true", default=defaults.USE_PREFIX,
                            help="Use prefix when searching for files to be organized")
        parser.add_argument("--no_set_prefix", default=defaults.NO_SET_PREFIX,
                            action="store_true", help="Do not create folders with data prefix")
        parser.add_argument("-l", "--leave_folders", "--leave_empty", default=defaults.LEAVE_FOLDERS,
                            action="store_true", help="Do not delete empty folders after organizing is done")
        parser.add_argument("--transfer_method", choices=["move", "copy"], default=defaults.TRANSFER_METHOD,
                            help="Change file transfering method (copy copies the files, move moves them)")
