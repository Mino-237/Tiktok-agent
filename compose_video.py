"""
Setzt das finale Video zusammen aus:
1. Bewegtem Partikel-Hintergrund (output/background.mp4)
2. D-ID Avatar-Video, oval zugeschnitten, unten rechts (weißer Hintergrund entfernt)
3. Wort-für-Wort animierten Karaoke-Untertiteln (output/captions.ass)
4. Logo-Overlay (assets/logo.png, optional)

Alle vier Ebenen werden in einem einzigen ffmpeg-Aufruf kombiniert.
"""

import subprocess
import os

from PIL import Image, ImageDraw

HINTERGRUND = "output/background.mp4"
AVATAR_ROH = "output/video_roh.mp4"
UNTERTITEL = "output/captions.ass"
LOGO = "assets/logo.png"
KREIS_MASKE = "output/kreis_maske.png"
FERTIGES_VIDEO = "output/video_final.mp4"

AVATAR_GROESSE = 380  # Durchmesser des ovalen Avatar-Ausschnitts in Pixeln
AVATAR_ABSTAND_RECHTS = 40
AVATAR_ABSTAND_UNTEN = 500  # Abstand vom unteren Rand, damit Platz für Untertitel bleibt


def kreis_maske_erstellen():
    """Erzeugt einmalig eine PNG-Maske (weißer Kreis auf schwarzem
    Hintergrund), die für den ovalen Avatar-Ausschnitt gebraucht wird."""
    maske = Image.new("L", (AVATAR_GROESSE, AVATAR_GROESSE), 0)
    draw = ImageDraw.Draw(maske)
    draw.ellipse([0, 0, AVATAR_GROESSE, AVATAR_GROESSE], fill=255)
    maske.save(KREIS_MASKE)


def video_zusammensetzen():
    kreis_maske_erstellen()

    inputs = [
        "-i", HINTERGRUND,
        "-i", AVATAR_ROH,
        "-i", KREIS_MASKE,
    ]

    logo_vorhanden = os.path.exists(LOGO)
    if logo_vorhanden:
        inputs += ["-i", LOGO]

    # Avatar: weißen Hintergrund per colorkey transparent machen, auf
    # AVATAR_GROESSE zuschneiden, dann mit der Kreismaske kombinieren
    # (colorkey-Alpha UND Kreismaske werden multipliziert, damit beide
    # Bedingungen gelten - siehe ausführliche Tests/Doku).
    filter_complex = (
        f"[1:v]colorkey=0xFFFFFF:0.08:0.0,"
        f"scale={AVATAR_GROESSE}:{AVATAR_GROESSE}:force_original_aspect_ratio=increase,"
        f"crop={AVATAR_GROESSE}:{AVATAR_GROESSE},format=yuva420p,split=2[a1][a2];"
        f"[a1]alphaextract[a1_alpha];"
        f"[a1_alpha][2:v]blend=all_mode=multiply,format=gray[maske_final];"
        f"[a2][maske_final]alphamerge[avatar_fertig];"
        f"[0:v][avatar_fertig]overlay=W-w-{AVATAR_ABSTAND_RECHTS}:H-h-{AVATAR_ABSTAND_UNTEN}[vout1];"
        f"[vout1]subtitles={UNTERTITEL}[vout2]"
    )

    if logo_vorhanden:
        filter_complex += f";[vout2][3:v]overlay=W-w-40:40[vout3]"  # oben rechts, kollidiert nicht mit Avatar/Untertiteln
        finaler_output = "[vout3]"
    else:
        finaler_output = "[vout2]"

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
