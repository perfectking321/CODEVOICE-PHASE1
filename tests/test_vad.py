"""
Test Suite for VAD (Voice Activity Detection)
Tests: VAD model loading, speech detection, silence detection
"""

import pytest
import numpy as np
import torch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio.vad import VADDetector


class TestVAD:
    """Test Voice Activity Detection functionality."""
    
    def test_vad_init(self):
        """Test VAD detector initialization."""
        vad = VADDetector()
        assert vad is not None
        assert vad.SAMPLE_RATE == 16000
    
    def test_vad_model_loaded(self):
        """Test VAD model is properly loaded."""
        vad = VADDetector()
        assert vad.model is not None
        print(f"\n✓ VAD model type: {type(vad.model)}")
    
    def test_detect_speech_with_audio(self):
        """Test speech detection with real audio."""
        vad = VADDetector()
        
        # Generate synthetic "speech-like" audio (random noise with patterns)
        # Real speech has higher amplitude than silence
        speech_audio = np.random.randint(-5000, 5000, size=512, dtype=np.int16)
        speech_bytes = speech_audio.tobytes()
        
        is_speech = vad.is_speech(speech_bytes)
        assert isinstance(is_speech, bool)
        print(f"\n✓ Speech detected: {is_speech}")
    
    def test_detect_silence(self):
        """Test silence detection."""
        vad = VADDetector()
        
        # Generate silence (near-zero audio)
        silence_audio = np.zeros(512, dtype=np.int16)
        silence_bytes = silence_audio.tobytes()
        
        is_speech = vad.is_speech(silence_bytes)
        assert isinstance(is_speech, bool)
        assert is_speech == False, "Silence should not be detected as speech"
        print(f"\n✓ Silence correctly identified: not speech")
    
    def test_vad_latency(self):
        """Test VAD processing latency (should be < 30ms)."""
        import time
        
        vad = VADDetector()
        audio = np.random.randint(-5000, 5000, size=512, dtype=np.int16).tobytes()
        
        # Measure latency over 10 runs
        latencies = []
        for _ in range(10):
            start = time.perf_counter()
            vad.is_speech(audio)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms
        
        avg_latency = np.mean(latencies)
        assert avg_latency < 30, f"VAD latency {avg_latency:.2f}ms exceeds 30ms target"
        print(f"\n✓ Average VAD latency: {avg_latency:.2f}ms (target: <30ms)")
    
    def test_vad_with_different_audio_sizes(self):
        """Test VAD handles different audio chunk sizes."""
        vad = VADDetector()
        
        # Test with 256 samples (16ms)
        audio_256 = np.random.randint(-5000, 5000, size=256, dtype=np.int16).tobytes()
        result_256 = vad.is_speech(audio_256)
        assert isinstance(result_256, bool)
        
        # Test with 512 samples (32ms)
        audio_512 = np.random.randint(-5000, 5000, size=512, dtype=np.int16).tobytes()
        result_512 = vad.is_speech(audio_512)
        assert isinstance(result_512, bool)
        
        print(f"\n✓ VAD works with multiple chunk sizes")
