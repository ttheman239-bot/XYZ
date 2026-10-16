"""Unit tests for Thai text normalizer."""

from pathlib import Path

import pytest

from live_host.normalizer import (
    Normalizer,
    baht_to_thai,
    decimal_to_thai,
    number_to_thai,
)


@pytest.mark.parametrize("n,expected", [
    (0, "ศูนย์"),
    (1, "หนึ่ง"),
    (10, "สิบ"),
    (11, "สิบเอ็ด"),
    (20, "ยี่สิบ"),
    (21, "ยี่สิบเอ็ด"),
    (99, "เก้าสิบเก้า"),
    (100, "หนึ่งร้อย"),
    (101, "หนึ่งร้อยเอ็ด"),
    (111, "หนึ่งร้อยสิบเอ็ด"),
    (299, "สองร้อยเก้าสิบเก้า"),
    (1000, "หนึ่งพัน"),
    (1234, "หนึ่งพันสองร้อยสามสิบสี่"),
    (10000, "หนึ่งหมื่น"),
    (100000, "หนึ่งแสน"),
    (1_000_000, "หนึ่งล้าน"),
    (1_234_567, "หนึ่งล้านสองแสนสามหมื่นสี่พันห้าร้อยหกสิบเจ็ด"),
])
def test_number_to_thai(n, expected):
    assert number_to_thai(n) == expected


@pytest.mark.parametrize("amount,expected", [
    ("299", "สองร้อยเก้าสิบเก้าบาท"),
    ("1,299", "หนึ่งพันสองร้อยเก้าสิบเก้าบาท"),
    ("99.50", "เก้าสิบเก้าบาทห้าสิบสตางค์"),
    ("0.25", "ยี่สิบห้าสตางค์"),
    ("100.00", "หนึ่งร้อยบาท"),
])
def test_baht_to_thai(amount, expected):
    assert baht_to_thai(amount) == expected


def test_decimal_to_thai():
    assert decimal_to_thai("3.14") == "สามจุดหนึ่งสี่"
    assert decimal_to_thai("10") == "สิบ"


@pytest.fixture
def normalizer():
    return Normalizer.from_yaml(Path("config/pronunciations.yaml"))


def test_normalize_currency(normalizer):
    assert normalizer.normalize("ราคา ฿299") == "ราคา สองร้อยเก้าสิบเก้าบาท"
    assert normalizer.normalize("ลด 50% เหลือ 1,299 บาท") == \
        "ลด ห้าสิบเปอร์เซ็นต์ เหลือ หนึ่งพันสองร้อยเก้าสิบเก้าบาท"


def test_normalize_brand(normalizer):
    out = normalizer.normalize("ซื้อผ่าน Shopee หรือ Lazada ก็ได้")
    assert "ช็อปปี้" in out
    assert "ลาซาด้า" in out


def test_normalize_bare_number(normalizer):
    out = normalizer.normalize("มีของ 150 ชิ้น")
    assert "หนึ่งร้อยห้าสิบ" in out


def test_split_segments():
    n = Normalizer(max_words=5)
    text = "สวัสดีครับ. วันนี้มาแนะนำสินค้าใหม่ ราคาสุดคุ้ม ลด แรง มากครับ."
    out = n.split_segments(text)
    assert all(len(s.split()) <= 5 for s in out)
    assert len(out) >= 2


def test_pronunciation_overrides_brand_in_mixed_text(normalizer):
    out = normalizer.normalize("Shopee มีโปร COD ด้วยนะครับ")
    assert "ช็อปปี้" in out
    assert "ซี โอ ดี" in out
