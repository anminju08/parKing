import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import uuid
from models import ParkingLot, ParkingSpace, GameRoom, ParkingSpaceStatus

class ParkingGameService:
    def __init__(self):
        self.game_rooms: Dict[str, GameRoom] = {}
        self.api_key = "ldsUnAd0IgYlk/QbU7ax9Sw9G3h0d3Cn2gTWiwnfwC2F8u6BplOoG2f/DLqvR7DM7QBVL+82rOS/x+2u2EhOPA=="
        # 한국 공공데이터포털 API 엔드포인트
        self.api_base_url = "https://api.odcloud.kr/api"
        self.service_key = "15064338/v1/uddi:91ea9cb0-f9d1-48ab-ab53-89c0a6b94451"
    
    async def fetch_parking_data(self, page: int = 1, per_page: int = 10) -> List[ParkingLot]:
        """한국 공공데이터포털 API에서 주차장 데이터를 가져옵니다"""
        
        try:
            async with httpx.AsyncClient() as client:
                # 한국 공공데이터포털 API 엔드포인트
                endpoint = f"{self.api_base_url}/{self.service_key}"
                params = {
                    "page": page,
                    "perPage": per_page,
                    "serviceKey": self.api_key
                }
                
                response = await client.get(endpoint, params=params, timeout=10.0)
                response.raise_for_status()
                
                api_response = response.json()
                print(f"API 응답: {api_response}")  # 디버깅용
                
                # 공공데이터포털 API 응답 구조에 맞게 수정
                if "data" in api_response:
                    raw_data = api_response["data"]
                elif isinstance(api_response, list):
                    raw_data = api_response
                else:
                    print(f"예상과 다른 API 응답 구조: {api_response}")
                    raw_data = []
                    
        except Exception as e:
            print(f"API 호출 실패: {e}")
            raw_data = []
        
        parking_lots = []
        for data in raw_data:
            # 주차 공간 생성
            spaces = []
            space_id = 1
            
            # 각 타입별로 주차 공간 생성
            for space_type, count in [
                ("옥내 기계식", data["옥내 기계식 주차대수"]),
                ("옥외 기계식", data["옥외 기계식 주차대수"]),
                ("옥내 자주식", data["옥내 자주식 주차대수"]),
                ("옥외 자주식", data["옥외 자주식 주차대수"])
            ]:
                for _ in range(count):
                    spaces.append(ParkingSpace(
                        id=space_id,
                        space_type=space_type
                    ))
                    space_id += 1
            
            parking_lot = ParkingLot(
                순번=data["순번"],
                대지위치주소=data["대지위치주소"],
                건축면적=data["건축면적"],
                옥내_기계식_주차대수=data["옥내 기계식 주차대수"],
                옥외_기계식_주차대수=data["옥외 기계식 주차대수"],
                옥내_자주식_주차대수=data["옥내 자주식 주차대수"],
                옥외_자주식_주차대수=data["옥외 자주식 주차대수"],
                총_주차대수=data["총 주차대수"],
                spaces=spaces
            )
            parking_lots.append(parking_lot)
        
        return parking_lots
    
    def create_game_room(self, parking_lot_id: int) -> str:
        """새로운 게임 룸을 생성합니다"""
        room_id = str(uuid.uuid4())[:8]
        
        # 게임 룸 초기화를 비동기로 실행
        asyncio.create_task(self._initialize_room(room_id, parking_lot_id))
        
        return room_id
    
    async def _initialize_room(self, room_id: str, parking_lot_id: int):
        """게임 룸을 초기화합니다"""
        parking_lots = await self.fetch_parking_data()
        if parking_lots and len(parking_lots) > parking_lot_id - 1:
            parking_lot = parking_lots[parking_lot_id - 1]
            
            game_room = GameRoom(
                room_id=room_id,
                parking_lot=parking_lot,
                created_at=datetime.now()
            )
            self.game_rooms[room_id] = game_room
    
    def get_game_room(self, room_id: str) -> Optional[GameRoom]:
        """게임 룸 정보를 가져옵니다"""
        return self.game_rooms.get(room_id)
    
    def join_game(self, room_id: str, player_name: str) -> bool:
        """플레이어가 게임에 참가합니다"""
        room = self.game_rooms.get(room_id)
        if room and player_name not in room.players:
            room.players.append(player_name)
            return True
        return False
    
    def occupy_space(self, room_id: str, space_id: int, player_name: str) -> tuple[bool, str, Optional[ParkingSpace]]:
        """주차 공간을 선점합니다"""
        room = self.game_rooms.get(room_id)
        if not room:
            return False, "게임 룸을 찾을 수 없습니다", None
        
        if player_name not in room.players:
            return False, "게임에 참가하지 않은 플레이어입니다", None
        
        # 해당 공간 찾기
        space = None
        for s in room.parking_lot.spaces:
            if s.id == space_id:
                space = s
                break
        
        if not space:
            return False, "존재하지 않는 주차 공간입니다", None
        
        if space.status != ParkingSpaceStatus.AVAILABLE:
            return False, "이미 점유된 주차 공간입니다", None
        
        # 공간 점유
        space.status = ParkingSpaceStatus.OCCUPIED
        space.occupied_by = player_name
        space.occupied_at = datetime.now()
        
        return True, "주차 공간을 성공적으로 선점했습니다!", space
    
    def get_game_stats(self, room_id: str) -> Optional[dict]:
        """게임 통계를 가져옵니다"""
        room = self.game_rooms.get(room_id)
        if not room:
            return None
        
        total_spaces = len(room.parking_lot.spaces)
        occupied_spaces = sum(1 for space in room.parking_lot.spaces 
                            if space.status == ParkingSpaceStatus.OCCUPIED)
        available_spaces = total_spaces - occupied_spaces
        
        # 리더보드 생성
        leaderboard = {}
        for space in room.parking_lot.spaces:
            if space.occupied_by:
                leaderboard[space.occupied_by] = leaderboard.get(space.occupied_by, 0) + 1
        
        return {
            "room_id": room_id,
            "total_spaces": total_spaces,
            "occupied_spaces": occupied_spaces,
            "available_spaces": available_spaces,
            "players": room.players,
            "leaderboard": leaderboard
        }

# 싱글톤 인스턴스
parking_service = ParkingGameService()