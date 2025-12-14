# 🚗 주차 선점 게임 (ParKing Game)

매일 반복되는 주차 자리 싸움을 게임으로 만들어 스트레스를 해소하는 웹 애플리케이션입니다!

## 🎯 프로젝트 목적

- 주차 자리를 선점하는 게임 형식으로 주차 문제에 대한 스트레스 해소
- 공공 오픈 API를 활용한 실제 주차장 데이터 기반 게임
- 먼저 선점한 주차 자리에 더 이상 스트레스받지 않는 "퇴근길" 경험 제공

## 🚀 주요 기능

### 게임 시스템
- **실시간 주차 공간 선점**: 클릭 한 번으로 주차 공간 선점
- **다양한 주차 타입**: 옥내/옥외 기계식, 자주식 주차 공간 구분
- **멀티플레이어**: 여러 플레이어가 동시에 게임 참여 가능
- **실시간 리더보드**: 가장 많은 주차 공간을 선점한 플레이어 순위

### API 기능
- **주차장 데이터 조회**: 공공 API 연동으로 실제 주차장 정보 제공
- **게임 룸 관리**: 독립적인 게임 세션 생성 및 관리
- **실시간 게임 상태**: 주차 공간 점유 현황 실시간 업데이트

## 🛠 기술 스택

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla JavaScript + HTML/CSS
- **API**: RESTful API + MCP (Model Context Protocol)
- **실시간 통신**: HTTP Polling (향후 WebSocket 업그레이드 예정)

## 📁 프로젝트 구조

```
fastapi_mcp/
├── main.py              # FastAPI 메인 애플리케이션
├── models.py            # Pydantic 데이터 모델
├── parking_service.py   # 주차 게임 비즈니스 로직
├── static/
│   └── index.html      # 게임 웹 인터페이스
├── requirements.txt     # Python 의존성
└── README.md           # 프로젝트 문서
```

## 🎮 게임 플레이 방법

### 1. 서버 실행
```bash
cd fastapi_mcp
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 게임 접속
브라우저에서 `http://localhost:8000` 접속

### 3. 게임 시작
1. **플레이어 이름 입력**
2. **"새 게임 만들기"** 클릭하여 새 게임 룸 생성
3. **주차 공간 클릭**으로 선점하기
4. **리더보드**에서 순위 확인

### 4. 멀티플레이어
- 다른 플레이어는 **룸 ID**를 입력하여 같은 게임에 참가
- 실시간으로 다른 플레이어의 선점 현황 확인 가능

## 🎨 게임 인터페이스

### 주차 공간 표시
- 🟢 **초록색**: 사용 가능한 주차 공간
- 🔴 **빨간색**: 이미 점유된 주차 공간
- **숫자**: 주차 공간 ID
- **호버 효과**: 선점 가능한 공간에 마우스 오버 시 확대

### 실시간 통계
- **전체 주차 공간 수**
- **점유된 공간 수**
- **사용 가능한 공간 수**
- **플레이어별 선점 순위**

## 🔧 API 엔드포인트

### 주차장 정보
- `GET /api/parking/lots` - 주차장 목록 조회

### 게임 관리
- `POST /api/parking/game/create` - 새 게임 룸 생성
- `GET /api/parking/game/{room_id}` - 게임 룸 정보 조회
- `POST /api/parking/game/{room_id}/join` - 게임 참가
- `POST /api/parking/game/occupy` - 주차 공간 선점
- `GET /api/parking/game/{room_id}/stats` - 게임 통계 조회

### API 문서
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔮 향후 개발 계획

### 단기 계획
- [ ] 실제 공공 API 연동 (현재는 목업 데이터 사용)
- [ ] WebSocket을 통한 실시간 업데이트
- [ ] 주차 공간 타입별 색상 구분
- [ ] 게임 시간 제한 기능

### 중기 계획
- [ ] 사용자 계정 시스템
- [ ] 게임 히스토리 저장
- [ ] 주차장별 랭킹 시스템
- [ ] 모바일 앱 개발

### 장기 계획
- [ ] 실제 주차장과의 IoT 연동
- [ ] AR/VR 인터페이스
- [ ] 주차 예약 시스템 통합

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 연락처

프로젝트 관련 문의사항이 있으시면 언제든 연락주세요!

---

**주차 스트레스, 이제 게임으로 해결하세요! 🎮🚗**