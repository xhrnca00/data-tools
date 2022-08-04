from ..logger import get_logger
from .export_yolov4_config import get_yolo_tiny_config
from .yolo import YoloArgs, YoloConverter

logger = get_logger()


class YoloTinyConverter(YoloConverter):
    def __init__(self, args: YoloArgs):
        super().__init__(args)

    def _get_config(self):
        return get_yolo_tiny_config(len(self.classes), self.batch_size, self.subdivisions, self.height, self.width)
