"""Script Engine — call Claude API, return segments JSON.

Input:  product info dict
Output: {"segments": [{id, product_id, text, action, pin_cue}, ...]}

ใช้ Anthropic SDK + prompt caching (ลด cost ของ system prompt ที่คงที่)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import anthropic
except ImportError:  # ให้ import module ได้โดยไม่ครั้ง install ทุกคน
    anthropic = None  # type: ignore[assignment]


SYSTEM_PROMPT = """คุณเป็นสคริปต์ไรเตอร์มืออาชีพสำหรับไลฟ์ขายของภาษาไทย

หน้าที่: รับข้อมูลสินค้า แล้วแต่งสคริปต์ไลฟ์แบ่งเป็น segment สั้น ๆ

กฎการเขียน:
1. 1 segment = 1-2 ประโยค ยาวไม่เกิน 20 คำ (จะถูกส่งเข้า TTS ทีละอัน)
2. ภาษาธรรมชาติ เหมือนคนไลฟ์ ไม่ใช่โฆษณาแข็ง
3. ห้ามอ้างสรรพคุณเกินจริง — โดยเฉพาะอาหาร/ยา/เครื่องสำอาง
4. ห้ามใช้คำว่า "รักษา" "หาย" "ที่สุด" "100%" กับสินค้าที่ไม่มีหลักฐาน
5. ถ้าเป็นสินค้าใหม่/ลดราคา/ของแถม ให้ใส่ pin_cue=true ใน segment ที่กระตุ้นให้กด (ให้คนไลฟ์ปักเอง)
6. action เลือกจาก: idle, point, smile, nod — ให้สอดคล้องเนื้อความ

Output: JSON เท่านั้น ไม่มีคำนำ ไม่มี markdown ไม่มี ```

{
  "segments": [
    {"id": 1, "product_id": "A01", "text": "...", "action": "smile", "pin_cue": false},
    ...
  ]
}
"""


@dataclass
class ScriptConfig:
    model: str = "claude-sonnet-5-5"
    max_tokens: int = 2048
    temperature: float = 0.4
    cache_system_prompt: bool = True


class ScriptEngine:
    def __init__(self, config: ScriptConfig | None = None, api_key: str | None = None):
        if anthropic is None:
            raise RuntimeError("กรุณา `pip install anthropic`")
        self.config = config or ScriptConfig()
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )

    def generate(self, product: dict[str, Any]) -> list[dict[str, Any]]:
        """Return list of segment dicts; raises on invalid JSON."""
        user_msg = (
            "ข้อมูลสินค้า (JSON):\n"
            + json.dumps(product, ensure_ascii=False, indent=2)
            + "\n\nแต่งสคริปต์ไลฟ์ 8-15 segment ครอบคลุม: ทักทาย, "
            "แนะนำสินค้า, จุดขาย, ราคา/โปรโมชัน (ถ้ามี), กระตุ้นให้กด, ปิดการขาย"
        )

        system = (
            [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]
            if self.config.cache_system_prompt
            else SYSTEM_PROMPT
        )

        resp = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        data = json.loads(_strip_fences(text))
        segments = data.get("segments")
        if not isinstance(segments, list):
            raise ValueError("Claude ไม่ได้คืน 'segments' เป็น array")
        return segments


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        first_nl = text.find("\n")
        text = text[first_nl + 1 :] if first_nl != -1 else text
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def cli() -> None:
    p = argparse.ArgumentParser(description="Generate live-host script segments from product JSON")
    p.add_argument("--product-file", type=Path, required=True)
    p.add_argument("--model", default="claude-sonnet-5-5")
    p.add_argument("--out", type=Path, help="เขียน segments JSON ลงไฟล์ (ถ้าไม่ระบุ พิมพ์ลง stdout)")
    args = p.parse_args()

    product = json.loads(args.product_file.read_text(encoding="utf-8"))
    engine = ScriptEngine(ScriptConfig(model=args.model))
    segments = engine.generate(product)
    output = json.dumps({"segments": segments}, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(output, encoding="utf-8")
        print(f"wrote {len(segments)} segments → {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    cli()
