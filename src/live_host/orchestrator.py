"""Orchestrator — ร้อยทุกส่วนเข้าด้วยกัน.

flow:
  product dict → ScriptEngine → segments
                     ↓
                 Normalizer (ปรับข้อความ, ตัด > N คำ)
                     ↓
                 TTSQueue (pre-generate ล่วงหน้า)
                     ↓
                 LiveTalking (push audio, play idle, pin cue)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .lipsync_client import LipsyncConfig, LiveTalkingClient
from .normalizer import Normalizer
from .script_engine import ScriptConfig, ScriptEngine
from .tts_worker import Segment, TTSQueue, build_backend

log = logging.getLogger(__name__)


@dataclass
class PinCue:
    """ข้อความเตือนให้ operator ปักสินค้าในหน้าแชท."""
    segment_id: int
    product_id: str
    message: str


class Orchestrator:
    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)
        self.config = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        self.cache_dir = Path("cache/tts")
        self._pin_cues: list[PinCue] = []

    def _build_normalizer(self) -> Normalizer:
        pron_file = self.config["normalizer"]["pronunciations_file"]
        return Normalizer.from_yaml(
            pron_file,
            max_words=self.config["normalizer"].get("max_words_per_segment", 20),
        )

    def _build_script_engine(self) -> ScriptEngine:
        c = self.config["script_engine"]
        return ScriptEngine(
            ScriptConfig(
                model=c["model"],
                max_tokens=c.get("max_tokens", 2048),
                temperature=c.get("temperature", 0.4),
                cache_system_prompt=c.get("cache_system_prompt", True),
            )
        )

    def _build_tts_queue(self) -> TTSQueue:
        tc = self.config["tts"]
        kwargs: dict[str, Any] = {}
        if tc["backend"] != "mock":
            kwargs = {
                "endpoint": tc["endpoint"],
                "voice_sample": Path(tc["voice_sample"]) if tc.get("voice_sample") else None,
                "speed": tc.get("speed", 1.0),
            }
        backend = build_backend(tc["backend"], **kwargs)
        return TTSQueue(backend, self.cache_dir, buffer_size=tc.get("buffer_segments", 3))

    def _build_lipsync(self) -> LiveTalkingClient:
        lc = self.config["lipsync"]
        return LiveTalkingClient(LipsyncConfig(
            base_url=lc["base_url"],
            session_id=lc.get("session_id", "default"),
            model=lc.get("model", "musetalk"),
            transport=lc.get("transport", "virtualcam"),
            rtmp_push_url=lc.get("rtmp_push_url"),
        ))

    async def run_product(self, product: dict[str, Any]) -> None:
        normalizer = self._build_normalizer()
        engine = self._build_script_engine()
        tts = self._build_tts_queue()
        lip = self._build_lipsync()

        log.info("1/4 generate script via Claude...")
        raw = engine.generate(product)

        log.info("2/4 normalize + split segments...")
        segments: list[Segment] = []
        next_id = 1
        for s in raw:
            text = normalizer.normalize(s["text"])
            for chunk in normalizer.split_segments(text) or [text]:
                segments.append(Segment(
                    id=next_id,
                    text=chunk,
                    product_id=s.get("product_id"),
                    action=s.get("action", "idle"),
                    pin_cue=s.get("pin_cue", False),
                ))
                next_id += 1
        log.info("   → %d segments", len(segments))

        log.info("3/4 start LiveTalking session + prime TTS queue...")
        await lip.start_session()
        tts.start(segments)

        log.info("4/4 stream segments...")
        try:
            for seg in segments:
                result = await tts.get()
                if seg.action and seg.action != "idle":
                    try:
                        await lip.play_idle(seg.action)
                    except Exception as exc:
                        log.warning("idle action failed: %s", exc)
                await lip.push_audio(result.audio_path, seg.id)
                if seg.pin_cue:
                    cue = PinCue(seg.id, seg.product_id or "?", f"ปักสินค้า {seg.product_id} ตอนนี้")
                    self._pin_cues.append(cue)
                    log.warning("📌 PIN CUE: %s", cue.message)
                # รอให้ segment เล่นจบประมาณ ๆ (ปรับตามจริง)
                await asyncio.sleep(result.duration_s * 0.9)
        finally:
            await tts.stop()
            await lip.stop_session()
            await lip.close()
