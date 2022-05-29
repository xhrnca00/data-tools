from typing import Dict, Type

from .attributes import AttributesConverter
from .base_converter import Converter
from .yolo import YoloConverter
from .yolo_tiny import YoloTinyConverter

name_converter_map: Dict[str, Type[Converter]] = {
    "attributes": AttributesConverter,
    "yolo": YoloConverter,
    "yolo-tiny": YoloTinyConverter
}
