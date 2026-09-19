"""
Transkribiert die komplette Erzähl-Tonspur (output/voiceover_full.mp3)
mit Wort-Zeitstempeln, via faster-whisper (lokal, kostenlos).

NEU - INITIAL_PROMPT MIT FACHBEGRIFF: Whisper erkennt fremdsprachige
oder ungewöhnliche Fachbegriffe (z.B. "Mere-Exposure-Effekt") mitten in
deutscher Sprache manchmal falsch (z.B. "elusuritrufefekt" statt
korrekt). Über den initial_prompt-Parameter kann Whisper vorab "Hinweis-
Vokabular" mitgegeben werden - das verbessert die Trefferquote bei
genau solchen Begriffen deutlich, ohne die Erkennung sonst zu verändern.
"""

import re
import json
from faster_whisper import WhisperModel


def fachbegriff_ermitteln(skript_daten: dict) -> str:
    """Extrahiert den Fachbegriff aus thema_original, z.B. aus
    'Warum ... (Mere-Exposure-Effekt)' wird 'Mere-Exposure-Effekt'."""
    thema = skript_daten.get("thema_original", "")
    treffer = re.search(r'\(([^)]+)\)\s*$', thema)
    if treffer:
        return treffer.group(1).strip()
    return ""


def initial_prompt_erstellen(skript_daten: dict) -> str:
    """Baut einen kurzen Hinweistext mit dem Fachbegriff (und dem
    Titel), den Whisper als Kontext bekommt - hilft bei der korrekten
    Schreibweise ungewöhnlicher/fremdsprachiger Begriffe."""
    fachbegriff = fachbegriff_ermitteln(skript_daten)
    titel = skript_daten.get("titel", "")
    hinweis_teile = [t for t in [fachbegriff, titel] if t]
    if not hinweis_teile:
        return ""
    return "Alltagspsychologie-Video. Wichtige Begriffe: " + ", ".join(hinweis_teile) + "."


def woerter_transkribieren(audio_pfad: str, initial_prompt: str) -> list:
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        audio_pfad,
        word_timestamps=True,
        language="de",
        initial_prompt=initial_prompt or None,
    )

    woerter = []
    for segment in segments:
        for wort in segment.words:
            woerter.append({
                "text": wort.word.strip(),
                "start": wort.start,
                "end": wort.end,
            })
    return woerter


def main():
    with open("pending_script.json", encoding="utf-8") as f:
        skript_daten = json.load(f)

    initial_prompt = initial_prompt_erstellen(skript_daten)
    if initial_prompt:
        print(f"Whisper-Hinweis (initial_prompt): {initial_prompt}")

    woerter = woerter_transkribieren("output/voiceover_full.mp3", initial_prompt)
    with open("output/captions.json", "w", encoding="utf-8") as f:
        json.dump(woerter, f, ensure_ascii=False, indent=2)
    print(f"{len(woerter)} Wörter transkribiert.")


if __name__ == "__main__":
    main()
