import os
from typing import List, Dict, Optional
from models import ParkingLot, GameRoom
import json
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class ParkingAIService:
    def __init__(self):
        # Gemini API 키 설정 (환경변수에서 가져오기)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables")
            self.model = None
            return
            
        # Gemini 클라이언트 초기화
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.parking_knowledge_base = []
        
    async def build_parking_knowledge_base(self, parking_lots: List[ParkingLot]):
        """주차장 데이터로 지식베이스 구축 (간단한 텍스트 검색)"""
        if not self.model:
            return
            
        self.parking_knowledge_base = []
        
        for lot in parking_lots:
            # 주차장 정보를 텍스트로 변환
            content = f"""
            주차장 정보:
            - 위치: {lot.대지위치주소}
            - 건축면적: {lot.건축면적}㎡
            - 총 주차대수: {lot.총_주차대수}대
            - 옥내 기계식: {lot.옥내_기계식_주차대수}대
            - 옥외 기계식: {lot.옥외_기계식_주차대수}대  
            - 옥내 자주식: {lot.옥내_자주식_주차대수}대
            - 옥외 자주식: {lot.옥외_자주식_주차대수}대
            
            특징: 이 주차장은 {lot.대지위치주소}에 위치하며, 
            총 {lot.총_주차대수}개의 주차공간을 보유하고 있습니다.
            """
            
            self.parking_knowledge_base.append({
                "content": content,
                "metadata": {
                    "순번": lot.순번,
                    "주소": lot.대지위치주소,
                    "총_주차대수": lot.총_주차대수
                }
            })
        
    async def search_parking_lots(self, query: str, k: int = 3) -> List[Dict]:
        """자연어 쿼리로 주차장 검색 (간단한 키워드 매칭)"""
        if not self.parking_knowledge_base:
            return []
            
        # 간단한 키워드 매칭
        results = []
        query_lower = query.lower()
        
        for item in self.parking_knowledge_base:
            content_lower = item["content"].lower()
            # 키워드가 포함되어 있으면 결과에 추가
            if any(keyword in content_lower for keyword in query_lower.split()):
                results.append({
                    "content": item["content"],
                    "metadata": item["metadata"],
                    "relevance_score": "높음"
                })
                
        return results[:k]
    
    async def get_parking_recommendation(self, query: str, parking_lots: List[ParkingLot]) -> str:
        """AI 주차장 추천"""
        if not self.model:
            return "AI 서비스를 사용하려면 Gemini API 키가 필요합니다."
            
        # 지식베이스 구축
        if not self.parking_knowledge_base:
            await self.build_parking_knowledge_base(parking_lots)
            
        # 관련 주차장 검색
        search_results = await self.search_parking_lots(query, 3)
        
        # 검색 결과를 컨텍스트로 구성
        context = "\n".join([result["content"] for result in search_results])
        
        # 프롬프트 구성
        prompt = f"""
        사용자 질문: {query}
        
        관련 주차장 정보:
        {context}
        
        위 정보를 바탕으로 사용자의 질문에 가장 적합한 주차장을 추천해주세요.
        추천 이유와 함께 구체적인 정보를 제공해주세요.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            # 기본 추천 로직
            if search_results:
                best_result = search_results[0]
                return f"""
                📍 추천 주차장:
                
                {best_result['content']}
                
                추천 이유: 검색 조건 '{query}'에 가장 적합한 주차장입니다.
                """
            else:
                return f"'{query}' 조건에 맞는 주차장을 찾지 못했습니다. 다른 검색어를 시도해보세요."
    
    async def generate_game_strategy(self, game_room: GameRoom, player_name: str) -> str:
        """게임 전략 AI 코치"""
        if not self.model:
            return "AI 서비스를 사용하려면 Gemini API 키가 필요합니다."
            
        # 게임 상황 분석
        total_spaces = len(game_room.parking_lot.spaces)
        occupied_spaces = sum(1 for space in game_room.parking_lot.spaces 
                            if space.status.value == "occupied")
        available_spaces = total_spaces - occupied_spaces
        
        # 플레이어 현재 점유 공간
        player_spaces = sum(1 for space in game_room.parking_lot.spaces 
                          if space.occupied_by == player_name)
        
        prompt = f"""
        주차 게임 전략 분석:
        
        게임 상황:
        - 총 주차공간: {total_spaces}개
        - 점유된 공간: {occupied_spaces}개  
        - 남은 공간: {available_spaces}개
        - 참가자 수: {len(game_room.players)}명
        - {player_name}님의 현재 점유 공간: {player_spaces}개
        
        위 상황을 바탕으로 {player_name}님에게 최적의 게임 전략을 제안해주세요.
        어떤 타입의 주차공간을 우선적으로 노려야 하는지, 
        경쟁 상황에서 어떻게 대응해야 하는지 구체적으로 조언해주세요.
        """
        
        try:
            full_prompt = "당신은 게임 전략 전문 AI 코치입니다.\n\n" + prompt
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            # 기본 전략 제공
            if available_spaces > occupied_spaces:
                strategy = "🎯 현재 게임 초반입니다. 빠르게 여러 공간을 선점하세요!"
            elif available_spaces < 10:
                strategy = "⚡ 게임 막바지입니다. 남은 공간을 신속하게 확보하세요!"
            else:
                strategy = "🏃‍♂️ 중반전입니다. 전략적으로 좋은 위치의 공간을 노리세요!"
            
            return f"""
            🎮 {player_name}님을 위한 게임 전략:
            
            현재 상황:
            - 총 {total_spaces}개 공간 중 {occupied_spaces}개 점유됨
            - 당신의 점유 공간: {player_spaces}개
            - 경쟁자: {len(game_room.players)-1}명
            
            {strategy}
            
            💡 팁: 옥내 자주식 공간이 일반적으로 선호도가 높습니다!
            """
    
    async def generate_game_commentary(self, game_room: GameRoom) -> str:
        """실시간 게임 해설"""
        if not self.model:
            return "AI 서비스를 사용하려면 Gemini API 키가 필요합니다."
            
        # 리더보드 생성
        leaderboard = {}
        for space in game_room.parking_lot.spaces:
            if space.occupied_by:
                leaderboard[space.occupied_by] = leaderboard.get(space.occupied_by, 0) + 1
        
        # 순위 정렬
        sorted_players = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
        
        prompt = f"""
        주차 게임 실시간 해설:
        
        게임 룸: {game_room.room_id}
        주차장 위치: {game_room.parking_lot.대지위치주소}
        
        현재 순위:
        {chr(10).join([f"{i+1}위: {player} ({score}개 점유)" for i, (player, score) in enumerate(sorted_players)])}
        
        총 {len(game_room.parking_lot.spaces)}개 공간 중 {sum(leaderboard.values())}개가 점유되었습니다.
        
        위 상황을 바탕으로 흥미진진한 게임 해설을 해주세요. 
        스포츠 중계처럼 생동감 있게 현재 상황을 설명하고, 
        앞으로의 전개를 예측해주세요.
        """
        
        try:
            full_prompt = "당신은 스포츠 해설 전문 AI입니다.\n\n" + prompt
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            # 기본 해설 제공
            total_occupied = sum(leaderboard.values())
            progress = (total_occupied / len(game_room.parking_lot.spaces)) * 100
            
            if sorted_players:
                leader = sorted_players[0]
                commentary = f"""
                🎙️ 실시간 게임 해설:
                
                현재 {game_room.parking_lot.대지위치주소}에서 치열한 주차 선점 게임이 펼쳐지고 있습니다!
                
                🏆 현재 1위는 {leader[0]}님으로 {leader[1]}개의 공간을 선점하고 있습니다!
                
                📊 게임 진행률: {progress:.1f}% ({total_occupied}/{len(game_room.parking_lot.spaces)})
                
                🔥 참가자들 간의 경쟁이 점점 치열해지고 있습니다!
                """
            else:
                commentary = f"""
                🎙️ 게임이 막 시작되었습니다!
                
                {len(game_room.players)}명의 플레이어가 {len(game_room.parking_lot.spaces)}개의 주차 공간을 두고 경쟁합니다.
                
                과연 누가 가장 많은 공간을 선점할 수 있을까요?
                """
            
            return commentary
    
    async def chat_with_parking_assistant(self, message: str, parking_lots: List[ParkingLot]) -> str:
        """주차 어시스턴트 채팅"""
        if not self.model:
            return "AI 서비스를 사용하려면 Gemini API 키가 필요합니다."
            
        # 지식베이스 구축 (필요시)
        if not self.parking_knowledge_base:
            await self.build_parking_knowledge_base(parking_lots)
        
        # 간단한 채팅 응답
        prompt = f"""
        당신은 주차장 전문 AI 어시스턴트입니다.
        사용자의 주차 관련 질문에 친절하고 정확하게 답변해주세요.
        
        사용자 질문: {message}
        
        주차장 정보, 게임 규칙, 전략 등에 대해 도움을 드리겠습니다.
        """
        
        try:
            full_prompt = "당신은 주차장 전문 AI 어시스턴트입니다.\n\n" + prompt
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            # Gemini API 오류 시 기본 응답 제공
            if "주차 게임" in message.lower():
                return """
                🎮 주차 선점 게임 규칙:
                
                1. 실제 주차장 데이터를 기반으로 게임이 진행됩니다
                2. 여러 플레이어가 동시에 참가할 수 있습니다
                3. 주차 공간을 선착순으로 선점하는 게임입니다
                4. 가장 많은 주차 공간을 선점한 플레이어가 승리합니다
                5. 주차 공간 타입: 옥내/옥외 기계식, 옥내/옥외 자주식
                
                게임 플로우:
                - 주차장 선택 → 게임 룸 생성 → 플레이어 참가 → 주차 공간 선점 → 결과 확인
                """
            elif "추천" in message.lower():
                return "주차장 추천을 위해서는 구체적인 조건을 알려주세요. 예: 위치, 주차 타입, 규모 등"
            else:
                return f"죄송합니다. AI 서비스에 일시적인 문제가 있습니다: {str(e)}"

# 싱글톤 인스턴스
ai_service = ParkingAIService()