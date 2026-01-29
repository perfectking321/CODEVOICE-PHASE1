"""
Voice Activity Detection (VAD) Module
Uses Silero VAD to detect speech in audio streams with low latency.
"""

import torch
import numpy as np
from typing import Union


class VADDetector:
    """
    Silero Voice Activity Detection.
    
    Detects speech in audio chunks with ~30ms latency.
    Optimized for battery efficiency - only runs ASR when speech detected.
    """
    
    SAMPLE_RATE = 16000  # 16 kHz
    
    def __init__(self, threshold: float = 0.5):
        """
        Initialize VAD detector.
        
        Args:
            threshold: Speech detection threshold (0.0-1.0)
                      Higher = more conservative (less false positives)
                      Lower = more sensitive (catches more speech)
        """
        self.threshold = threshold
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Silero VAD model from torch hub."""
        try:
            # Load from torch hub (cached after first download)
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                trust_repo=True
            )
            
            # Extract model from tuple if needed
            if isinstance(model, tuple):
                model = model[0]
            
            self.model = model
            self.model.eval()  # Set to evaluation mode
            
            # Extract utility functions
            (self.get_speech_timestamps,
             self.save_audio,
             self.read_audio,
             self.VADIterator,
             self.collect_chunks) = utils
            
        except Exception as e:
            print(f"Warning: Could not load Silero VAD: {e}")
            print("VAD will use fallback energy-based detection")
            self.model = None
    
    def is_speech(self, audio_chunk: Union[bytes, np.ndarray]) -> bool:
        """
        Detect if audio chunk contains speech.
        
        Args:
            audio_chunk: Audio data as bytes or numpy array
                        Expected: 16-bit PCM, 16kHz, mono
        
        Returns:
            True if speech detected, False otherwise
        
        Example:
            >>> vad = VADDetector()
            >>> is_speaking = vad.is_speech(audio_bytes)
        """
        # Convert bytes to numpy array if needed
        if isinstance(audio_chunk, bytes):
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16)
        else:
            audio_np = audio_chunk
        
        # If model failed to load, use energy-based fallback
        if self.model is None:
            return self._energy_based_detection(audio_np)
        
        # Convert to float32 normalized to [-1, 1]
        audio_float = audio_np.astype(np.float32) / 32768.0
        
        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio_float)
        
        # Silero VAD expects specific chunk sizes, pad if needed
        required_size = 512  # 32ms at 16kHz
        if len(audio_tensor) < required_size:
            padding = required_size - len(audio_tensor)
            audio_tensor = torch.nn.functional.pad(audio_tensor, (0, padding))
        elif len(audio_tensor) > required_size:
            audio_tensor = audio_tensor[:required_size]
        
        try:
            # Run VAD model
            with torch.no_grad():
                speech_prob = self.model(audio_tensor, self.SAMPLE_RATE).item()
            
            # Return True if probability exceeds threshold
            return speech_prob > self.threshold
        
        except Exception as e:
            # Fallback to energy-based detection if model fails
            return self._energy_based_detection(audio_np)
    
    def _energy_based_detection(self, audio_np: np.ndarray) -> bool:
        """
        Fallback energy-based speech detection.
        
        Simply checks if audio energy exceeds silence threshold.
        Less accurate than Silero but works without model.
        """
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_np.astype(np.float32) ** 2))
        
        # Threshold for speech (tuned for typical microphone levels)
        energy_threshold = 500.0
        
        return rms > energy_threshold
    
    def get_speech_probability(self, audio_chunk: Union[bytes, np.ndarray]) -> float:
        """
        Get continuous speech probability score.
        
        Args:
            audio_chunk: Audio data
        
        Returns:
            Probability score (0.0 - 1.0)
        """
        # Convert bytes to numpy if needed
        if isinstance(audio_chunk, bytes):
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16)
        else:
            audio_np = audio_chunk
        
        if self.model is None:
            # Return binary 0 or 1 for fallback
            return 1.0 if self._energy_based_detection(audio_np) else 0.0
        
        # Convert to float32 normalized
        audio_float = audio_np.astype(np.float32) / 32768.0
        audio_tensor = torch.from_numpy(audio_float)
        
        # Pad/trim to 512 samples
        required_size = 512
        if len(audio_tensor) < required_size:
            padding = required_size - len(audio_tensor)
            audio_tensor = torch.nn.functional.pad(audio_tensor, (0, padding))
        elif len(audio_tensor) > required_size:
            audio_tensor = audio_tensor[:required_size]
        
        try:
            with torch.no_grad():
                speech_prob = self.model(audio_tensor, self.SAMPLE_RATE).item()
            return speech_prob
        except:
            return 0.5  # Uncertain


# Example usage
if __name__ == "__main__":
    import time
    
    vad = VADDetector()
    
    # Test with silence
    silence = np.zeros(512, dtype=np.int16)
    print(f"Silence detection: {vad.is_speech(silence)}")
    
    # Test with noise (simulated speech)
    noise = np.random.randint(-5000, 5000, size=512, dtype=np.int16)
    print(f"Noise detection: {vad.is_speech(noise)}")
    
    # Measure latency
    latencies = []
    for _ in range(100):
        audio = np.random.randint(-3000, 3000, size=512, dtype=np.int16)
        start = time.perf_counter()
        vad.is_speech(audio)
        latencies.append((time.perf_counter() - start) * 1000)
    
    print(f"\nAverage latency: {np.mean(latencies):.2f}ms")
    print(f"Max latency: {np.max(latencies):.2f}ms")
