"""
Erzeugt die KOMPLETTE Sprachausgabe (Hook + Kern + CTA - das ganze
Skript) über OpenAIs Text-to-Speech-API. D-ID/Brandon wird nicht mehr
genutzt - dadurch entfällt die D-ID-Kosten-/Minuten-Begrenzung komplett,
was für mehrmals tägliches Posten in der Wachstumsphase wichtig ist.

Deutlich günstiger als D-ID (~$0,015/Minute statt ~$0,47/Minute bei
D-ID Lite) und ohne jedes Mengenlimit außer dem eigenen API-Guthaben.
"""

import json
import subprocess
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

STIMME = "onyx"  # ruhige, männliche Stimme


def vollstaendigen_text_erstellen(daten: dict) -> str:
    teile = [daten["hook"], daten["kern"], daten["cta"]]
    return " ".join(t.strip() for t in teile)


def voiceover_generieren(text: str, ziel_pfad: str):
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=STIMME,
        input=text,
    )
    response.stream_to_file(ziel_pfad)


def audio_dauer_ermitteln(pfad: str) -> float:
    """Ermittelt die Dauer einer Audiodatei in Sekunden via ffprobe."""
    befehl = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        pfad,
    ]
    ergebnis = subprocess.run(befehl, capture_output=True, text=True, check=True)
    return float(ergebnis.stdout.strip())


def main():
    with open("pending_script.json", encoding="utf-8") as f:
        daten = json.load(f)

    os.makedirs("output", exist_ok=True)

    text = vollstaendigen_text_erstellen(daten)
    print("Generiere Voiceover für das komplette Skript (OpenAI TTS)...")
    voiceover_generieren(text, "output/voiceover_full.mp3")

    dauer = audio_dauer_ermitteln("output/voiceover_full.mp3")

    with open("output/video_meta.json", "w", encoding="utf-8") as f:
        json.dump({"duration": dauer}, f)

    print(f"Voiceover fertig. Dauer: {dauer:.1f}s")


if __name__ == "__main__":
    main()
