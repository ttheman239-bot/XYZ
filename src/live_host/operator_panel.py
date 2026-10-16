"""Operator Panel — FastAPI + WebSocket + static HTML (minimal).

ทำได้: ดู segment ปัจจุบัน / pin cue, แทรกประโยค, pause/skip

หมายเหตุ: นี่คือโครงเริ่มต้น (M3) — ตัวจริงต้องผูกกับ Orchestrator ผ่าน shared state หรือ pub/sub
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

log = logging.getLogger(__name__)


@dataclass
class PanelState:
    current_segment_id: int = 0
    current_text: str = ""
    pin_cue: str | None = None
    paused: bool = False
    inject_queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)
    _ws_clients: set[WebSocket] = field(default_factory=set)

    async def broadcast(self, event: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self._ws_clients:
            try:
                await ws.send_text(json.dumps(event, ensure_ascii=False))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._ws_clients.discard(ws)

    def snapshot(self) -> dict:
        return {
            "current_segment_id": self.current_segment_id,
            "current_text": self.current_text,
            "pin_cue": self.pin_cue,
            "paused": self.paused,
        }


HTML_PAGE = """<!doctype html>
<html lang="th"><head>
<meta charset="utf-8"><title>Operator Panel</title>
<style>
  body { font-family: system-ui, sans-serif; background: #0b1020; color: #e6ecff; margin: 0; padding: 24px; }
  h1 { font-size: 20px; margin: 0 0 16px; }
  .card { background: #1b2447; padding: 16px; border-radius: 12px; margin-bottom: 12px; }
  .pin { background: #ff7df9; color: #0b1020; font-weight: 600; }
  button { padding: 8px 14px; border: 0; border-radius: 999px; background: #7df9ff; color: #0b1020; margin-right: 8px; cursor: pointer; }
  input { padding: 8px 12px; border-radius: 999px; border: 1px solid #2c3a73; background: #0b1020; color: #e6ecff; width: 60%; }
</style></head>
<body>
<h1>🎙 Thai AI Live Host — Operator Panel</h1>
<div class="card"><strong>Segment #<span id="sid">—</span></strong><div id="text" style="margin-top:8px">—</div></div>
<div class="card pin" id="pin" style="display:none"></div>
<div class="card">
  <input id="inject" placeholder="พิมพ์แล้วกด Enter เพื่อแทรกคำพูด..." />
  <button onclick="togglePause()">Pause/Resume</button>
  <button onclick="skip()">Skip segment</button>
</div>
<script>
const ws = new WebSocket(`ws://${location.host}/ws`);
ws.onmessage = e => {
  const s = JSON.parse(e.data);
  document.getElementById('sid').textContent = s.current_segment_id || '—';
  document.getElementById('text').textContent = s.current_text || '—';
  const pin = document.getElementById('pin');
  if (s.pin_cue) { pin.style.display='block'; pin.textContent = '📌 ' + s.pin_cue; }
  else pin.style.display='none';
};
document.getElementById('inject').addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.target.value.trim()) {
    fetch('/api/inject', { method:'POST', headers:{'content-type':'application/json'},
      body: JSON.stringify({ text: e.target.value })});
    e.target.value = '';
  }
});
function togglePause() { fetch('/api/pause', { method:'POST' }); }
function skip() { fetch('/api/skip', { method:'POST' }); }
</script>
</body></html>
"""


def create_app(state: PanelState) -> FastAPI:
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return HTML_PAGE

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        state._ws_clients.add(ws)
        await ws.send_text(json.dumps(state.snapshot(), ensure_ascii=False))
        try:
            while True:
                await ws.receive_text()  # client-ping
        except WebSocketDisconnect:
            state._ws_clients.discard(ws)

    @app.post("/api/inject")
    async def inject(payload: dict) -> dict:
        text = (payload.get("text") or "").strip()
        if text:
            await state.inject_queue.put(text)
        return {"ok": True}

    @app.post("/api/pause")
    async def pause() -> dict:
        state.paused = not state.paused
        await state.broadcast({"paused": state.paused, **state.snapshot()})
        return {"paused": state.paused}

    @app.post("/api/skip")
    async def skip() -> dict:
        await state.inject_queue.put("__SKIP__")
        return {"ok": True}

    return app


def run() -> None:
    import uvicorn
    state = PanelState()
    app = create_app(state)
    uvicorn.run(app, host="127.0.0.1", port=8765)


if __name__ == "__main__":
    run()
