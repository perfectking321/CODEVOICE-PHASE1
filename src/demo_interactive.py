"""
Interactive Week 1+2 Demo: Voice Input → Understanding
Speak commands and see real-time intent classification + entity extraction.
"""

import asyncio
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from audio.microphone import MicrophoneStream
from audio.vad import VADDetector
from asr.whisper_asr import WhisperASR
from intent.classifier import IntentClassifier
from intent.entities import EntityExtractor
from colorama import init, Fore, Style

# Initialize colorama
init()


class VoiceUnderstandingDemo:
    """Interactive demo combining speech recognition and understanding."""
    
    def __init__(self):
        self.mic = None
        self.vad = None
        self.asr = None
        self.classifier = None
        self.extractor = None
    
    async def initialize(self):
        """Load all components."""
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"  CodeVoice Week 1+2 Interactive Demo")
        print(f"  Voice Input → Transcription → Understanding")
        print(f"{'='*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}🚀 Initializing components...{Style.RESET_ALL}")
        
        # Week 1 components
        self.mic = MicrophoneStream()
        print(f"{Fore.GREEN}✓ Microphone ready{Style.RESET_ALL}")
        
        self.vad = VADDetector()
        print(f"{Fore.GREEN}✓ VAD loaded{Style.RESET_ALL}")
        
        self.asr = WhisperASR()
        print(f"{Fore.GREEN}✓ Whisper ASR loaded{Style.RESET_ALL}")
        
        # Week 2 components
        self.classifier = IntentClassifier()
        print(f"{Fore.GREEN}✓ Intent classifier loaded{Style.RESET_ALL}")
        
        self.extractor = EntityExtractor()
        print(f"{Fore.GREEN}✓ Entity extractor loaded{Style.RESET_ALL}\n")
    
    async def process_command(self, audio_data: bytes):
        """Process audio through full pipeline."""
        # Step 1: Transcribe (Week 1)
        transcription = self.asr.transcribe(audio_data)
        text = transcription["text"].strip()
        
        if not text or text.lower() in ["you", "thank you", "thanks"]:
            return None  # Ignore filler words
        
        print(f"\n{Fore.WHITE}📝 You said: {Fore.YELLOW}\"{text}\"{Style.RESET_ALL}")
        
        # Step 2: Classify intent (Week 2)
        intent_result = await self.classifier.classify(text)
        print(f"   {Fore.GREEN}→ Intent:{Style.RESET_ALL} {Fore.CYAN}{intent_result.intent}{Style.RESET_ALL} "
              f"(confidence: {intent_result.confidence:.2f}, {intent_result.latency_ms:.1f}ms)")
        
        # Show alternatives if available
        if intent_result.alternatives and len(intent_result.alternatives) > 1:
            print(f"      {Fore.BLUE}Alternatives:{Style.RESET_ALL}", end="")
            for alt_intent, alt_conf in intent_result.alternatives[1:3]:
                print(f" {alt_intent}({alt_conf:.2f})", end="")
            print()
        
        # Step 3: Extract entities (Week 2)
        entity_result = await self.extractor.extract(text, intent=intent_result.intent)
        if entity_result.entities:
            print(f"   {Fore.GREEN}→ Entities:{Style.RESET_ALL}")
            for key, value in entity_result.entities.items():
                print(f"      • {Fore.MAGENTA}{key}:{Style.RESET_ALL} {value}")
        else:
            print(f"   {Fore.GREEN}→ Entities:{Style.RESET_ALL} (none)")
        
        return {
            "text": text,
            "intent": intent_result.intent,
            "entities": entity_result.entities,
            "confidence": intent_result.confidence
        }
    
    async def run_interactive(self, duration: float = 60.0):
        """Run interactive voice understanding session."""
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🎤 Listening for commands...{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Speak naturally. Try commands like:{Style.RESET_ALL}")
        print(f"  • {Fore.CYAN}\"open main.py\"{Style.RESET_ALL}")
        print(f"  • {Fore.CYAN}\"commit changes with message fix bug\"{Style.RESET_ALL}")
        print(f"  • {Fore.CYAN}\"install numpy\"{Style.RESET_ALL}")
        print(f"  • {Fore.CYAN}\"search for python tutorial\"{Style.RESET_ALL}")
        print(f"  • {Fore.CYAN}\"run tests\"{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        speech_buffer = []
        is_speaking = False
        silence_count = 0
        command_count = 0
        
        # Lower VAD threshold for better sensitivity
        original_threshold = self.vad.threshold
        self.vad.threshold = 0.2  # Even lower = more sensitive (default is 0.5)
        
        print(f"{Fore.BLUE}[Debug] VAD threshold set to {self.vad.threshold} (lower = more sensitive){Style.RESET_ALL}\n")
        
        try:
            async for audio_chunk in self.mic.stream_audio(duration=duration):
                # Convert bytes to numpy for VAD
                audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Calculate volume for debugging
                volume = np.abs(audio_np).mean()
                
                # Check for voice activity (VAD or volume-based fallback)
                is_speech_vad = self.vad.is_speech(audio_np)
                is_speech_volume = volume > 0.01  # Simple volume threshold
                is_speech = is_speech_vad or is_speech_volume  # Use either method
                
                # Show activity indicator
                if volume > 0.005:
                    status = f"VAD: {is_speech_vad} | Vol: {is_speech_volume}"
                    print(f"\r{Fore.CYAN}🎵 Audio: {volume:.4f} | {status}{Style.RESET_ALL}", end="", flush=True)
                
                if is_speech:
                    silence_count = 0  # Reset silence counter
                    if not is_speaking:
                        print(f"{Fore.GREEN}🔊 Speech detected...{Style.RESET_ALL}", end="", flush=True)
                        is_speaking = True
                    speech_buffer.append(audio_chunk)  # Store as bytes
                else:
                    if is_speaking:
                        silence_count += 1
                        # Keep buffering for a bit to avoid cutting off speech
                        if silence_count < 10:  # ~320ms of silence tolerance
                            speech_buffer.append(audio_chunk)
                        elif len(speech_buffer) > 0:
                            # Enough silence detected, process the command
                            print(f"\r{Fore.GREEN}🔊 Speech detected... Processing{Style.RESET_ALL}")
                            
                            # Combine all audio byte chunks
                            audio_bytes = b''.join(speech_buffer)
                            
                            # Only process if we have enough audio (at least 0.3 seconds)
                            if len(audio_bytes) >= 9600:  # 0.3 seconds at 16kHz * 2 bytes per sample
                                # Process through understanding pipeline
                                result = await self.process_command(audio_bytes)
                            else:
                                print(f"{Fore.YELLOW}   (Too short, ignoring){Style.RESET_ALL}")
                                result = None
                            
                            if result:
                                command_count += 1
                                print(f"\n{Fore.WHITE}{'─'*70}{Style.RESET_ALL}\n")
                            
                            # Reset buffer
                            speech_buffer = []
                            is_speaking = False
                            silence_count = 0
        
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Stopping...{Style.RESET_ALL}\n")
        
        finally:
            # Restore original VAD threshold
            self.vad.threshold = original_threshold
        
        # Summary
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"  Session Complete")
        print(f"{'='*70}{Style.RESET_ALL}\n")
        print(f"{Fore.GREEN}📊 Commands understood: {command_count}{Style.RESET_ALL}\n")


async def main():
    """Main entry point."""
    demo = VoiceUnderstandingDemo()
    await demo.initialize()
    await demo.run_interactive(duration=120.0)  # 2 minutes


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Exiting...{Style.RESET_ALL}\n")
