"""
Microphone Audio Streaming Module
Captures real-time audio from microphone for voice processing.
"""

import pyaudio
import asyncio
from typing import AsyncIterator, List, Dict
import numpy as np


class MicrophoneStream:
    """Real-time microphone audio streaming."""
    
    # Audio configuration optimized for Whisper
    SAMPLE_RATE = 16000        # 16 kHz (Whisper optimized)
    CHANNELS = 1               # Mono (VAD compatible)
    CHUNK_SIZE = 512           # 32 ms chunks (512 samples / 16000 Hz)
    FORMAT = pyaudio.paInt16   # 16-bit PCM
    
    def __init__(self, device_id: int = None):
        """
        Initialize microphone stream.
        
        Args:
            device_id: Microphone device ID (None = default device)
        """
        self.device_id = device_id
        self.audio = pyaudio.PyAudio()
        self.stream = None
    
    def list_devices(self) -> List[Dict]:
        """
        List all available audio input devices.
        
        Returns:
            List of device info dictionaries
        """
        devices = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:  # Input device
                devices.append({
                    'index': i,
                    'name': device_info['name'],
                    'channels': device_info['maxInputChannels'],
                    'sample_rate': int(device_info['defaultSampleRate'])
                })
        return devices
    
    async def stream_audio(self, duration: float = None) -> AsyncIterator[bytes]:
        """
        Stream audio chunks from microphone.
        
        Args:
            duration: Duration in seconds (None = infinite stream)
            
        Yields:
            Audio chunks as bytes (512 samples each)
        
        Example:
            async for chunk in mic.stream_audio(duration=5.0):
                # Process audio chunk
                pass
        """
        # Open audio stream
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            input_device_index=self.device_id,
            frames_per_buffer=self.CHUNK_SIZE,
            stream_callback=None  # Blocking mode for simplicity
        )
        
        chunks_to_read = None
        if duration is not None:
            # Calculate number of chunks for given duration
            chunks_to_read = int((duration * self.SAMPLE_RATE) / self.CHUNK_SIZE)
        
        try:
            chunk_count = 0
            while True:
                # Read audio chunk (blocking)
                audio_data = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.stream.read,
                    self.CHUNK_SIZE
                )
                
                yield audio_data
                
                chunk_count += 1
                
                # Stop if duration reached
                if chunks_to_read and chunk_count >= chunks_to_read:
                    break
        
        finally:
            # Clean up
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
    
    def close(self):
        """Close audio resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.audio:
            self.audio.terminate()
            self.audio = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()


# Example usage
if __name__ == "__main__":
    async def main():
        mic = MicrophoneStream()
        
        # List available devices
        print("Available audio devices:")
        for device in mic.list_devices():
            print(f"  [{device['index']}] {device['name']} ({device['channels']} channels)")
        
        # Record 2 seconds of audio
        print("\n🎤 Recording 2 seconds...")
        chunks = []
        async for audio_chunk in mic.stream_audio(duration=2.0):
            chunks.append(audio_chunk)
        
        print(f"✓ Recorded {len(chunks)} chunks ({len(chunks) * 512} samples)")
        
        mic.close()
    
    asyncio.run(main())
