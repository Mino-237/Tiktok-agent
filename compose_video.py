"""
Setzt das finale Video zusammen aus:
1. Bewegtem Hintergrund aus 3 KI-Bildern (output/background.mp4)
2. Wort-für-Wort animierten Karaoke-Untertiteln (output/captions.ass)
3. Logo-Overlay (assets/logo.png, optional)
4. Tonspur: output/voiceover_full.mp3 (komplettes OpenAI-Voiceover)

WICHTIGE ÄNDERUNG: Kein D-ID/Brandon-Avatar mehr - dadurch entfällt der
komplette Colorkey-/Masken-/Overlay-Aufwand von früher. Das Video ist
jetzt reiner Hintergrund + Untertitel + Ton, deutlich einfacher
zusammengesetzt.
"""

import subprocess
import os

HINTERGRUND = "output/background.mp4"
VOICEOVER = "output/voiceover_full.mp3"
UNTERTITEL = "output/captions.ass"
LOGO = "assets/logo.png"
FERTIGES_VIDEO = "output/video_final.mp4"


def video_zusammensetzen():
    inputs = [
        "-i", HINTERGRUND,
        "-i", VOICEOVER,
    ]

    logo_vorhanden = os.path.exists(LOGO)
    if logo_vorhanden:
        inputs += ["-i", LOGO]

    filter_complex = f"[0:v]subtitles={UNTERTITEL}[vout1]"

    if logo_vorhanden:
        filter_complex += ";[vout1][2:v]overlay=W-w-40:40[vout2]"  # oben rechts
        finaler_output = "[vout2]"
    else:
        finaler_output = "[vout1]"

    befehl = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", finaler_output,
        "-map", "1:a",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest",
        FERTIGES_VIDEO,
    ]
    subprocess.run(befehl, check=True)
    print(f"Finales Video erstellt: {FERTIGES_VIDEO}")


if __name__ == "__main__":
    video_zusammensetzen()
