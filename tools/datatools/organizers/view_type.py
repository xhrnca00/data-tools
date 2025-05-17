from json import loads
from typing import Any, Dict, List

from ..logger import get_logger
from .base_organizer import BaseOrganizer, OrganizerArgs


logger = get_logger()


class ViewTypeArgs(OrganizerArgs):
    ...


class ViewTypeOrganizer(BaseOrganizer):
    def __init__(self, args: ViewTypeArgs) -> None:
        super().__init__(args)

    def _should_transfer(self, group_paths: List[str]) -> bool:
        if len(group_paths) == 0:
            logger.warning("Empty group")
            return False
        file_endings = {path.rsplit(".", 1)[1] for path in group_paths}
        if self.image_extension not in file_endings:
            # this should never happen
            logger.warning("No image in group for some reason")
            return False
        if "json" not in file_endings:
            logger.warning("No annotation file in group")
            return False
        json_path = [path for path in group_paths if path.endswith(".json")][0]
        with open(json_path) as f:
            json = loads(f.read())
        if "shapes" not in json:
            logger.warning("No shapes field in annotation file")
            return False
        return True

    def _get_transfer_folder(self, group_paths: List[str]) -> str:
        json_path = [path for path in group_paths if path.endswith(".json")][0]
        with open(json_path) as f:
            json = loads(f.read())
        v_type = self._get_type(json)
        view = json["imagePath"].split("#", 1)[0]
        return f"{view}\{v_type}"

    def _get_type(self, json: Dict[str, Any]):
        vehicles: List[Dict[str, Any]] = [shape for shape in json["shapes"]
                                          if shape["label"] == "vehicle"]
        type_area: Dict[str, float] = {}
        for vehicle in vehicles:
            veh_type = vehicle["type"]
            area: float = abs(vehicle["points"][0][0] - vehicle["points"][1][0]
                              * vehicle["points"][0][1] - vehicle["points"][1][1])
            type_area[veh_type] = type_area.get(veh_type, 0) + area

        if len(type_area) == 0:
            return "empty"
        return max(type_area, key=type_area.get)  # type: ignore
