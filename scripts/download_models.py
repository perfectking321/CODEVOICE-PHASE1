"""Download and verify pre-trained models."""

import sys
import os

def download_models():
    """Download all required pre-trained models."""
    
    print("🚀 CodeVoice Model Download Script")
    print("=" * 50)
    
    # 1. Download Whisper Base Model
    print("\n1️⃣ Downloading Whisper base model (140 MB)...")
    try:
        import whisper
        model = whisper.load_model("base")
        print("✅ Whisper base model downloaded successfully")
        print(f"   Model loaded: {type(model).__name__}")
    except Exception as e:
        print(f"❌ Failed to download Whisper: {e}")
        return False
    
    # 2. Download Silero VAD Model (skip if rate limited)
    print("\n2️⃣ Downloading Silero VAD model (1 MB)...")
    try:
        import torch
        # Try to load from local cache first
        model = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            trust_repo=True,
            skip_validation=True
        )
        print("✅ Silero VAD model downloaded successfully")
        print(f"   Model type: {type(model).__name__}")
    except Exception as e:
        print(f"⚠️  Silero VAD download skipped (will download on first use): {e}")
        print("   This is OK - it will auto-download when needed")
    
    # 3. Download DistilBERT Model
    print("\n3️⃣ Downloading DistilBERT model (268 MB)...")
    try:
        from transformers import pipeline
        classifier = pipeline(
            "text-classification",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        result = classifier("test")
        print("✅ DistilBERT model downloaded successfully")
        print(f"   Test classification: {result}")
    except Exception as e:
        print(f"❌ Failed to download DistilBERT: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Core models downloaded successfully!")
    print(f"📊 Total size: ~400 MB")
    print(f"💾 Cache location: {os.path.expanduser('~/.cache')}")
    print("\n🎉 You're ready to start Week 1!")
    
    return True

if __name__ == "__main__":
    success = download_models()
    sys.exit(0 if success else 1)
