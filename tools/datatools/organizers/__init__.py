from typing import Dict, Type

from .base_organizer import BaseOrganizer
from .view_type import ViewTypeOrganizer


name_organizer_map: Dict[str, Type[BaseOrganizer]] = {
    "view-type": ViewTypeOrganizer,
}
