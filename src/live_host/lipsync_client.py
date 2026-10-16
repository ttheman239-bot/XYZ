"""LiveTalking HTTP client.

LiveTalking (github.com/lipku/LiveTalking) exposes HTTP APIs สำหรับ:
- push เสียงเข้าไป lip-sync กับวิดีโอฐาน
- สั่งเล่น idle action
- interrupt (ตัดเสียงที่กำลังพูด)

หมายเหตุ: endpoint ที่ให้ไว้นี้เป็นแม่แบบ — ตรวจกับ README ของ LiveTalking เวอร์ชันจริง
แล้วแก้ `endpoint_path` ให้ตรง.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import httpx

log = logging.getLogger(__name__)


@dataclass
class LipsyncConfig:
    base_url: str = "http://127.0.0.1:8010"
    session_id: str = "default"
    model: str = "musetalk"
    transport: str = "virtualcam"  # virtualcam | rtmp | webrtc
    rtmp_push_url: str | None = None
    request_timeout_s: float = 30.0


class LiveTalkingClient:
    def __init__(self, config: LipsyncConfig):
        self.config = config
        self._client = httpx.AsyncClient(timeout=config.request_timeout_s)

    async def health(self) -> bool:
        try:
            r = await self._client.get(f"{self.config.base_url}/health")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    async def push_audio(self, wav_path: Path, segment_id: int) -> None:
        """อัปโหลด WAV เข้า session; LiveTalking จะเล่น + lip-sync ต่อเนื่อง."""
        url = f"{self.config.base_url}/sessions/{self.config.session_id}/audio"
        with wav_path.open("rb") as f:
            files = {"file": (wav_path.name, f, "audio/wav")}
            data = {"segment_id": str(segment_id)}
            r = await self._client.post(url, files=files, data=data)
            r.raise_for_status()
        log.info("pushed audio segment %d (%s)", segment_id, wav_path.name)

    async def play_idle(self, action_name: str) -> None:
        url = f"{self.config.base_url}/sessions/{self.config.session_id}/idle"
        r = await self._client.post(url, json={"action": action_name})
        r.raise_for_status()
        log.info("idle → %s", action_name)

    async def interrupt(self) -> None:
        """ตัดเสียงที่กำลังเล่น (ใช้ตอนผู้ควบคุมแทรกข้อความ)."""
        url = f"{self.config.base_url}/sessions/{self.config.session_id}/interrupt"
        r = await self._client.post(url)
        r.raise_for_status()

    async def start_session(self) -> None:
        url = f"{self.config.base_url}/sessions"
        body = {
            "id": self.config.session_id,
            "model": self.config.model,
            "transport": self.config.transport,
        }
        if self.config.rtmp_push_url:
            body["rtmp_push_url"] = self.config.rtmp_push_url
        r = await self._client.post(url, json=body)
        r.raise_for_status()
        log.info("session started: %s (model=%s, transport=%s)",
                 self.config.session_id, self.config.model, self.config.transport)

    async def stop_session(self) -> None:
        url = f"{self.config.base_url}/sessions/{self.config.session_id}"
        try:
            await self._client.delete(url)
        except httpx.HTTPError as exc:
            log.warning("stop_session: %s", exc)

    async def close(self) -> None:
        await self._client.aclose()
