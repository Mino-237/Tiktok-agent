"""
Setzt das finale Video zusammen aus:
1. Bewegtem Hintergrund aus KI-Bildern (output/background.mp4)
2. Wort-für-Wort animierten Karaoke-Untertiteln (output/captions.ass)
3. Logo-Overlay (assets/logo.png, optional)
4. Tonspur: output/voiceover_full.mp3 (komplettes Azure-TTS-Voiceover)

NEU - SERIEN-BADGE: Kleines "Fakt #N"-Badge oben links, durchgehend
sichtbar - nutzt "folge_nummer" aus pending_script.json.

NEU - EFFEKT-MOMENT: Der Fachbegriff der Folge (aus thema_original,
Text in Klammern, z.B. "Blinder Fleck") poppt groß in der Bildmitte auf,
genau wenn der Kern-Teil beginnt (Timing aus video_meta.json,
"kern_start_zeit" - siehe generate_background_image.py).
"""

import subprocess
import os
import re
import json

HINTERGRUND = "output/background.mp4"
VOICEOVER = "output/voiceover_full.mp3"
UNTERTITEL = "output/captions.ass"
LOGO = "assets/logo.png"
FERTIGES_VIDEO = "output/video_final.mp4"

FONT_PFAD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
POP_DAUER = 1.3  # Sekunden, wie lange der Fachbegriff eingeblendet bleibt


def fachbegriff_ermitteln(skript_daten: dict) -> str:
    """Extrahiert den Fachbegriff aus thema_original, z.B. aus
    'Warum ... (Blinder Fleck)' wird 'Blinder Fleck'. Fällt auf den
    Titel zurück, falls keine Klammer gefunden wird."""
    thema = skript_daten.get("thema_original", "")
    treffer = re.search(r'\(([^)]+)\)\s*$', thema)
    if treffer:
        return treffer.group(1).strip()
    return skript_daten.get("titel", "")


def text_fuer_drawtext_escapen(text: str) -> str:
    """Escaped Sonderzeichen, die in ffmpegs drawtext-Filter-Syntax
    eine Bedeutung haben."""
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\u2019")  # normales Apostroph durch typografisches ersetzen, vermeidet Escaping-Ärger
    )


def video_zusammensetzen():
    with open("pending_script.json", encoding="utf-8") as f:
        skript_daten = json.load(f)

    with open("output/video_meta.json", encoding="utf-8") as f:
        meta = json.load(f)

    folge_nummer = skript_daten.get("folge_nummer")
    kern_start_zeit = meta.get("kern_start_zeit")
    fachbegriff = fachbegriff_ermitteln(skript_daten)

    inputs = [
        "-i", HINTERGRUND,
        "-i", VOICEOVER,
    ]

    logo_vorhanden = os.path.exists(LOGO)
    if logo_vorhanden:
        inputs += ["-i", LOGO]

    vorstufen_filter = []
    aktuelles_label = "0:v"

    # Serien-Badge oben links, durchgehend sichtbar
    if folge_nummer:
        badge_text = text_fuer_drawtext_escapen(f"Fakt #{folge_nummer}")
        vorstufen_filter.append(
            f"[{aktuelles_label}]drawtext=fontfile={FONT_PFAD}:text='{badge_text}':"
            f"fontsize=34:fontcolor=white:x=40:y=50:"
            f"box=1:boxcolor=black@0.35:boxborderw=14[vbadge]"
        )
        aktuelles_label = "vbadge"

    # Effekt-Moment: Fachbegriff ploppt groß in der Mitte auf, wenn der
    # Kern-Teil beginnt
    if fachbegriff and kern_start_zeit is not None:
        begriff_text = text_fuer_drawtext_escapen(fachbegriff)
        start = kern_start_zeit
        ende = start + POP_DAUER
        vorstufen_filter.append(
            f"[{aktuelles_label}]drawtext=fontfile={FONT_PFAD}:text='{begriff_text}':"
            f"fontsize=68:fontcolor=0xFFD24D:x=(w-text_w)/2:y=h*0.38:"
            f"box=1:boxcolor=black@0.45:boxborderw=24:"
            f"enable='between(t,{start:.2f},{ende:.2f})'[vpop]"
        )
        aktuelles_label = "vpop"

    vorstufen_filter.append(f"[{aktuelles_label}]subtitles={UNTERTITEL}[vout1]")

    if logo_vorhanden:
        logo_index = 2
        vorstufen_filter.append(f"[vout1][{logo_index}:v]overlay=W-w-40:40[vout2]")
        finaler_output = "[vout2]"
    else:
        finaler_output = "[vout1]"

    filter_complex = ";".join(vorstufen_filter)

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
if __name__ == "__main__":
    video_zusammensetzen()
