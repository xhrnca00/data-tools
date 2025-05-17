import argparse
import sys

from os.path import exists
from pathlib import Path

from datatools import defaults
from datatools.logger import get_logger
from datatools.organizers import name_organizer_map
from datatools.util import base_off_cwd


LAST_ARGS_SAVE_PATH = base_off_cwd(
    f"last_{Path(__file__).stem}_args.txt", __file__)

logger = get_logger()


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sort car type dataset based off location and dominant car type",
    )
    parser.add_argument("-S", "--save_args", action="store_const",
                        const=True, default=defaults.SAVE_ARGS,
                        help="Whether to save arguments into a file")

    # * only one parser for now
    name_organizer_map["view-type"].add_arguments(parser)

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


if __name__ == "__main__":
    # TODO: make a copy of the dataset
    # TODO: test this
    raise NotImplementedError("Not tested, make a COPY of the dataset!")
    main()
