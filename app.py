import sys
import os

# Render(또는 어떤 환경이든) 실행 위치에 상관없이 패키지 경로 보장
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from bootstrap.container import build_app
import config

app = build_app()

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
        log_level="info",
    )
