# CONTEXT: Thai AI Digital Human — Live Host พูดตามสคริปต์

> เอกสารนี้ใช้เป็น context ให้ Claude Code สร้างระบบ
> สถานะข้อมูล: ค้นคว้า ณ 16 ต.ค. 2026 — ทุกข้อแยกเป็น ✅ ยืนยันจากแหล่งที่มา / ⚠ ยังไม่ยืนยัน ต้องทดสอบก่อนใช้

---

## 0. เป้าหมาย

สร้างระบบที่รับ **ข้อมูลสินค้า → สคริปต์ภาษาไทย → เสียงไทย → วิดีโอคนพูดขยับปากตรงเสียงแบบเรียลไทม์ → ส่งออกเป็นกล้อง/สตรีม** เพื่อใช้ไลฟ์ขายของ

**หลักการออกแบบ:** สคริปต์รู้ล่วงหน้า → สร้างเสียงล่วงหน้าเป็นคิวได้ ไม่ต้องพึ่ง TTS แบบ real-time
ส่วนที่ต้อง real-time จริงมีแค่ **lip-sync + การส่งภาพออก**

**นอกขอบเขต (ไม่ทำ):** การปักตะกร้า/ปักสินค้าอัตโนมัติผ่าน API ที่ reverse-engineer — ให้คนกดเอง ระบบแค่ขึ้นคิวเตือน

---

## 1. สถาปัตยกรรม

```
[Product input: ชื่อ/ราคา/จุดขาย]
        │
        ▼
[1. Script Engine]  LLM แต่งสคริปต์แบ่งเป็น segment (1 segment = 1-2 ประโยค, ผูก product_id)
        │
        ▼
[2. Thai Text Normalizer]  แปลงตัวเลข/ราคา/ชื่อแบรนด์อังกฤษ → คำอ่านไทย
        │
        ▼
[3. TTS Worker (Thai voice clone)]  สร้าง WAV ล่วงหน้า เก็บเป็นคิว (buffer ≥ 3 segment)
        │
        ▼
[4. Lip-sync Renderer]  LiveTalking + MuseTalk 1.5 / Wav2Lip  ← ใช้วิดีโอฐานคนจริง
        │
        ▼
[5. Output]  Virtual Camera / RTMP  →  OBS  →  แพลตฟอร์มไลฟ์
        │
[6. Operator Panel]  แสดง segment ปัจจุบัน + "ให้ปักสินค้า X ตอนนี้", ปุ่ม pause/skip/แทรกประโยค
```

---

## 2. ส่วนประกอบ (ตัวเลือกหลัก + สำรอง)

### 2.1 Lip-sync engine — ✅ แกนหลักของระบบ
ใช้ **LiveTalking** (github.com/lipku/LiveTalking) เป็นฐาน — ไม่เขียนใหม่
- รองรับ ernerf, musetalk, wav2lip, Ultralight-Digital-Human
- ส่งออก WebRTC, RTMP, virtual camera
- ตัดเสียงกลางคัน / แทรกเสียง / idle action ได้
- Apache 2.0 (เวอร์ชันโอเพนซอร์ส)

FPS จาก README:

| โมเดล | GPU | FPS |
|---|---|---|
| wav2lip256 | RTX 3060 | 60 |
| wav2lip256 | RTX 3080Ti | 120 |
| musetalk | RTX 3080Ti | 42 |
| musetalk | RTX 4090 | 72 |

⚠ ตรวจ license ของ **model weights** MuseTalk แยกจาก license โค้ด ก่อนใช้เชิงพาณิชย์

### 2.2 Thai TTS — ⚠ ต้องเลือกจากการทดสอบจริง

| ตัวเลือก | จุดเด่น | สถานะ |
|---|---|---|
| **JaiTTS** (JTS-AI/JaiTTS-F5TTS) | paper รายงาน CER ต่ำสุด, อ่านตัวเลข+ไทยปนอังกฤษโดยไม่ต้อง normalize | ⚠ ยืนยัน license |
| **ThonburianTTS** (biodatlab) | Thai voice clone จากคลิปสั้น | ⚠ ตรวจ license |
| **SE-Bridge-TTS** | checkpoint ไทย + clone | ⚠ ตรวจคุณภาพ |

**วัด CER:** `typhoon-ai/typhoon-whisper-large-v3` ถอดเสียงกลับมาเทียบ

### 2.3 Script Engine
LLM → JSON:
```json
{"segments": [{"id": 1, "product_id": "A01", "text": "...", "action": "idle|point|smile", "pin_cue": true}]}
```

### 2.4 Thai Text Normalizer
- `฿299` → "สองร้อยเก้าสิบเก้าบาท"
- `50%` → "ห้าสิบเปอร์เซ็นต์"
- brand ภาษาอังกฤษ → พจนานุกรม (แก้ได้)
- ตัด segment > 20 คำ

### 2.5 Output
- virtual camera / RTMP → OBS → Shopee Live PC
- ⚠ บัญชี affiliate ไทยอาจไม่มี Stream Key — ตรวจก่อน

---

## 3. วิดีโอฐาน
- คนจริง + **หนังสือยินยอมเชิงพาณิชย์**
- 1–3 นาที, กล้องนิ่ง, แสงคงที่, หน้าตรง, ไม่มีมือบังหน้า
- อัดแยก (1) ท่าพูด (2) ท่า idle
- เสียง clone 10–30 วิ, ห้องเงียบ

## 4. ฮาร์ดแวร์
- ขั้นต่ำ (wav2lip): RTX 3060
- แนะนำ (MuseTalk): RTX 3080Ti ขึ้นไป
- ⚠ TTS + lip-sync แย่ง VRAM — ทางออก: pre-generate ทั้งหมด หรือแยก GPU

## 5. กฎแพลตฟอร์ม
| ข้อ | สถานะ | ผลต่อระบบ |
|---|---|---|
| Shopee Video: ป้าย AI-generated ตั้งแต่ 1 ส.ค. 2026 | ✅ (SG) | ใส่ป้าย AI ตลอด |
| ติดป้าย AI = ค่าคอมถูกปิด | ⚠ (บุคคลที่สาม) | **ยืนยันกับ Shopee ไทยก่อนลงทุน** |
| VN: วิดีโออัดไว้ = ละเมิด | ✅ VN / ⚠ TH | ต้อง "ไลฟ์จริง" |
| ใช้หน้า/เสียงคนจริง | หลักทั่วไป | เก็บหนังสือยินยอม |

⚠ **ไม่แนะนำ**: ฉีดภาพผ่าน virtual camera บน root → เสี่ยงถูกแบน

---

## 6. Milestones

**M0 — ตรวจความเป็นไปได้** (ก่อนเขียนโค้ด)
- [ ] บัญชีไทยเข้า Shopee Live PC ได้ Stream Key?
- [ ] ยืนยันนโยบาย AI host + ค่าคอมกับ Shopee ไทย
- [ ] ยืนยัน license: LiveTalking, MuseTalk weights, TTS

**M1 — Benchmark**
- [ ] LiveTalking + wav2lip + musetalk: FPS/VRAM
- [ ] TTS 2-3 ตัว: CER, RTF, ฟัง
- ✔ lip-sync ≥ 25fps ต่อเนื่อง 30 นาที, TTS RTF < 1

**M2 — Pipeline พื้นฐาน**
- [ ] Script Engine → Normalizer → TTS queue → LiveTalking → virtual camera → OBS
- ✔ ไลฟ์ทดสอบ 10 นาที, 3 สินค้า, ปากตรงเสียง

**M3 — Idle/Action + Operator Panel**
- [ ] สลับท่า idle ระหว่าง segment
- [ ] แผงควบคุม: current segment, pin cue, pause/skip/แทรกประโยค

**M4 — ความเสถียร**
- [ ] 2 ชม. ต่อเนื่อง: memory leak, A/V drift, RTMP reconnect
- [ ] ป้าย AI บนจอ

**M5 (ทางเลือก)** — ตอบคอมเมนต์อัตโนมัติ (หลังยืนยันนโยบายแล้ว)

---

## 7. ความเสี่ยง (เรียงตามผลกระทบ)
1. นโยบาย/ค่าคอม → M0
2. ช่องทางส่งสัญญาณ → บัญชีไทยอาจไม่มี Stream Key
3. คุณภาพเสียงไทย → วรรณยุกต์ผิด = ดูเป็น AI
4. License weights
5. GPU VRAM

---

## 8. แหล่งอ้างอิง
- LiveTalking: https://github.com/lipku/LiveTalking
- MuseTalk: https://github.com/TMElyralab/MuseTalk
- Ditto: https://github.com/antgroup/ditto-talkinghead
- JaiTTS: https://huggingface.co/JTS-AI/JaiTTS-F5TTS
- ThonburianTTS: https://github.com/biodatlab/thonburian-tts
- SE-Bridge-TTS: https://github.com/InsiderX-Pro/SE-Bridge-TTS
- Shopee Video AIGC: https://help.shopee.sg/portal/10/article/201777
