"""TTS worker + queue.

- Abstraction `TTSBackend` รองรับหลาย TTS
- `TTSQueue` ทำ pre-generate ล่วงหน้า N segment (buffer)
- Backend: Jaitts / Thonburian / SEBridge / Mock

ตัวจริงต้อง fine-tune per TTS; ที่นี่ให้โครง HTTP wrapper เพื่อให้สลับตัวทดสอบง่าย
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

import httpx

log = logging.getLogger(__name__)


@dataclass
class TTSResult:
    segment_id: int
    audio_path: Path
    duration_s: float


@runtime_checkable
class TTSBackend(Protocol):
    async def synthesize(self, text: str, out_path: Path) -> TTSResult: ...


# ------------------- Backends -------------------

@dataclass
class MockBackend:
    """สร้างไฟล์ WAV ว่าง (silence) ตามความยาวเฉลี่ย — ใช้สำหรับทดสอบ pipeline โดยไม่ต้องมี GPU."""

    sample_rate: int = 24000
    chars_per_second: float = 15.0

    async def synthesize(self, text: str, out_path: Path) -> TTSResult:
        import numpy as np
        import soundfile as sf

        duration = max(0.4, len(text) / self.chars_per_second)
        samples = np.zeros(int(duration * self.sample_rate), dtype=np.float32)
        await asyncio.to_thread(sf.write, str(out_path), samples, self.sample_rate)
        return TTSResult(segment_id=0, audio_path=out_path, duration_s=duration)


@dataclass
class HTTPBackend:
    """TTS แบบ HTTP service — ใช้ได้กับ JaiTTS / Thonburian / SE-Bridge
    ถ้ารันเป็น service แล้ว endpoint รับ { text, voice_sample } คืน WAV
    ปรับ `endpoint_path` ให้ตรงกับ backend ที่เลือก.
    """

    endpoint: str
    voice_sample: Path | None = None
    endpoint_path: str = "/tts"
    speed: float = 1.0
    timeout_s: float = 60.0

    async def synthesize(self, text: str, out_path: Path) -> TTSResult:
        payload: dict = {"text": text, "speed": self.speed}
        if self.voice_sample is not None:
            payload["voice_sample"] = str(self.voice_sample)
        url = self.endpoint.rstrip("/") + self.endpoint_path
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            out_path.write_bytes(resp.content)
        duration = _wav_duration(out_path)
        return TTSResult(segment_id=0, audio_path=out_path, duration_s=duration)


def _wav_duration(path: Path) -> float:
    try:
        import soundfile as sf
        info = sf.info(str(path))
        return info.frames / info.samplerate
    except Exception as exc:
        log.warning("อ่าน duration ไฟล์ wav ไม่สำเร็จ (%s), fallback = 0", exc)
        return 0.0


def build_backend(name: str, **kwargs) -> TTSBackend:
    name = name.lower()
    if name == "mock":
        return MockBackend()
    if name in ("jaitts", "thonburian", "se_bridge"):
        return HTTPBackend(**kwargs)
    raise ValueError(f"unknown TTS backend: {name}")


# ------------------- Queue -------------------

@dataclass
class Segment:
    id: int
    text: str
    product_id: str | None = None
    action: str = "idle"
    pin_cue: bool = False


class TTSQueue:
    """Pre-generate N segment ล่วงหน้าแล้วรอให้ consumer ดึง."""

    def __init__(
        self,
        backend: TTSBackend,
        cache_dir: Path,
        buffer_size: int = 3,
    ):
        self.backend = backend
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._queue: asyncio.Queue[TTSResult] = asyncio.Queue(maxsize=buffer_size)
        self._producer_task: asyncio.Task | None = None

    def start(self, segments: list[Segment]) -> None:
        self._producer_task = asyncio.create_task(self._produce(segments))

    async def _produce(self, segments: list[Segment]) -> None:
        for seg in segments:
            key = hashlib.sha1(seg.text.encode("utf-8")).hexdigest()[:12]
            out = self.cache_dir / f"seg_{seg.id:04d}_{key}.wav"
            if not out.exists():
                log.info("TTS: synth segment %d — %r", seg.id, seg.text[:40])
                result = await self.backend.synthesize(seg.text, out)
            else:
                log.info("TTS: cache hit segment %d", seg.id)
                result = TTSResult(seg.id, out, _wav_duration(out))
            result.segment_id = seg.id
            await self._queue.put(result)

    async def get(self) -> TTSResult:
        return await self._queue.get()

    async def stop(self) -> None:
        if self._producer_task:
            self._producer_task.cancel()
            try:
                await self._producer_task
            except asyncio.CancelledError:
                pass
