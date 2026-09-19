"""
Erzeugt die KOMPLETTE Sprachausgabe (Hook + Kern + CTA - das ganze
Skript) über die Azure Text-to-Speech-API (REST-Endpunkt).

Nutzt die Stimme de-DE-FlorianMultilingualNeural.

NEU - PAUSE ZWISCHEN DEN CTA-SÄTZEN: Der CTA besteht aus zwei Sätzen
(humorvoller Übergangssatz + Like/Folgen-Einladung). Damit die beiden
nicht ohne Luft ineinander übergehen, wird zwischen ihnen jetzt eine
kurze SSML-Sprechpause (600ms) eingefügt.

Azure-Doku: https://learn.microsoft.com/azure/ai-services/speech-service/rest-text-to-speech
"""

import os
import re
import json
import subprocess
import requests

AZURE_SPEECH_KEY = os.environ["AZURE_SPEECH_KEY"]
AZURE_SPEECH_REGION = os.environ["AZURE_SPEECH_REGION"]

STIMME = "de-DE-FlorianMultilingualNeural"
TTS_URL = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

CTA_PAUSE_MS = 600  # Pause zwischen Übergangssatz und Like/Folgen-Einladung im CTA


def escape_fuer_ssml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def cta_mit_pause_aufbauen(cta_text: str) -> str:
    """Teilt den CTA am ersten Satzende auf (Übergangssatz | Rest) und
    fügt dazwischen eine SSML-Pause ein. Falls der CTA nur aus einem
    Satz besteht, wird er unverändert zurückgegeben."""
    teile = re.split(r'(?<=[.!?])\s+', cta_text.strip(), maxsplit=1)
    if len(teile) != 2:
        return escape_fuer_ssml(cta_text.strip())

    uebergang, rest = teile
    pause = f'<break time="{CTA_PAUSE_MS}ms"/>'
    return f"{escape_fuer_ssml(uebergang.strip())}{pause}{escape_fuer_ssml(rest.strip())}"


def vollstaendigen_ssml_text_erstellen(daten: dict) -> str:
    hook = escape_fuer_ssml(daten["hook"].strip())
    kern = escape_fuer_ssml(daten["kern"].strip())
    cta = cta_mit_pause_aufbauen(daten["cta"])
    return f"{hook} {kern} {cta}"


def voiceover_generieren(ssml_text_inhalt: str, ziel_pfad: str):
    ssml = (
        f'<speak version="1.0" xml:lang="de-DE">'
        f'<voice xml:lang="de-DE" name="{STIMME}">'
        f'{ssml_text_inhalt}'
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

    ssml_text_inhalt = vollstaendigen_ssml_text_erstellen(daten)
    print("Generiere Voiceover für das komplette Skript (Azure TTS, Florian, mit CTA-Pause)...")
    voiceover_generieren(ssml_text_inhalt, "output/voiceover_full.mp3")

    dauer = audio_dauer_ermitteln("output/voiceover_full.mp3")

    with open("output/video_meta.json", "w", encoding="utf-8") as f:
        json.dump({"duration": dauer}, f)

    print(f"Voiceover fertig. Dauer: {dauer:.1f}s")


if __name__ == "__main__":
    main()
