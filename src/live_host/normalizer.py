"""Thai text normalizer for TTS.

- ตัวเลข / ราคา / เปอร์เซ็นต์ → คำอ่านไทย
- brand ภาษาอังกฤษ → คำอ่านไทยจาก pronunciations.yaml
- ตัดประโยคยาว > N คำเป็นหลาย segment
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_DIGITS = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
_PLACES = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน"]


def number_to_thai(n: int) -> str:
    """Convert non-negative integer → Thai reading. รองรับ 0..999_999_999_999."""
    if n < 0:
        return "ลบ" + number_to_thai(-n)
    if n == 0:
        return "ศูนย์"
    if n >= 1_000_000:
        high, low = divmod(n, 1_000_000)
        return number_to_thai(high) + "ล้าน" + (number_to_thai(low) if low else "")

    s = str(n)
    length = len(s)
    out = []
    for i, ch in enumerate(s):
        d = int(ch)
        pos = length - i - 1
        if d == 0:
            continue
        if pos == 1 and d == 1:
            out.append("สิบ")
        elif pos == 1 and d == 2:
            out.append("ยี่สิบ")
        elif pos == 0 and d == 1 and length > 1:
            out.append("เอ็ด")
        else:
            out.append(_DIGITS[d] + _PLACES[pos])
    return "".join(out)


def decimal_to_thai(num_str: str) -> str:
    """เช่น "99.50" → "เก้าสิบเก้าจุดห้าศูนย์"  (ใช้ภายใน currency ก่อนแปลงเป็นสตางค์)"""
    if "." not in num_str:
        return number_to_thai(int(num_str))
    whole, frac = num_str.split(".", 1)
    frac = frac.rstrip("0")
    if not frac:
        return number_to_thai(int(whole))
    frac_th = "".join(_DIGITS[int(d)] if int(d) else "ศูนย์" for d in frac)
    return number_to_thai(int(whole)) + "จุด" + frac_th


def baht_to_thai(amount_str: str) -> str:
    """เช่น "299" → "สองร้อยเก้าสิบเก้าบาท", "99.50" → "เก้าสิบเก้าบาทห้าสิบสตางค์"."""
    amount_str = amount_str.replace(",", "").strip()
    if "." in amount_str:
        baht, satang = amount_str.split(".", 1)
        satang = (satang + "00")[:2]
        baht_i = int(baht) if baht else 0
        satang_i = int(satang)
        parts = []
        if baht_i:
            parts.append(number_to_thai(baht_i) + "บาท")
        if satang_i:
            parts.append(number_to_thai(satang_i) + "สตางค์")
        return "".join(parts) or "ศูนย์บาท"
    return number_to_thai(int(amount_str)) + "บาท"


_RE_BAHT = re.compile(r"฿\s*([\d,]+(?:\.\d+)?)|([\d,]+(?:\.\d+)?)\s*บาท")
_RE_PERCENT = re.compile(r"([\d,]+(?:\.\d+)?)\s*%")
_RE_PLAIN_NUM = re.compile(r"(?<!\w)(-?\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?!\w)")


@dataclass
class Normalizer:
    """Thai text normalizer with configurable brand/unit dictionary."""

    pronunciations: dict[str, str] = field(default_factory=dict)
    max_words: int = 20

    @classmethod
    def from_yaml(cls, path: Path | str, max_words: int = 20) -> "Normalizer":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        flat: dict[str, str] = {}
        for section in ("brands", "units", "common"):
            for k, v in (data.get(section) or {}).items():
                flat[str(k).lower()] = str(v)
        return cls(pronunciations=flat, max_words=max_words)

    def normalize(self, text: str) -> str:
        """One pass: currency, percent, dictionary, bare numbers."""
        text = _RE_BAHT.sub(
            lambda m: baht_to_thai(m.group(1) or m.group(2)), text
        )
        text = _RE_PERCENT.sub(
            lambda m: decimal_to_thai(m.group(1).replace(",", "")) + "เปอร์เซ็นต์",
            text,
        )
        text = self._replace_dictionary(text)
        text = _RE_PLAIN_NUM.sub(
            lambda m: decimal_to_thai(
                (m.group(1) + (m.group(2) or "")).replace(",", "")
            ),
            text,
        )
        return re.sub(r"\s+", " ", text).strip()

    def _replace_dictionary(self, text: str) -> str:
        if not self.pronunciations:
            return text
        # longest key first — "pre-order" ก่อน "pre"
        keys = sorted(self.pronunciations.keys(), key=len, reverse=True)
        for key in keys:
            pattern = re.compile(
                r"(?<![a-zA-Z])" + re.escape(key) + r"(?![a-zA-Z])",
                re.IGNORECASE,
            )
            text = pattern.sub(self.pronunciations[key], text)
        return text

    def split_segments(self, text: str) -> list[str]:
        """ตัดประโยคยาวเป็นหลายท่อน (ขอบเขต: . ! ? ฯ และวรรค space)."""
        parts = re.split(r"(?<=[.!?ฯ])\s+", text)
        result: list[str] = []
        for part in parts:
            words = part.split()
            if len(words) <= self.max_words:
                if part.strip():
                    result.append(part.strip())
                continue
            # ตัดด้วย comma หรือกลุ่มคำ
            chunks = re.split(r"[,،]", part)
            buf: list[str] = []
            for c in chunks:
                buf.extend(c.split())
                if len(buf) >= self.max_words:
                    result.append(" ".join(buf).strip())
                    buf = []
            if buf:
                result.append(" ".join(buf).strip())
        return [r for r in result if r]
