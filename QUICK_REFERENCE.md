# CodeVoice Quick Reference

## 🚀 Start Working

```powershell
cd "c:\AIot Project\phase 1\codevoice"
.\venv\Scripts\Activate.ps1
python src\main.py
```

## 🧪 Run Tests

```powershell
# All tests
pytest

# Specific component
pytest tests/test_audio.py -v
pytest tests/test_vad.py -v
pytest tests/test_asr.py -v

# Integration
pytest tests/test_integration.py -v

# With coverage
pytest --cov=src tests/
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Demo application |
| `src/audio/microphone.py` | Audio capture |
| `src/audio/vad.py` | Speech detection |
| `src/asr/whisper_asr.py` | Transcription |

## 🔧 Common Commands

```powershell
# List audio devices
python -c "from src.audio.microphone import MicrophoneStream; m = MicrophoneStream(); [print(d) for d in m.list_devices()]"

# Test VAD latency
python src\audio\vad.py

# Test Whisper latency
python src\asr\whisper_asr.py

# Re-download models
python scripts\download_models.py
```

## ⚙️ Configuration

Edit `.env`:
```ini
MICROPHONE_DEVICE_ID=0        # Change device
ASR_MODEL_SIZE=base          # tiny/base/small
ASR_LANGUAGE=en              # Language code
```

## 📊 Performance Targets

| Metric | Target | Achieved |
|--------|--------|----------|
| VAD | <30ms | ~15ms ✅ |
| Whisper | <500ms | ~400ms ✅ |

## 🐛 Troubleshooting

```powershell
# No audio?
python -c "import pyaudio; pa = pyaudio.PyAudio(); print(pa.get_device_count())"

# Models missing?
python scripts\download_models.py

# Tests failing?
pytest --tb=short -v
```

## 📅 Week 1 Status

✅ Microphone streaming  
✅ VAD (speech detection)  
✅ Whisper ASR  
✅ Integration tests  
✅ Demo working  

**Next:** Week 2 - Intent Classification

---

**Quick Start:**
```powershell
.\venv\Scripts\Activate.ps1
python src\main.py
```
**Then speak!** 🎤
