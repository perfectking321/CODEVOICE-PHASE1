"""
CodeVoice Main Program - Week 1 Demo
Simple voice-to-text demonstration using Microphone → VAD → Whisper pipeline.
"""

import asyncio
import numpy as np
from colorama import init, Fore, Style
from audio.microphone import MicrophoneStream
from audio.vad import VADDetector
from asr.whisper_asr import WhisperASR

# Initialize colorama for Windows
init()


class CodeVoiceDemo:
    """Simple voice-to-text demo."""
    
    def __init__(self):
        """Initialize all components."""
        print(f"{Fore.CYAN}🚀 Initializing CodeVoice...{Style.RESET_ALL}")
        
        self.mic = MicrophoneStream()
        self.vad = VADDetector(threshold=0.5)
        self.asr = WhisperASR(model_size="base")
        
        print(f"{Fore.GREEN}✓ All components loaded{Style.RESET_ALL}\n")
    
    async def run(self, duration: float = 30.0):
        """
        Run voice-to-text demo.
        
        Args:
            duration: How long to listen (seconds)
        """
        print(f"{Fore.YELLOW}🎤 Listening for speech (duration: {duration}s)...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Speak naturally. Press Ctrl+C to stop.{Style.RESET_ALL}\n")
        
        # Buffer to collect speech audio
        speech_buffer = []
        is_collecting = False
        silence_chunks = 0
        max_silence_chunks = 10  # 320ms of silence to trigger transcription
        
        try:
            async for audio_chunk in self.mic.stream_audio(duration=duration):
                # Check if speech is present
                is_speech = self.vad.is_speech(audio_chunk)
                
                if is_speech:
                    if not is_collecting:
                        # Start of speech
                        print(f"{Fore.GREEN}● Speech detected...{Style.RESET_ALL}", end='', flush=True)
                        is_collecting = True
                    
                    # Add to buffer
                    speech_buffer.append(audio_chunk)
                    silence_chunks = 0
                
                elif is_collecting:
                    # Silence during collection
                    speech_buffer.append(audio_chunk)
                    silence_chunks += 1
                    
                    # If enough silence, transcribe
                    if silence_chunks >= max_silence_chunks:
                        print(f"\r{Fore.YELLOW}⏳ Transcribing...{Style.RESET_ALL}" + " " * 20, end='', flush=True)
                        
                        # Concatenate audio
                        full_audio = np.concatenate([
                            np.frombuffer(chunk, dtype=np.int16) 
                            for chunk in speech_buffer
                        ]).astype(np.float32) / 32768.0
                        
                        # Transcribe
                        result = self.asr.transcribe(full_audio)
                        text = result['text'].strip()
                        
                        if text:
                            print(f"\r{Fore.CYAN}📝 You said:{Style.RESET_ALL} \"{Fore.WHITE}{text}{Style.RESET_ALL}\"")
                        else:
                            print(f"\r{Fore.RED}[No speech detected]{Style.RESET_ALL}")
                        
                        # Reset buffer
                        speech_buffer = []
                        is_collecting = False
                        silence_chunks = 0
        
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}⏹️  Stopped by user{Style.RESET_ALL}")
        
        finally:
            self.mic.close()
            print(f"\n{Fore.GREEN}✓ Demo complete{Style.RESET_ALL}")
    
    def list_devices(self):
        """Show available audio devices."""
        print(f"\n{Fore.CYAN}Available Audio Devices:{Style.RESET_ALL}")
        devices = self.mic.list_devices()
        
        for device in devices:
            print(f"  [{device['index']}] {device['name']}")
            print(f"      Channels: {device['channels']}, Rate: {device['sample_rate']}Hz")
        
        print()


async def main():
    """Main entry point."""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}  CodeVoice - Voice-to-Text Demo (Week 1){Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Create demo
    demo = CodeVoiceDemo()
    
    # List audio devices
    demo.list_devices()
    
    # Run for 60 seconds
    await demo.run(duration=60.0)
    
    print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}  Demo Complete! Week 1 Pipeline Working ✓{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    asyncio.run(main())
