"""
Test Suite for Audio Microphone Stream
Tests: Microphone initialization, audio capture, stream generation
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio.microphone import MicrophoneStream

class TestMicrophoneStream:
    """Test microphone streaming functionality."""
    
    def test_microphone_init(self):
        """Test microphone stream initialization."""
        mic = MicrophoneStream()
        assert mic is not None
        assert mic.SAMPLE_RATE == 16000
        assert mic.CHANNELS == 1
        assert mic.CHUNK_SIZE == 512
    
    def test_list_audio_devices(self):
        """Test listing available audio devices."""
        mic = MicrophoneStream()
        devices = mic.list_devices()
        assert isinstance(devices, list)
        assert len(devices) > 0
        print(f"\nFound {len(devices)} audio devices")
    
    @pytest.mark.asyncio
    async def test_audio_stream_format(self):
        """Test audio stream produces correct format."""
        mic = MicrophoneStream()
        
        chunk_count = 0
        async for audio_chunk in mic.stream_audio(duration=1.0):
            assert isinstance(audio_chunk, bytes)
            assert len(audio_chunk) > 0
            
            # Convert to numpy array
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16)
            assert audio_np.shape[0] == mic.CHUNK_SIZE
            
            chunk_count += 1
            if chunk_count >= 5:  # Test 5 chunks only
                break
        
        assert chunk_count == 5
        print(f"\n✓ Captured {chunk_count} audio chunks successfully")
    
    @pytest.mark.asyncio
    async def test_audio_stream_duration(self):
        """Test audio stream respects duration parameter."""
        mic = MicrophoneStream()
        
        chunk_count = 0
        async for audio_chunk in mic.stream_audio(duration=0.5):
            chunk_count += 1
        
        # 0.5 seconds at 16kHz with 512 chunk size = ~15 chunks
        expected_chunks = int((0.5 * mic.SAMPLE_RATE) / mic.CHUNK_SIZE)
        assert abs(chunk_count - expected_chunks) <= 2  # Allow 2 chunk tolerance
        print(f"\n✓ Duration test: captured {chunk_count} chunks (expected ~{expected_chunks})")
