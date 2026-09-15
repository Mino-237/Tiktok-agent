"""
SCHRITT 2 von 2: Erstellt das fertige Video aus pending_script.json.

Wird NICHT automatisch ausgeführt, sondern nur, wenn du ihn manuell über
den "Run workflow" Button in GitHub Actions startest (Workflow
"2 - Video erstellen"). So hast du vorher die Chance, pending_script.json
im Repository zu prüfen und bei Bedarf zu bearbeiten.

WACHSTUMSPHASE-VERSION: Kein D-ID/Brandon-Avatar mehr - das komplette
Skript wird über OpenAIs günstige Text-to-Speech-API vorgelesen. Das
spart D-ID-Kosten/Minuten-Limits komplett und ermöglicht mehrmals
tägliches Posten. Brandon kann später wieder aktiviert werden, sobald
der Fokus auf 60-90s Creator-Rewards-Videos wechselt.

NEUER ABLAUF (5 statt 6 Schritte):
1. OpenAI TTS liest das komplette Skript vor (Hook + Kern + CTA)
2. Hintergrund wird passend zur Gesamtlänge generiert (3 KI-Bilder)
3. Die Tonspur wird transkribiert (für Untertitel-Timing)
4. Karaoke-Untertitel werden erstellt
5. Alles wird zum finalen Video zusammengesetzt
"""

import json
import generate_voiceover
import generate_background_image
import transcribe_captions
import create_captions
import compose_video


def main():
    with open("pending_script.json", encoding="utf-8") as f:
        daten = json.load(f)
    print(f"Erstelle Video für: {daten['titel']}")

    print("\n=== Schritt 1/5: Voiceover für komplettes Skript (OpenAI TTS) ===")
    generate_voiceover.main()

    print("\n=== Schritt 2/5: Hintergrund aus 3 KI-Bildern erstellen ===")
    generate_background_image.main()

    print("\n=== Schritt 3/5: Tonspur transkribieren (Wort-Zeitstempel) ===")
    transcribe_captions.main()

    print("\n=== Schritt 4/5: Karaoke-Untertitel erstellen ===")
    create_captions.main()

    print("\n=== Schritt 5/5: Finales Video zusammensetzen ===")
    compose_video.video_zusammensetzen()

    print("\nFertig! Video liegt unter output/video_final.mp4")
    print("Lade es aus dem GitHub Actions Run als Artifact herunter und")
    print("poste es manuell in der TikTok-App.")


if __name__ == "__main__":
    main()



if __name__ == "__main__":
    main()
