import os

from typing import Any, Dict, List, Tuple
from json import loads, dumps
from random import shuffle


TRAIN_SPLIT_PERCENT = 0.80

ALLOW_FLAG_CLASSIFICATION = True
ALLOW_LABEL_CLASSIFICATION = False

if ALLOW_LABEL_CLASSIFICATION:
    VEHICLE_TYPES = ["car", "bus", "van", "truck", "lighttruck"]
    COLORS = ["white", "gray", "yellow", "red", "green", "blue", "black"]


def find_pic_subdirs(data_prefix: str = "!") -> List[str]:
    dir_paths = []
    for item in os.scandir("."):
        if item.is_dir() and item.name.startswith(data_prefix):
            dir_paths.append(item.path)
    return dir_paths


def find_config_in_subdir(path, extension="json") -> List[str]:
    json_paths = []
    for item in os.scandir(path):
        if item.name.endswith(f".{extension}"):
            json_paths.append(item.path)
    return json_paths


def convert_to_export_json(path: str, label: str, is_occluded: bool, view: str, dataset: str):
    with open(path) as file:
        old = loads(file.read())
    veh_type, color, obj_bbox, color_bbox = parse_shapes_json(old["shapes"])

    new: Dict[str, Any] = {}
    new["image_size"] = [old["imageWidth"], old["imageHeight"]]
    new["objects"] = [{
        "label": label,
        "is_occluded": is_occluded,
        "attributes": {
            "type": veh_type,
            "color_bbox": [color_bbox],
            "view": view,
            "color": color
        },
        "bbox": obj_bbox
    }]
    new["dataset"] = dataset
    new["image"] = os.path.relpath(
        os.path.join(path, os.pardir, old["imagePath"]))
    return new


def parse_shapes_json(shapes: List[Dict[str, Any]]) -> Tuple[str, str, List[float], List[float]]:
    for shape in shapes:
        if shape["label"] == "vehicle" and ALLOW_FLAG_CLASSIFICATION:
            veh_type = type_from_shape_flags(shape)
            obj_bbox = parse_bbox(shape)
        elif shape["label"] == "color" and ALLOW_FLAG_CLASSIFICATION:
            color = type_from_shape_flags(shape)
            color_bbox = parse_bbox(shape, round_digits=0)
        elif shape["label"] in VEHICLE_TYPES and ALLOW_LABEL_CLASSIFICATION:
            veh_type = shape["label"]
            obj_bbox = parse_bbox(shape)
        elif shape["label"] in COLORS and ALLOW_LABEL_CLASSIFICATION:
            color = shape["label"]
            color_bbox = parse_bbox(shape, round_digits=0)
        else:
            raise ValueError("unknown label")
    return (veh_type, color, obj_bbox, color_bbox)

def type_from_shape_flags(shape: Dict[str, Dict[str, bool]]) -> str:
    types: List[str] = []
    for flag, value in shape["flags"].items():
        if value and flag:
            types.append(flag)
    return types[0]


def parse_bbox(shape: Dict[str, Any], round_digits=1) -> List[float]:
        bbox = shape["points"][0] + shape["points"][1]
        for i in range(len(bbox)):
            bbox[i] = round(bbox[i], round_digits) if round_digits > 0 else round(
                bbox[i])  # rounds to an int
        # change bbox to format Xmin, Ymin, Xmax, Ymax
        bbox[0], bbox[2] = min(bbox[0], bbox[2]), max(bbox[0], bbox[2])
        bbox[1], bbox[3] = min(bbox[1], bbox[3]), max(bbox[1], bbox[3])
        return bbox

def convert_all(dir=".", label: str = "vehicle", is_occluded: bool = False, view: str = "front", dataset: str = "cars"):
    os.chdir(dir)
    train_path = "./train.json"
    test_path = "./test.json"
    # check if files exist; if yes, ask to proceed and delte them
    if os.path.isfile(train_path) or os.path.isfile(test_path):
        ui = input("Current config will be overwritten!\n" +
                   "Do you want to proceed? (Y/n): ").lower()
        if ui != "y":
            return
        if os.path.isfile(train_path):
            os.remove(train_path)
        if os.path.isfile(test_path):
            os.remove(test_path)

    dir_paths = find_pic_subdirs()
    json_paths: List[str] = []
    for dir_path in dir_paths:
        json_paths.extend(find_config_in_subdir(dir_path))

    all_vehicles = []
    for json_path in json_paths:
        all_vehicles.append(convert_to_export_json(json_path, label,
                                                   is_occluded, view, dataset))

    split_num = int(len(all_vehicles) * TRAIN_SPLIT_PERCENT)
    shuffle(all_vehicles)
    with open(train_path, "w") as train_file:
        train_file.write(dumps(all_vehicles[:split_num]))
    with open(test_path, "w") as test_file:
        test_file.write(dumps(all_vehicles[split_num:]))


if __name__ == "__main__":
    convert_all()
