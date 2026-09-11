"""
SCHRITT 2 von 2: Erstellt das fertige Video aus pending_script.json.

Wird NICHT automatisch ausgeführt, sondern nur, wenn du ihn manuell über
den "Run workflow" Button in GitHub Actions startest (Workflow
"2 - Video erstellen"). So hast du vorher die Chance, pending_script.json
im Repository zu prüfen und bei Bedarf zu bearbeiten.

WICHTIG: Dieses Skript lädt das Video NICHT automatisch auf TikTok hoch
(TikTok hat den automatisierten Upload für private/individuelle Nutzung
abgelehnt - siehe PROJEKTUEBERBLICK.md, Abschnitt 'Wichtige Änderung').
Das fertige Video wird stattdessen als Download bereitgestellt (GitHub
Actions Artifact) - du lädst es manuell in der TikTok-App hoch (dauert
ca. 1 Minute).
"""

import json
import generate_video
import generate_background_image as generate_background
import transcribe_captions
import create_captions
import compose_video


def main():
    with open("pending_script.json", encoding="utf-8") as f:
        daten = json.load(f)
    print(f"Erstelle Video für: {daten['titel']}")

    print("\n=== Schritt 1/5: Avatar-Video generieren (D-ID) ===")
    generate_video.main()

    print("\n=== Schritt 2/5: Bewegten Hintergrund erstellen ===")
    generate_background.main()

    print("\n=== Schritt 3/5: Video transkribieren (Wort-Zeitstempel) ===")
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
