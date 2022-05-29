import argparse
import sys

from pathlib import Path
from time import time

from datatools import defaults
from datatools.converters import name_converter_map
from datatools.logger import get_logger
from datatools.util import base_off_cwd, get_relpath
from genericpath import exists

LAST_ARGS_SAVE_PATH = base_off_cwd(
    f"last_{Path(__file__).stem}_args.txt", __file__)

logger = get_logger()


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Convert car annotation files from labelme to different format",
        epilog=f"For more info on formats, use {get_relpath('.', __file__)} <format> -h"
    )
    formats = parser.add_subparsers(dest="format", required=True)
    for name, converter in name_converter_map.items():
        subparser = formats.add_parser(
            name, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        converter.add_parser_arguments(subparser)

    parser.add_argument("-S", "--save-args", action="store_const",
                        const=not defaults.SAVE_ARGS, default=defaults.SAVE_ARGS,
                        help="Whether to save arguments into a file")

    if len(sys.argv) == 1 and exists(LAST_ARGS_SAVE_PATH):
        with open(LAST_ARGS_SAVE_PATH) as file:
            args = parser.parse_args(file.read().split())
    else:
        args = parser.parse_args()
        if args.save_args:
            with open(LAST_ARGS_SAVE_PATH, "w") as file:
                file.write(" ".join(sys.argv[1:]))
    return args


def main():
    args = parse_args()
    logger.debug(args)
    converter_class = name_converter_map[args.format]
    converter = converter_class(args)
    # raise NotImplementedError(
    #     "Might not be fully done yet, please do not mess up the dataset")
    logger.info("converting...")
    start = time()
    converter.convert()
    logger.debug(f"Took {time() - start} s")


if __name__ == "__main__":
    main()
