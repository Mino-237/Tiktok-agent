"""
Setzt das finale Video zusammen aus:
1. Bewegtem Hintergrund aus KI-Bildern (output/background.mp4)
2. Wort-für-Wort animierten Karaoke-Untertiteln (output/captions.ass)
3. Logo-Overlay (assets/logo.png, optional)
4. Tonspur: output/voiceover_full.mp3 (komplettes Azure-TTS-Voiceover)

SERIEN-BADGE: Kleines "Fakt #N"-Badge oben links, durchgehend sichtbar.

EFFEKT-MOMENT (aktualisiert): Der Fachbegriff der Folge poppt jetzt mit
einer kurzen "Bounce"-Animation auf (wächst leicht über die Zielgröße
hinaus und federt zurück, statt einfach nur zu erscheinen) und bleibt
länger sichtbar (POP_DAUER = 2,5s statt vorher 1,3s).
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
POP_DAUER = 2.5  # Sekunden, wie lange der Fachbegriff insgesamt sichtbar bleibt

# Bounce-Animation-Einstellungen (Schriftgröße über die Zeit)
BOUNCE_START_GROESSE = 20   # Startgröße beim Auftauchen (sehr klein)
BOUNCE_UEBERSCHWINGEN = 82  # kurz über die Zielgröße hinauswachsen ("Bounce")
BOUNCE_ZIEL_GROESSE = 68    # Größe, bei der es sich einpendelt
BOUNCE_WACHSEN_DAUER = 0.15   # Sekunden bis zum Überschwingen
BOUNCE_EINPENDELN_DAUER = 0.12  # Sekunden vom Überschwingen bis zur Zielgröße


def fachbegriff_ermitteln(skript_daten: dict) -> str:
    """Extrahiert den Fachbegriff aus thema_original, z.B. aus
    'Warum ... (Blinder Fleck)' wird 'Blinder Fleck'."""
    thema = skript_daten.get("thema_original", "")
    treffer = re.search(r'\(([^)]+)\)\s*$', thema)
    if treffer:
        return treffer.group(1).strip()
    return skript_daten.get("titel", "")


def text_fuer_drawtext_escapen(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\u2019")
    )


def bounce_fontsize_ausdruck(start: float) -> str:
    """Baut einen ffmpeg-Ausdruck, der die Schriftgröße über die Zeit
    animiert: schnelles Wachsen -> kurzes Überschwingen -> Einpendeln
    auf die Zielgröße. Ergibt einen kleinen "Bounce"-Effekt beim
    Auftauchen des Textes."""
    t1 = start + BOUNCE_WACHSEN_DAUER
    t2 = t1 + BOUNCE_EINPENDELN_DAUER
    return (
        f"if(lt(t,{t1:.3f}),"
        f"{BOUNCE_START_GROESSE}+({BOUNCE_UEBERSCHWINGEN}-{BOUNCE_START_GROESSE})*(t-{start:.3f})/{BOUNCE_WACHSEN_DAUER},"
        f"if(lt(t,{t2:.3f}),"
        f"{BOUNCE_UEBERSCHWINGEN}-({BOUNCE_UEBERSCHWINGEN}-{BOUNCE_ZIEL_GROESSE})*(t-{t1:.3f})/{BOUNCE_EINPENDELN_DAUER},"
        f"{BOUNCE_ZIEL_GROESSE}))"
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

    # Effekt-Moment: Fachbegriff poppt mit Bounce-Animation auf, wenn
    # der Kern-Teil beginnt, und bleibt POP_DAUER Sekunden sichtbar
    if fachbegriff and kern_start_zeit is not None:
        begriff_text = text_fuer_drawtext_escapen(fachbegriff)
        start = kern_start_zeit
        ende = start + POP_DAUER
        fontsize_ausdruck = bounce_fontsize_ausdruck(start)
        vorstufen_filter.append(
            f"[{aktuelles_label}]drawtext=fontfile={FONT_PFAD}:text='{begriff_text}':"
            f"fontsize='{fontsize_ausdruck}':fontcolor=0xFFD24D:"
            f"x=(w-text_w)/2:y=h*0.38:"
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
if __name__ == "__main__":
    video_zusammensetzen()
