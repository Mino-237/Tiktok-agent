"""
Erzeugt den Hintergrund: statt reiner abstrakter Partikel-Animation wird
jetzt ein zum Thema passendes KI-Bild (GPT Image 2) generiert und mit
einem sanften Zoom (Ken-Burns-Effekt) animiert, damit es sich bewegt
statt komplett statisch zu wirken.
"""

import os
import json
import subprocess
import base64
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

BREITE, HOEHE = 1080, 1920
FPS = 30


def bild_prompt_erstellen(thema: str) -> str:
    return (
        f"Abstract, dark, moody digital illustration inspired by the psychological "
        f"concept: '{thema}'. Deep blue and purple tones, soft glowing light, "
        f"dreamlike and symbolic, no text, no words, no letters, no people's faces, "
        f"cinematic atmosphere, vertical portrait composition."
    )


def bild_generieren(prompt: str, ziel_pfad: str):
    response = client.images.generate(
        model="gpt-image-2",
        prompt=prompt,
        size="1024x1536",
        quality="medium",
        n=1,
    )
    bild_base64 = response.data[0].b64_json
    with open(ziel_pfad, "wb") as f:
        f.write(base64.b64decode(bild_base64))


def ken_burns_video_erstellen(bild_pfad: str, dauer_sekunden: float, ziel_pfad: str):
    anzahl_frames = int((dauer_sekunden + 1) * FPS)
    zoompan_filter = (
        f"scale=2160:3840,"
        f"zoompan=z='min(zoom+0.0007,1.15)':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={anzahl_frames}:s={BREITE}x{HOEHE}:fps={FPS}"
    )
    befehl = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", bild_pfad,
        "-vf", zoompan_filter,
        "-t", str(dauer_sekunden + 1),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        ziel_pfad,
    ]
    subprocess.run(befehl, check=True)


def main():
    with open("output/video_meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    dauer = meta["duration"]

    with open("pending_script.json", encoding="utf-8") as f:
        skript_daten = json.load(f)
    thema = skript_daten.get("thema_original", skript_daten.get("titel", ""))

    prompt = bild_prompt_erstellen(thema)
    print(f"Generiere Hintergrundbild für Thema: {thema}")
    bild_generieren(prompt, "output/hintergrund_bild.png")

    print("Animiere Hintergrundbild (Ken-Burns-Zoom)...")
    ken_burns_video_erstellen("output/hintergrund_bild.png", dauer, "output/background.mp4")

    print(f"Hintergrund erstellt: {dauer:.1f}s")


if __name__ == "__main__":
    main()
