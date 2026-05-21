"""
FastAPI + WebSocket server.
Each browser tab gets its own GameSession (independent game state).
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from data.game_state import GameState
from services.game_service import tick, set_key, activate_ultimate, init_bg_particles
from infrastructure.serializer import serialize
import config

BASE_DIR = Path(__file__).parent.parent  # project root


class GameSession:
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.state = GameState()
        self.start_time = datetime.now()
        init_bg_particles(self.state)

    def handle_message(self, msg: dict):
        mtype = msg.get("type")
        s = self.state

        if mtype == "start" and s.phase == "title":
            s.phase = "playing"
            self.start_time = datetime.now()

        elif mtype == "restart":
            self.state = GameState()
            init_bg_particles(self.state)

        elif mtype == "keydown":
            set_key(s, msg.get("key", ""), True)

        elif mtype == "keyup":
            set_key(s, msg.get("key", ""), False)

        elif mtype == "ultimate":
            activate_ultimate(s)

    def step(self):
        elapsed = int((datetime.now() - self.start_time).total_seconds())
        tick(self.state, elapsed)
        return serialize(self.state)


def build_app() -> FastAPI:
    app = FastAPI()

    # static files
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    # HTML page
    html_path = BASE_DIR / "interfaces" / "index.html"

    @app.get("/", response_class=HTMLResponse)
    async def root():
        return html_path.read_text(encoding="utf-8")

    # WebSocket endpoint – one per browser tab
    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        await ws.accept()
        session = GameSession(ws)

        async def recv_loop():
            while True:
                try:
                    raw = await ws.receive_text()
                    msg = json.loads(raw)
                    session.handle_message(msg)
                except (WebSocketDisconnect, Exception):
                    break

        async def send_loop():
            try:
                while True:
                    frame = session.step()
                    await ws.send_text(json.dumps(frame))
                    await asyncio.sleep(1 / config.FPS)
            except (WebSocketDisconnect, Exception):
                pass

        recv_task = asyncio.create_task(recv_loop())
        send_task = asyncio.create_task(send_loop())
        done, pending = await asyncio.wait(
            [recv_task, send_task], return_when=asyncio.FIRST_COMPLETED
        )
        for t in pending:
            t.cancel()

    return app
