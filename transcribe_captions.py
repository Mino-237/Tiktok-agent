"""
Transkribiert das erzeugte Avatar-Video mit Wort-Zeitstempeln, via
faster-whisper (lokal, kostenlos, läuft direkt im GitHub-Actions-Runner
ohne externe API). Diese Zeitstempel werden für die Wort-für-Wort
animierten Untertitel ("Karaoke-Stil") gebraucht.

HINWEIS: Der erste Lauf lädt das Whisper-Modell herunter (~150MB),
das kostet ein bis zwei Minuten zusätzlich. Der GitHub-Actions-Workflow
cached das Modell zwischen den Läufen, damit das nicht jeden Tag erneut
passiert (siehe .github/workflows/2_publish.yml).
"""

import json
from faster_whisper import WhisperModel


def woerter_transkribieren(video_pfad: str) -> list:
    # "base"-Modell: guter Kompromiss zwischen Genauigkeit und Geschwindigkeit
    # für kurze Clips (60-90 Sekunden) auf einem CPU-only GitHub-Actions-Runner.
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(video_pfad, word_timestamps=True, language="de")

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
    woerter = woerter_transkribieren("output/video_roh.mp4")
    with open("output/captions.json", "w", encoding="utf-8") as f:
        json.dump(woerter, f, ensure_ascii=False, indent=2)
    print(f"{len(woerter)} Wörter transkribiert.")


if __name__ == "__main__":
    main()
