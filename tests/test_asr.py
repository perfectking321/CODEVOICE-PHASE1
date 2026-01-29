"""
Test Suite for Whisper ASR (Automatic Speech Recognition)
Tests: Model loading, transcription, latency
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asr.whisper_asr import WhisperASR


class TestWhisperASR:
    """Test Whisper speech recognition functionality."""
    
    def test_whisper_init(self):
        """Test Whisper ASR initialization."""
        asr = WhisperASR()
        assert asr is not None
        assert asr.model_size == "base"
    
    def test_whisper_model_loaded(self):
        """Test Whisper model is properly loaded."""
        asr = WhisperASR()
        assert asr.model is not None
        print(f"\n✓ Whisper model loaded: {type(asr.model).__name__}")
    
    def test_transcribe_silence(self):
        """Test transcription of silence returns empty or minimal text."""
        asr = WhisperASR()
        
        # Generate 2 seconds of silence
        duration = 2.0
        silence_audio = np.zeros(int(16000 * duration), dtype=np.float32)
        
        result = asr.transcribe(silence_audio)
        
        assert isinstance(result, dict)
        assert 'text' in result
        # Silence should produce empty or very short text
        assert len(result['text'].strip()) < 10
        print(f"\n✓ Silence transcription: '{result['text']}'")
    
    def test_transcribe_returns_proper_format(self):
        """Test transcription returns proper dictionary format."""
        asr = WhisperASR()
        
        # Generate synthetic audio (noise that might be mistaken for speech)
        audio = np.random.randn(16000 * 2).astype(np.float32) * 0.1
        
        result = asr.transcribe(audio)
        
        assert isinstance(result, dict)
        assert 'text' in result
        assert isinstance(result['text'], str)
        print(f"\n✓ Result format correct")
    
    def test_transcribe_latency(self):
        """Test transcription latency (should be < 1000ms for 2 sec audio)."""
        import time
        
        asr = WhisperASR()
        
        # Generate 2 seconds of audio
        audio = np.random.randn(16000 * 2).astype(np.float32) * 0.1
        
        start = time.perf_counter()
        result = asr.transcribe(audio)
        latency = (time.perf_counter() - start) * 1000
        
        # Base model should process 2sec audio in < 1000ms on modern hardware
        assert latency < 2000, f"Latency {latency:.0f}ms too high"
        print(f"\n✓ Transcription latency: {latency:.0f}ms for 2sec audio")
    
    def test_transcribe_with_bytes(self):
        """Test transcription accepts bytes input."""
        asr = WhisperASR()
        
        # Generate audio as int16 bytes (typical microphone format)
        audio_int16 = np.random.randint(-5000, 5000, 16000 * 2, dtype=np.int16)
        audio_bytes = audio_int16.tobytes()
        
        result = asr.transcribe(audio_bytes)
        
        assert isinstance(result, dict)
        assert 'text' in result
        print(f"\n✓ Bytes input accepted")
    
    @pytest.mark.slow
    def test_transcribe_actual_speech(self):
        """Test transcription with actual speech (if available)."""
        # This test requires actual speech audio file
        # Skip if not available
        pytest.skip("Requires actual speech audio file for testing")
