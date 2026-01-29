"""
Microphone Test & Diagnostic Tool
Tests if audio capture is working and shows audio levels.
"""

import numpy as np
import pyaudio
import time
from colorama import init, Fore, Style

init()

def test_microphone():
    """Test microphone and show audio levels."""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  Microphone Diagnostic Test")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    # Initialize PyAudio
    audio = pyaudio.PyAudio()
    
    # List available devices
    print(f"{Fore.YELLOW}Available audio input devices:{Style.RESET_ALL}\n")
    default_device = None
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            is_default = " (DEFAULT)" if i == audio.get_default_input_device_info()['index'] else ""
            print(f"  [{i}] {info['name']}{Fore.GREEN}{is_default}{Style.RESET_ALL}")
            if is_default:
                default_device = i
    
    print(f"\n{Fore.CYAN}Using default device: {default_device}{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Speak now! Audio levels will be shown...{Style.RESET_ALL}")
    print(f"{Fore.WHITE}(Press Ctrl+C to stop){Style.RESET_ALL}\n")
    
    # Open stream
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        input_device_index=default_device,
        frames_per_buffer=512
    )
    
    try:
        while True:
            # Read audio
            data = stream.read(512, exception_on_overflow=False)
            audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Calculate volume level
            volume = np.abs(audio_np).mean()
            db = 20 * np.log10(volume + 1e-10)
            
            # Show level bar
            bar_length = int(min(50, max(0, (db + 60) / 60 * 50)))
            bar = "█" * bar_length
            
            # Color based on volume
            if volume > 0.05:
                color = Fore.GREEN
                status = "LOUD"
            elif volume > 0.01:
                color = Fore.YELLOW
                status = "SPEAKING"
            else:
                color = Fore.RED
                status = "QUIET"
            
            print(f"\r{color}[{bar:<50}] {volume:.4f} ({db:.1f} dB) {status}{Style.RESET_ALL}", end="", flush=True)
            
            time.sleep(0.032)  # ~30 fps
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.GREEN}Test complete!{Style.RESET_ALL}\n")
    
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
    
    print(f"{Fore.CYAN}If you saw the bar moving when you spoke, your microphone works!{Style.RESET_ALL}\n")


if __name__ == "__main__":
    test_microphone()
