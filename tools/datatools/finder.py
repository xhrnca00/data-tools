import os

from queue import Queue
from typing import Generator, List


class Finder:
    def __init__(self, search_root: str, data_prefix: str, data_extension: str) -> None:
        self.search_root = search_root
        self.data_prefix = data_prefix
        self.data_extension = data_extension

    def _is_data_dir(self, item: os.DirEntry, data_prefix) -> bool:
        return item.is_dir() and item.name.startswith(data_prefix)

    def _is_data_file(self, item: os.DirEntry, extension) -> bool:
        return item.is_file() and item.name.endswith(f".{extension}")

    def find_all(self, data_extension=None, data_prefix=None, search_root=None) -> Generator[str, None, None]:
        if data_extension is None:
            data_extension = self.data_extension
        if data_prefix is None:
            data_prefix = self.data_prefix
        if search_root is None:
            search_root = self.search_root
        unsearched_dirs: Queue[str] = Queue()
        unsearched_dirs.put(search_root)
        while not unsearched_dirs.empty():
            _dir = unsearched_dirs.get()  # dir shadows a builtin
            for item in os.scandir(_dir):
                if self._is_data_file(item, data_extension):
                    yield item.path
                elif self._is_data_dir(item, data_prefix):
                    unsearched_dirs.put(item.path)

    def find_all_list(self, data_extension=None, data_prefix=None, search_root=None) -> List[str]:
        return list(self.find_all(data_extension, data_prefix, search_root))
