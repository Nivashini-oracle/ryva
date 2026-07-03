"""
RYVA - Voice alert generator (run this ONCE to create the audio files)
Usage:
    python generate_audio.py
This creates a folder called "audio" next to this script, with the
AMBER, RED, and REST alert files in English and Tamil.
"""
from gtts import gTTS
import os

os.makedirs("audio", exist_ok=True)

alerts = {
    "amber_en": ("You are showing signs of fatigue. Please stay alert.", "en"),
    "amber_ta": ("நீங்கள் சோர்வின் அறிகுறிகளை காட்டுகிறீர்கள். எச்சரிக்கையாக இருங்கள்.", "ta"),
    "red_en": ("Warning. High fatigue detected. Please stop and take a break immediately.", "en"),
    "red_ta": ("எச்சரிக்கை. அதிக சோர்வு கண்டறியப்பட்டது. உடனடியாக நிறுத்தி ஓய்வு எடுங்கள்.", "ta"),
    "rest_en": ("You have been fatigued for a while. Consider taking a short rest.", "en"),
}

for filename, (text, lang) in alerts.items():
    print(f"Generating {filename}.mp3 ...")
    tts = gTTS(text=text, lang=lang)
    tts.save(f"audio/{filename}.mp3")

print("\nDone. Files are in the 'audio' folder next to this script.")