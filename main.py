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
from ai_service import ai_service

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

# AI 관련 모델들
class AIRecommendationRequest(BaseModel):
    query: str
    max_results: int = 3

class AIRecommendationResponse(BaseModel):
    recommendation: str
    search_results: list

class AIChatRequest(BaseModel):
    message: str

class AIChatResponse(BaseModel):
    response: str

class AIStrategyResponse(BaseModel):
    strategy: str
    
class AICommentaryResponse(BaseModel):
    commentary: str

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
    "/api/parking/test",
    operation_id="test_parking_api",
    tags=["Parking Game"],
)
async def test_parking_api():
    """공공데이터포털 API 연결 테스트"""
    try:
        parking_lots = await parking_service.fetch_parking_data(1, 5)
        return {
            "success": True,
            "message": "API 연결 성공",
            "data_count": len(parking_lots),
            "sample_data": parking_lots[0] if parking_lots else None
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"API 연결 실패: {str(e)}"
        }

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
#  AI 기능 API 엔드포인트들 (LangChain/LLM/RAG)
# ---------------------------------------------------------------------

@app.post(
    "/api/parking/ai/recommend",
    response_model=AIRecommendationResponse,
    operation_id="ai_parking_recommendation",
    tags=["AI Features"],
)
async def ai_parking_recommendation(request: AIRecommendationRequest):
    """AI 기반 주차장 추천 (RAG 활용)"""
    # 현재 주차장 데이터 가져오기
    parking_lots = await parking_service.fetch_parking_data(1, 50)
    
    # AI 추천 생성
    recommendation = await ai_service.get_parking_recommendation(request.query, parking_lots)
    
    # RAG 검색 결과
    search_results = await ai_service.search_parking_lots(request.query, request.max_results)
    
    return AIRecommendationResponse(
        recommendation=recommendation,
        search_results=search_results
    )

@app.post(
    "/api/parking/ai/chat",
    response_model=AIChatResponse,
    operation_id="ai_parking_chat",
    tags=["AI Features"],
)
async def ai_parking_chat(request: AIChatRequest):
    """주차 어시스턴트 AI 채팅"""
    parking_lots = await parking_service.fetch_parking_data(1, 50)
    response = await ai_service.chat_with_parking_assistant(request.message, parking_lots)
    
    return AIChatResponse(response=response)

@app.get(
    "/api/parking/ai/strategy/{room_id}",
    response_model=AIStrategyResponse,
    operation_id="ai_game_strategy",
    tags=["AI Features"],
)
async def ai_game_strategy(room_id: str, player_name: str = Query(..., description="플레이어 이름")):
    """AI 게임 전략 코치"""
    room = parking_service.get_game_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="게임 룸을 찾을 수 없습니다")
    
    strategy = await ai_service.generate_game_strategy(room, player_name)
    
    return AIStrategyResponse(strategy=strategy)

@app.get(
    "/api/parking/ai/commentary/{room_id}",
    response_model=AICommentaryResponse,
    operation_id="ai_game_commentary",
    tags=["AI Features"],
)
async def ai_game_commentary(room_id: str):
    """실시간 게임 해설 AI"""
    room = parking_service.get_game_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="게임 룸을 찾을 수 없습니다")
    
    commentary = await ai_service.generate_game_commentary(room)
    
    return AICommentaryResponse(commentary=commentary)

@app.get(
    "/api/parking/ai/search",
    operation_id="ai_parking_search",
    tags=["AI Features"],
)
async def ai_parking_search(query: str = Query(..., description="검색 쿼리"), k: int = Query(3, description="결과 개수")):
    """RAG 기반 주차장 검색"""
    parking_lots = await parking_service.fetch_parking_data(1, 50)
    
    # 지식베이스 구축 (필요시)
    await ai_service.build_parking_knowledge_base(parking_lots)
    
    # 검색 실행
    results = await ai_service.search_parking_lots(query, k)
    
    return {
        "query": query,
        "results": results,
        "total_found": len(results)
    }


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