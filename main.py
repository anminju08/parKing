from fastapi import FastAPI, Body, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
import os

# -------------------------------
#  1. MCP 서버 클래스 가져오기
# -------------------------------
from fastapi_mcp.server import FastApiMCP

# 주차 게임 관련 import
from models import (
    ParkingLotResponse, GameRoom, OccupySpaceRequest, 
    OccupySpaceResponse, GameStatsResponse
)
from parking_service import parking_service

# FastAPI 앱 생성
app = FastAPI(
    title="FastAPI-MCP 주석 예제",
    version="1.0.0",
    description="FastAPI 엔드포인트를 MCP 도구로 사용하는 예제",
)

# Pydantic 모델 정의
class SummarizeRequest(BaseModel):
    text: str
    max_sentences: int = 2

class SummarizeResponse(BaseModel):
    summary: str
    original_length: int

class WeatherResponse(BaseModel):
    city: str
    temp_c: float
    condition: str

class GreetResponse(BaseModel):
    message: str

class TimeResponse(BaseModel):
    current_time: str

# ---------------------------------------------------------------------
# 2. MCP 도구로 사용할 API 엔드포인트 정의
# ---------------------------------------------------------------------
# FastApiMCP는 FastAPI 앱에 등록된 모든 API 엔드포인트(@app.get, @app.post 등)를
# 자동으로 스캔하여 MCP 도구로 만듭니다. 각 엔드포인트의 operation_id가 도구의 이름이 됩니다.
# ---------------------------------------------------------------------

# (1) 요약 API -> 'summarize_text' 도구로 변환됨
@app.post(
    "/api/summarize",
    response_model=SummarizeResponse,
    operation_id="summarize_text",
    tags=["API Tools"],
)
async def summarize(req: SummarizeRequest = Body(...)):
    """입력 텍스트를 단순 요약하는 API"""
    text = req.text.strip()
    sentences = [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if s.strip()]
    summary = ". ".join(sentences[: max(1, req.max_sentences)])
    return SummarizeResponse(summary=summary, original_length=len(text))

# (2) 날씨 API -> 'get_weather' 도구로 변환됨
@app.get(
    "/api/weather",
    response_model=WeatherResponse,
    operation_id="get_weather",
    tags=["API Tools"],
)
async def weather(city: str = Query("Seoul")):
    """도시별 임시 날씨 데이터 반환"""
    mock_data = {"Seoul": (22.3, "Cloudy"), "Busan": (24.1, "Sunny"), "Incheon": (21.0, "Rain")}
    t, cond = mock_data.get(city, (20.0, "Unknown"))
    return WeatherResponse(city=city, temp_c=t, condition=cond)

# (3) 현재 시간 API -> 'current_time_tool' 도구로 변환됨
@app.get(
    "/tools/current_time",
    response_model=TimeResponse,
    operation_id="current_time_tool",
    tags=["Custom Tools"],
)
async def current_time_tool() -> dict:
    """현재 UTC 시간을 ISO 포맷으로 반환"""
    return {"current_time": datetime.utcnow().isoformat()}

# (4) 인사 API -> 'greet_user' 도구로 변환됨
@app.get(
    "/tools/greet",
    response_model=GreetResponse,
    operation_id="greet_user",
    tags=["Custom Tools"],
)
async def greet_user(name: str = Query(..., description="인사할 사람의 이름")) -> dict:
    """이름을 받아 인사 문장 생성"""
    return {"message": f"안녕하세요, {name}님!"}


# ---------------------------------------------------------------------
#  주차 게임 API 엔드포인트들
# ---------------------------------------------------------------------

@app.get(
    "/api/parking/lots",
    response_model=ParkingLotResponse,
    operation_id="get_parking_lots",
    tags=["Parking Game"],
)
async def get_parking_lots(page: int = Query(1), per_page: int = Query(10)):
    """공공 API에서 주차장 목록을 가져옵니다"""
    parking_lots = await parking_service.fetch_parking_data(page, per_page)
    
    return ParkingLotResponse(
        page=page,
        perPage=per_page,
        totalCount=len(parking_lots),
        currentCount=len(parking_lots),
        matchCount=len(parking_lots),
        data=parking_lots
    )

@app.post(
    "/api/parking/game/create",
    operation_id="create_parking_game",
    tags=["Parking Game"],
)
async def create_parking_game(parking_lot_id: int = Query(..., description="주차장 ID")):
    """새로운 주차 게임 룸을 생성합니다"""
    room_id = parking_service.create_game_room(parking_lot_id)
    return {"room_id": room_id, "message": "게임 룸이 생성되었습니다"}

@app.get(
    "/api/parking/game/{room_id}",
    response_model=GameRoom,
    operation_id="get_parking_game",
    tags=["Parking Game"],
)
async def get_parking_game(room_id: str):
    """게임 룸 정보를 가져옵니다"""
    room = parking_service.get_game_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="게임 룸을 찾을 수 없습니다")
    return room

@app.post(
    "/api/parking/game/{room_id}/join",
    operation_id="join_parking_game",
    tags=["Parking Game"],
)
async def join_parking_game(room_id: str, player_name: str = Query(..., description="플레이어 이름")):
    """게임에 참가합니다"""
    success = parking_service.join_game(room_id, player_name)
    if not success:
        raise HTTPException(status_code=400, detail="게임 참가에 실패했습니다")
    return {"message": f"{player_name}님이 게임에 참가했습니다"}

@app.post(
    "/api/parking/game/occupy",
    response_model=OccupySpaceResponse,
    operation_id="occupy_parking_space",
    tags=["Parking Game"],
)
async def occupy_parking_space(request: OccupySpaceRequest):
    """주차 공간을 선점합니다"""
    success, message, space = parking_service.occupy_space(
        request.room_id, request.space_id, request.player_name
    )
    
    return OccupySpaceResponse(
        success=success,
        message=message,
        space=space
    )

@app.get(
    "/api/parking/game/{room_id}/stats",
    response_model=GameStatsResponse,
    operation_id="get_parking_game_stats",
    tags=["Parking Game"],
)
async def get_parking_game_stats(room_id: str):
    """게임 통계를 가져옵니다"""
    stats = parking_service.get_game_stats(room_id)
    if not stats:
        raise HTTPException(status_code=404, detail="게임 룸을 찾을 수 없습니다")
    
    return GameStatsResponse(**stats)


# ---------------------------------------------------------------------
#  3. MCP 서버 인스턴스 생성
# ---------------------------------------------------------------------
# FastApiMCP 클래스에 FastAPI 앱(app)을 전달하여 MCP 서버를 초기화합니다.
# 이 시점에서 mcp 인스턴스는 app에 등록된 모든 경로를 분석하여
# MCP 도구 목록을 내부적으로 준비합니다.
# ---------------------------------------------------------------------
mcp = FastApiMCP(
    app,
    name="My Advanced MCP",
    describe_all_responses=True,
    describe_full_response_schema=True,
)

# ---------------------------------------------------------------------
#  정적 파일 서빙 설정
# ---------------------------------------------------------------------
# 정적 파일 디렉토리가 존재하는지 확인하고 마운트
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_root():
    """메인 페이지 - 주차 게임 인터페이스"""
    static_file = os.path.join(static_dir, "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return {"message": "주차 선점 게임 API 서버가 실행 중입니다!"}

# ---------------------------------------------------------------------
#  4. MCP 서버를 HTTP 엔드포인트로 노출
# ---------------------------------------------------------------------
# mount_http() 메소드는 MCP 서버를 특정 경로(기본값: /mcp)에 연결합니다.
# 이제 외부 클라이언트는 이 경로로 JSON-RPC 요청을 보내
# 'list_tools'나 'call_tool' 같은 MCP 표준 메소드를 호출할 수 있습니다.
# ---------------------------------------------------------------------
mcp.mount_http()  # '/mcp' 경로에 MCP 서버를 마운트합니다.

# 실행 명령:
# uvicorn main:app —reload