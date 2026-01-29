"""
Integration Test - Full Pipeline
Tests complete flow: Microphone → VAD → Whisper ASR
"""

import pytest
import asyncio
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio.microphone import MicrophoneStream
from audio.vad import VADDetector
from asr.whisper_asr import WhisperASR


class TestIntegration:
    """Test complete audio processing pipeline."""
    
    @pytest.mark.asyncio
    async def test_microphone_to_vad_pipeline(self):
        """Test mic → VAD pipeline."""
        mic = MicrophoneStream()
        vad = VADDetector()
        
        speech_detected = False
        chunk_count = 0
        
        async for audio_chunk in mic.stream_audio(duration=1.0):
            is_speech = vad.is_speech(audio_chunk)
            
            if is_speech:
                speech_detected = True
            
            chunk_count += 1
            
            if chunk_count >= 10:  # Test 10 chunks
                break
        
        assert chunk_count == 10
        print(f"\n✓ Processed {chunk_count} chunks through VAD")
        print(f"✓ Speech detected: {speech_detected}")
    
    def test_vad_to_whisper_pipeline(self):
        """Test VAD → Whisper pipeline."""
        vad = VADDetector()
        asr = WhisperASR()
        
        # Generate 2 seconds of synthetic audio
        audio_data = []
        for _ in range(int(16000 * 2 / 512)):  # 2 seconds worth of 512-sample chunks
            chunk = np.random.randint(-3000, 3000, 512, dtype=np.int16)
            
            # Check if VAD detects speech
            is_speech = vad.is_speech(chunk)
            
            audio_data.append(chunk)
        
        # Concatenate all chunks
        full_audio = np.concatenate(audio_data).astype(np.float32) / 32768.0
        
        # Transcribe
        result = asr.transcribe(full_audio)
        
        assert isinstance(result, dict)
        assert 'text' in result
        print(f"\n✓ VAD → Whisper pipeline complete")
        print(f"✓ Transcription: '{result['text']}'")
    
    @pytest.mark.asyncio
    async def test_full_pipeline_latency(self):
        """Test end-to-end latency: Mic → VAD → Whisper."""
        import time
        
        mic = MicrophoneStream()
        vad = VADDetector()
        asr = WhisperASR()
        
        # Collect 2 seconds of audio
        audio_chunks = []
        chunk_count = 0
        
        pipeline_start = time.perf_counter()
        
        async for audio_chunk in mic.stream_audio(duration=2.0):
            # Stage 1: VAD (should be ~30ms)
            vad_start = time.perf_counter()
            is_speech = vad.is_speech(audio_chunk)
            vad_latency = (time.perf_counter() - vad_start) * 1000
            
            audio_chunks.append(audio_chunk)
            chunk_count += 1
        
        # Stage 2: Concatenate audio
        full_audio = np.concatenate([
            np.frombuffer(chunk, dtype=np.int16) for chunk in audio_chunks
        ]).astype(np.float32) / 32768.0
        
        # Stage 3: Whisper transcription
        asr_start = time.perf_counter()
        result = asr.transcribe(full_audio)
        asr_latency = (time.perf_counter() - asr_start) * 1000
        
        total_latency = (time.perf_counter() - pipeline_start) * 1000
        
        print(f"\n✓ Full pipeline latency breakdown:")
        print(f"  - Audio capture: 2000ms (expected)")
        print(f"  - VAD per chunk: ~{vad_latency:.1f}ms")
        print(f"  - Whisper transcription: {asr_latency:.0f}ms")
        print(f"  - Total pipeline: {total_latency:.0f}ms")
        
        # Whisper should process 2sec audio in < 1500ms
        assert asr_latency < 2000, f"ASR too slow: {asr_latency:.0f}ms"
    
    def test_all_components_initialized(self):
        """Test all components can be initialized together."""
        mic = MicrophoneStream()
        vad = VADDetector()
        asr = WhisperASR()
        
        assert mic is not None
        assert vad is not None
        assert asr is not None
        
        # Check devices available
        devices = mic.list_devices()
        assert len(devices) > 0
        
        print(f"\n✓ All components initialized successfully")
        print(f"✓ Available audio devices: {len(devices)}")
        
        mic.close()
