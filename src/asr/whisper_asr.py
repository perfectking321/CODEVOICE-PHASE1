"""
Whisper Automatic Speech Recognition Module
Converts audio to text with low latency.
"""

import whisper
import numpy as np
from typing import Union, Dict
import torch


class WhisperASR:
    """
    OpenAI Whisper speech recognition.
    
    Converts audio to text with ~150-250ms latency per 2-second chunk.
    """
    
    def __init__(self, model_size: str = "base", device: str = None):
        """
        Initialize Whisper ASR.
        
        Args:
            model_size: Model size (tiny, base, small, medium, large)
                       - tiny: 39M params, fastest
                       - base: 74M params, good balance (default)
                       - small: 244M params, better accuracy
            device: Device to run on ("cuda", "cpu", or None for auto)
        """
        self.model_size = model_size
        
        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model."""
        print(f"Loading Whisper {self.model_size} model on {self.device}...")
        self.model = whisper.load_model(self.model_size, device=self.device)
        print(f"✓ Whisper {self.model_size} loaded")
    
    def transcribe(
        self, 
        audio: Union[np.ndarray, bytes],
        language: str = "en",
        task: str = "transcribe"
    ) -> Dict:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio data as numpy array (float32) or bytes (int16 PCM)
            language: Language code (default: "en" for English)
            task: "transcribe" or "translate" (translate to English)
        
        Returns:
            Dictionary with keys:
                - text: Transcribed text
                - segments: List of segments with timing
                - language: Detected language
        
        Example:
            >>> asr = WhisperASR()
            >>> result = asr.transcribe(audio_data)
            >>> print(result['text'])
        """
        # Convert bytes to numpy if needed
        if isinstance(audio, bytes):
            audio = self._bytes_to_numpy(audio)
        
        # Ensure float32 in range [-1, 1]
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32) / 32768.0
        
        # Whisper expects audio to be at 16kHz
        # If audio is too short, pad it
        min_length = 16000  # 1 second minimum
        if len(audio) < min_length:
            audio = np.pad(audio, (0, min_length - len(audio)), mode='constant')
        
        try:
            # Run transcription
            result = self.model.transcribe(
                audio,
                language=language,
                task=task,
                fp16=False,  # Disable FP16 for CPU compatibility
                verbose=False
            )
            
            return {
                'text': result['text'].strip(),
                'segments': result.get('segments', []),
                'language': result.get('language', language)
            }
        
        except Exception as e:
            print(f"Error during transcription: {e}")
            return {
                'text': '',
                'segments': [],
                'language': language,
                'error': str(e)
            }
    
    def _bytes_to_numpy(self, audio_bytes: bytes) -> np.ndarray:
        """Convert bytes (int16 PCM) to numpy float32."""
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        return audio_float32
    
    def transcribe_file(self, audio_path: str, **kwargs) -> Dict:
        """
        Transcribe audio from file.
        
        Args:
            audio_path: Path to audio file
            **kwargs: Additional arguments for transcribe()
        
        Returns:
            Transcription result dictionary
        """
        result = self.model.transcribe(audio_path, **kwargs)
        return {
            'text': result['text'].strip(),
            'segments': result.get('segments', []),
            'language': result.get('language', 'en')
        }


# Example usage
if __name__ == "__main__":
    import time
    
    print("Initializing Whisper ASR...")
    asr = WhisperASR(model_size="base")
    
    # Test 1: Silence
    print("\nTest 1: Transcribing silence...")
    silence = np.zeros(16000 * 2, dtype=np.float32)
    result = asr.transcribe(silence)
    print(f"Result: '{result['text']}'")
    
    # Test 2: Noise
    print("\nTest 2: Transcribing random noise...")
    noise = np.random.randn(16000 * 2).astype(np.float32) * 0.05
    result = asr.transcribe(noise)
    print(f"Result: '{result['text']}'")
    
    # Test 3: Latency benchmark
    print("\nTest 3: Latency benchmark...")
    audio = np.random.randn(16000 * 2).astype(np.float32) * 0.05
    
    latencies = []
    for i in range(3):
        start = time.perf_counter()
        asr.transcribe(audio)
        latency = (time.perf_counter() - start) * 1000
        latencies.append(latency)
        print(f"  Run {i+1}: {latency:.0f}ms")
    
    print(f"Average latency: {np.mean(latencies):.0f}ms")
