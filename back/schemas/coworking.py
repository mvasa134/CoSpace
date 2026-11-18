from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class ZoneType(str, Enum):
    OPEN_SPACE = "open_space"
    SILENT_ZONE = "silent_zone"      # Тихая зона для концентрации
    MEETING_ROOM = "meeting_room"    # Переговорка / скайп-кабинка
    LECTURE_HALL = "lecture_hall"    # Лекционный зал / Event-зона

class Location(BaseModel):
    latitude: float = Field(..., example=50.4497, description="Широта (геолокация НТБ КПИ)")
    longitude: float = Field(..., example=30.4594, description="Долгота (геолокация НТБ КПИ)")
    address: str = Field(..., example="просп. Берестейский, 37, Киев (Библиотека КПИ)")

class Workspace(BaseModel):
    id: int
    coworking_id: int
    name: str = Field(..., example="Стол #4.12 (Зона A)")
    floor: int = Field(..., ge=1, le=7, description="Номер этажа библиотеки (1-7)")
    zone_type: ZoneType = ZoneType.OPEN_SPACE
    description: str = Field(..., example="Рабочее место возле атриума с розеткой и LAN")
    price_per_hour: float = 40.0
    price_per_day: float = 250.0
    price_per_month: float = 3500.0
    is_available: bool = True

class Coworking(BaseModel):
    id: int
    name: str = Field(..., example="НТБ КПИ ім. Ігоря Сікорського")
    location: Location
    total_floors: int = 7
    rating: float = Field(default=4.9, ge=0, le=5)
    workspaces: List[Workspace] = []