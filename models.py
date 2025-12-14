from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class ParkingSpaceStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"

class ParkingSpace(BaseModel):
    id: int
    space_type: str  # "옥내 기계식", "옥외 기계식", "옥내 자주식", "옥외 자주식"
    status: ParkingSpaceStatus = ParkingSpaceStatus.AVAILABLE
    occupied_by: Optional[str] = None
    occupied_at: Optional[datetime] = None

class ParkingLot(BaseModel):
    순번: int
    대지위치주소: str
    건축면적: str
    옥내_기계식_주차대수: int
    옥외_기계식_주차대수: int
    옥내_자주식_주차대수: int
    옥외_자주식_주차대수: int
    총_주차대수: int
    spaces: List[ParkingSpace] = []

class ParkingLotResponse(BaseModel):
    page: int
    perPage: int
    totalCount: int
    currentCount: int
    matchCount: int
    data: List[ParkingLot]

class GameRoom(BaseModel):
    room_id: str
    parking_lot: ParkingLot
    players: List[str] = []
    created_at: datetime
    is_active: bool = True

class OccupySpaceRequest(BaseModel):
    room_id: str
    space_id: int
    player_name: str

class OccupySpaceResponse(BaseModel):
    success: bool
    message: str
    space: Optional[ParkingSpace] = None

class GameStatsResponse(BaseModel):
    room_id: str
    total_spaces: int
    occupied_spaces: int
    available_spaces: int
    players: List[str]
    leaderboard: Dict[str, int]  # player_name: occupied_count