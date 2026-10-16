# Thai AI Live Host

ระบบ **Digital Human ไลฟ์ขายของภาษาไทย**: ป้อนข้อมูลสินค้า → LLM แต่งสคริปต์ → TTS ไทย → lip-sync กับวิดีโอคนจริง → ส่งออก OBS/RTMP

อ่าน [`CONTEXT.md`](./CONTEXT.md) ก่อน — มีสถาปัตยกรรม / milestones / ความเสี่ยง / ข้อกฎแพลตฟอร์มครบ

## สถานะโครงการ

สเกเลตันโค้ดระดับ **M0 → M2 เริ่มต้น** พร้อม:

| ส่วน | สถานะ |
|---|---|
| Thai text normalizer | ✅ ใช้งานได้ + unit tests |
| Script Engine (Anthropic SDK) | ✅ โครง + prompt caching |
| TTS worker | 🚧 โครง + ตัวอย่าง backend 3 ตัว |
| Lip-sync client (LiveTalking HTTP) | 🚧 โครง |
| Orchestrator | 🚧 โครง async queue |
| Operator Panel (FastAPI/WS) | 🚧 โครง |

## เริ่มต้น

1. อ่าน [`docs/INSTALL.md`](./docs/INSTALL.md) ติดตั้งเครื่องมือภายนอก (CUDA / LiveTalking / TTS / OBS)
2. เช็ค [`docs/M0_CHECKLIST.md`](./docs/M0_CHECKLIST.md) — **ทำ M0 ให้ครบก่อนลงทุนเวลาเขียนโค้ด**
3. อ่าน [`docs/POLICY.md`](./docs/POLICY.md) — ข้อกฎแพลตฟอร์มที่ต้องรองรับตั้งแต่ออกแบบ

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
cp config/config.example.yaml config/config.yaml

# ทดสอบ normalizer
pytest tests/

# รัน script engine (ต้อง ANTHROPIC_API_KEY)
python -m live_host.script_engine --product-file samples/product.json

# รัน orchestrator ครบวงจร (ต้องเปิด LiveTalking server ไว้ก่อน)
python -m live_host --config config/config.yaml
```

## โครงสร้าง

```
src/live_host/
  normalizer.py      Thai text / number / currency normalizer
  script_engine.py   Claude API → segments JSON
  tts_worker.py      TTS queue (JaiTTS / Thonburian / SE-Bridge backend)
  lipsync_client.py  LiveTalking HTTP client
  orchestrator.py    async pipeline
  operator_panel.py  FastAPI + WebSocket + static HTML

config/
  config.example.yaml   endpoints, model ids, keys
  pronunciations.yaml   brand/word → Thai reading

docs/
  INSTALL.md         ขั้นตอนติดตั้งเครื่องมือภายนอก พร้อมลิงก์
  M0_CHECKLIST.md    ตรวจความเป็นไปได้ก่อนลงทุน
  POLICY.md          กฎแพลตฟอร์ม + checklist ปฏิบัติ

android-app/         Android (Kotlin + Canvas) 2D graphics demo
                     — build APK ผ่าน GitHub Actions:
                       .github/workflows/android-apk.yml
```

## Android demo (secondary)

โปรเจกต์ `android-app/` เป็นเดโม 2D graphics (Particles / Bouncing Balls /
Fractal Tree / Waves) แยกจากระบบ Live Host หลัก Build APK ได้ 2 วิธี:

- **บนเครื่องตัวเอง** (ต้องมี Android SDK + JDK 17):
  ```sh
  cd android-app && ./gradlew :app:assembleDebug
  ```
- **บน GitHub Actions**: push ก็ build ให้เอง, APK แนบเป็น artifact
  — ดู Actions tab บน GitHub, workflow ชื่อ "Build Android APK"

## License

โค้ดในที่นี้: MIT
Weights / โมเดลภายนอก (MuseTalk, JaiTTS, ฯลฯ): **ต้องตรวจ license แยก** ก่อนใช้เชิงพาณิชย์ — ดู `docs/INSTALL.md`
