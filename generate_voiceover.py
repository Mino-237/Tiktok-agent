"""
Erzeugt die KOMPLETTE Sprachausgabe (Hook + Cliffhanger + Kern + CTA)
über die Azure Text-to-Speech-API.

TEST-CACHE: Solange pending_script.json "testmodus": true enthält, wird
das erzeugte Voiceover in test_cache/ zwischengespeichert. Bei
zukünftigen Testläufen wird es von dort wiederverwendet, statt erneut
bei Azure angefragt zu werden - Ton bleibt zwischen Testläufen exakt
gleich, damit sich Video-Effekt-Änderungen fair vergleichen lassen.
"""

import os
import re
import json
import shutil
import subprocess
import requests

AZURE_SPEECH_KEY = os.environ["AZURE_SPEECH_KEY"]
AZURE_SPEECH_REGION = os.environ["AZURE_SPEECH_REGION"]

STIMME = "de-DE-FlorianMultilingualNeural"
TTS_URL = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

CLIFFHANGER_PAUSE_MS = 450
CTA_PAUSE_MS = 600

TEST_CACHE_ORDNER = "test_cache"
CACHE_AUDIO_PFAD = os.path.join(TEST_CACHE_ORDNER, "voiceover_full.mp3")
CACHE_META_PFAD = os.path.join(TEST_CACHE_ORDNER, "voiceover_meta.json")


def escape_fuer_ssml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def cta_mit_pause_aufbauen(cta_text: str) -> str:
    teile = re.split(r'(?<=[.!?])\s+', cta_text.strip(), maxsplit=1)
    if len(teile) != 2:
        return escape_fuer_ssml(cta_text.strip())

    uebergang, rest = teile
    pause = f'<break time="{CTA_PAUSE_MS}ms"/>'
    return f"{escape_fuer_ssml(uebergang.strip())}{pause}{escape_fuer_ssml(rest.strip())}"


def vollstaendigen_ssml_text_erstellen(daten: dict) -> str:
    hook = escape_fuer_ssml(daten["hook"].strip())
    cliffhanger = daten.get("cliffhanger", "").strip()
    kern = escape_fuer_ssml(daten["kern"].strip())
    cta = cta_mit_pause_aufbauen(daten["cta"])

    teile = [hook]
    if cliffhanger:
        cliffhanger_pause = f'<break time="{CLIFFHANGER_PAUSE_MS}ms"/>'
        teile.append(f"{escape_fuer_ssml(cliffhanger)}{cliffhanger_pause}")
    teile.append(kern)
    teile.append(cta)

    return " ".join(teile)


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

    testmodus = daten.get("testmodus", False)
    os.makedirs("output", exist_ok=True)

    if testmodus and os.path.exists(CACHE_AUDIO_PFAD) and os.path.exists(CACHE_META_PFAD):
        print("⚠️  TEST-MODUS: nutze gecachtes Voiceover (keine neue Azure-Anfrage).")
        shutil.copy(CACHE_AUDIO_PFAD, "output/voiceover_full.mp3")
        with open(CACHE_META_PFAD, encoding="utf-8") as f:
            cache_daten = json.load(f)
        dauer = cache_daten["duration"]
    else:
        ssml_text_inhalt = vollstaendigen_ssml_text_erstellen(daten)
        print("Generiere Voiceover für das komplette Skript (Azure TTS, Florian)...")
        voiceover_generieren(ssml_text_inhalt, "output/voiceover_full.mp3")
        dauer = audio_dauer_ermitteln("output/voiceover_full.mp3")

        if testmodus:
            os.makedirs(TEST_CACHE_ORDNER, exist_ok=True)
            shutil.copy("output/voiceover_full.mp3", CACHE_AUDIO_PFAD)
            with open(CACHE_META_PFAD, "w", encoding="utf-8") as f:
                json.dump({"duration": dauer}, f)
            print("Test-Voiceover im Cache gespeichert für zukünftige Testläufe.")

    with open("output/video_meta.json", "w", encoding="utf-8") as f:
        json.dump({"duration": dauer}, f)

    print(f"Voiceover fertig. Dauer: {dauer:.1f}s")


if __name__ == "__main__":
    main()
