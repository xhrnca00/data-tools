from glob import glob
from typing import Dict, List

EXTERN_CLASSES = {
    0: "d_motorbike",
    1: "d_car",
    2: "d_bus",
    3: "d_truck",
    4: "n_motorbike",
    5: "n_car",
    6: "n_bus",
    7: "n_truck"
}
OUTPUT_CLASSES = {
    0: "car",
    1: "van",
    2: "lighttruck",
    3: "truck",
    4: "motorbike",
    5: "bus",
    6: "industrial"
}

CONVERT_CLASSES: Dict[int, int] = {
    0: 4,
    1: 0,
    2: 5,
    3: 3,
    4: 4,
    5: 0,
    6: 5,
    7: 3,
}

PATTERN = "./extern-*/**/*.txt"
LOGGING_INDEX = 20


def main():
    paths = glob(PATTERN, recursive=True)
    total = len(paths)
    for index, path in enumerate(paths):
        with open(path) as file:
            old = file.read().rstrip().split("\n")
        new: List[str] = []
        for line in old:
            new.append(f"{CONVERT_CLASSES[int(line[0])]}{line[1::]}")
        with open(path, "w") as file:
            file.write("\n".join(new))
        if index % LOGGING_INDEX == 0:
            print(f"{index}/{total}")
    print(f"{total}/{total}")
    print("done")


if __name__ == "__main__":
    response = input(
        f"This file will overwrite all .txt files matching the pattern '{PATTERN}'\n" +
        "Are you sure you want to continue? (Y/n): ").lower()
    if response == "y":
        main()
