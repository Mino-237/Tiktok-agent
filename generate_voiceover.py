"""
Erzeugt die KOMPLETTE Sprachausgabe (Hook + Kern + CTA - das ganze
Skript) über die Azure Text-to-Speech-API (REST-Endpunkt, keine
zusätzliche SDK-Abhängigkeit nötig - nutzt einfach "requests").

Nutzt dieselbe Stimme (de-DE-FlorianMultilingualNeural), die schon bei
D-ID gut ankam - nur jetzt direkt über Azure, ohne D-ID/Brandon als
Zwischenstation. Echte deutsche Neural-Stimme (anders als OpenAIs TTS,
die nur automatisch Sprache erkennt, aber primär für Englisch optimiert
ist).

Azure-Doku: https://learn.microsoft.com/azure/ai-services/speech-service/rest-text-to-speech
"""

import os
import json
import subprocess
import requests

AZURE_SPEECH_KEY = os.environ["AZURE_SPEECH_KEY"]
AZURE_SPEECH_REGION = os.environ["AZURE_SPEECH_REGION"]

STIMME = "de-DE-FlorianMultilingualNeural"
TTS_URL = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"


def vollstaendigen_text_erstellen(daten: dict) -> str:
    teile = [daten["hook"], daten["kern"], daten["cta"]]
    return " ".join(t.strip() for t in teile)


def escape_fuer_ssml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def voiceover_generieren(text: str, ziel_pfad: str):
    ssml = (
        f'<speak version="1.0" xml:lang="de-DE">'
        f'<voice xml:lang="de-DE" name="{STIMME}">'
        f'{escape_fuer_ssml(text)}'
        f'</voice></speak>'
    )
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3",
        "User-Agent": "tiktok-agent",
    }
    r = requests.post(TTS_URL, headers=headers, data=ssml.encode("utf-8"))
    if not r.ok:
        print(f"Azure TTS Antwort (Status {r.status_code}): {r.text}")
    r.raise_for_status()

    os.makedirs(os.path.dirname(ziel_pfad), exist_ok=True)
    with open(ziel_pfad, "wb") as f:
        f.write(r.content)


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

    text = vollstaendigen_text_erstellen(daten)
    print("Generiere Voiceover für das komplette Skript (Azure TTS, Florian)...")
    voiceover_generieren(text, "output/voiceover_full.mp3")

    dauer = audio_dauer_ermitteln("output/voiceover_full.mp3")

    with open("output/video_meta.json", "w", encoding="utf-8") as f:
        json.dump({"duration": dauer}, f)

    print(f"Voiceover fertig. Dauer: {dauer:.1f}s")


if __name__ == "__main__":
    main()
