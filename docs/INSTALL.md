# INSTALL — Thai AI Live Host

ขั้นตอนติดตั้งทุกอย่าง เรียงจากฐานขึ้นไป ลิงก์ทางการทั้งหมด

## 0) เครื่องและ OS

- Ubuntu 22.04 หรือ Windows 11 + WSL2 (Ubuntu 22.04)
- NVIDIA GPU — ขั้นต่ำ RTX 3060 (wav2lip256), แนะนำ RTX 3080Ti ขึ้นไป (MuseTalk)
- RAM 16 GB ขึ้นไป, SSD 50 GB ว่าง

## 1) NVIDIA driver + CUDA

- NVIDIA driver (Linux): https://www.nvidia.com/en-us/drivers/
- CUDA Toolkit 12.x: https://developer.nvidia.com/cuda-downloads
- cuDNN (ต้องสมัคร dev account): https://developer.nvidia.com/cudnn

ตรวจผล:
```bash
nvidia-smi
nvcc --version
```

## 2) Python 3.10 + ffmpeg + v4l2loopback

```bash
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip ffmpeg git git-lfs
# Linux เท่านั้น (สำหรับ virtual camera):
sudo apt install -y v4l2loopback-dkms v4l2loopback-utils
sudo modprobe v4l2loopback devices=1 video_nr=10 card_label="LiveTalkingCam" exclusive_caps=1
```

- Python: https://www.python.org/downloads/
- FFmpeg: https://ffmpeg.org/download.html
- git-lfs: https://git-lfs.com (จำเป็นสำหรับโหลด weights จาก HF)
- v4l2loopback: https://github.com/v4l2loopback/v4l2loopback

## 3) OBS Studio

- Download: https://obsproject.com/download
- Plugin **obs-virtual-cam** มากับ OBS 26+ อยู่แล้ว
- สำหรับ Shopee Live PC: เพิ่ม Media Source หรือ Browser Source แล้วตั้ง output canvas 720×1280 หรือ 1080×1920 (แนวตั้ง)

## 4) LiveTalking (lip-sync server)

**Repo:** https://github.com/lipku/LiveTalking · License: Apache 2.0

```bash
# ไว้ภายนอก repo นี้
cd ~/apps
git clone https://github.com/lipku/LiveTalking
cd LiveTalking

# สร้าง env แยก (LiveTalking มี dep แยกชัดเจน)
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**เลือกโมเดลตามการ์ดจอ:**

### Wav2Lip (แนะนำสำหรับ RTX 3060)
- weights: https://github.com/Rudrabha/Wav2Lip  (ตาม LiveTalking README ชี้ไปที่ wav2lip256)
- License weights: non-commercial โดยค่าเริ่มต้น — **ต้องขอสิทธิ์เชิงพาณิชย์แยก**

### MuseTalk 1.5 (แนะนำสำหรับ RTX 3080Ti ขึ้นไป)
- Repo: https://github.com/TMElyralab/MuseTalk
- Weights (HF): https://huggingface.co/TMElyralab/MuseTalk
- Model card ระบุ CC-BY-NC 4.0 สำหรับ weights — **ห้ามใช้เชิงพาณิชย์โดยไม่มีข้อตกลง** (อ่านใน repo ตรวจอีกครั้ง)

### Ditto (ทางเลือกจากภาพนิ่ง)
- Repo: https://github.com/antgroup/ditto-talkinghead

**เริ่ม LiveTalking:**
```bash
# ตัวอย่างคำสั่งจาก LiveTalking README (อ่าน README ตัวจริงประกอบ):
python app.py --model musetalk --transport rtmp --push_url rtmp://127.0.0.1/live/stream
# หรือ virtual cam
python app.py --model wav2lip --transport virtualcam
```

> ⚠ อ่าน `README.md` ของ LiveTalking เสมอ — flag อาจเปลี่ยนตามเวอร์ชัน

## 5) Thai TTS (เลือก 1–3 ตัวเพื่อ benchmark)

### JaiTTS (แนะนำเริ่มต้น)
- HF: https://huggingface.co/JTS-AI/JaiTTS-F5TTS
- Paper: https://arxiv.org/abs/2604.27607 (ตรวจอีกครั้ง — เลข arXiv ตามที่ context ระบุ)
```bash
git lfs install
git clone https://huggingface.co/JTS-AI/JaiTTS-F5TTS ~/models/jaitts
```

### Thonburian TTS
- Repo: https://github.com/biodatlab/thonburian-tts

### SE-Bridge-TTS
- Repo: https://github.com/InsiderX-Pro/SE-Bridge-TTS

### Typhoon Whisper (สำหรับวัด CER)
- HF: https://huggingface.co/typhoon-ai/typhoon-whisper-large-v3

> ⚠ ตรวจ `LICENSE` ของแต่ละ repo + model card ก่อนใช้เชิงพาณิชย์

## 6) โปรเจกต์นี้

```bash
cd /path/to/XYZ   # repo นี้
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp config/config.example.yaml config/config.yaml
# แก้ไข config.yaml ให้ชี้ไป LiveTalking endpoint, TTS backend, ฯลฯ
```

ตั้งคีย์ Claude:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```
สมัคร / จัดการคีย์: https://console.anthropic.com

## 7) ลำดับการเปิดระบบ

```
1. nvidia-smi                                 ตรวจ GPU
2. source LiveTalking/.venv/bin/activate     เปิด LiveTalking server
   python app.py --model musetalk ...
3. source .venv/bin/activate (repo นี้)
   python -m live_host --config config/config.yaml
4. OBS: เพิ่ม Video Capture Device = LiveTalkingCam (Linux) หรือ OBS-VirtualCam (Win)
5. OBS: Start Streaming → Shopee Live PC (ถ้าบัญชีมี Stream Key)
```

## 8) Troubleshooting แบบย่อ

| อาการ | ตรวจ |
|---|---|
| `v4l2loopback` ไม่เจอ device | `sudo modprobe v4l2loopback`, `ls /dev/video*` |
| CUDA out of memory | ลดคุณภาพโมเดล, แยก TTS/lip-sync คนละ GPU, pre-generate TTS ล่วงหน้าทั้งหมด |
| ปากไม่ตรงเสียง (lag) | เพิ่ม buffer segment, ลด FPS, ปิด augment |
| เสียงไทยอ่านตัวเลขผิด | ใช้ `normalizer.py` ก่อนส่งเข้า TTS |
| OBS หา Virtual Cam ไม่เจอ (Windows) | ลง OBS 28+, Tools → Start Virtual Camera |
