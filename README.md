# Dungeon Defender – Web Edition

과제 5 (pygame 버전) → FastAPI + HTML Canvas 웹 서버로 변환한 버전입니다.

## 폴더 구조

```
dungeon_defender/
├── app.py                   # 엔트리포인트 (uvicorn 실행)
├── config.py                # 상수 설정
├── requirements.txt
│
├── bootstrap/               # DI / 앱 조립
│   └── container.py         # FastAPI 앱 + WebSocket 라우팅
│
├── domain/                  # 순수 도메인 모델 (비즈니스 엔티티)
│   └── entities.py          # Player, Enemy, Boss, Bullet, Particle …
│
├── data/                    # 게임 상태 저장소
│   └── game_state.py        # GameState dataclass
│
├── services/                # 게임 로직 (규칙)
│   └── game_service.py      # tick(), set_key(), activate_ultimate()
│
├── infrastructure/          # 직렬화 / 외부 어댑터
│   └── serializer.py        # GameState → JSON dict
│
├── interfaces/              # HTML 뷰 템플릿
│   └── index.html
│
└── static/
    ├── js/renderer.js       # Canvas 렌더러 (브라우저 측)
    └── css/style.css
```

## 실행 방법

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python app.py
# 또는
uvicorn app:app --host 0.0.0.0 --port 7860
```

브라우저에서 `http://localhost:7860` 접속

## 조작 방법

| 키 | 동작 |
|----|------|
| ← → | 좌우 이동 |
| ↑ ↓ | 상하 이동 |
| SPACE | 신성한 화살 발사 (홀드) |
| Q | 궁극기 – 홀리 라이트 (게이지 가득 찰 때) |

## 클라우드 배포 (예시)

### Hugging Face Spaces (권장, 무료)
1. Spaces 생성 → SDK: **Docker** 선택
2. 이 폴더 전체 업로드
3. `Dockerfile` 추가:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 7860
CMD ["python", "app.py"]
```

### Railway / Render
- `python app.py` 를 Start Command로 설정
- PORT 환경변수 `7860` 지정
