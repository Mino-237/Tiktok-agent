"""
Setzt das finale Video zusammen aus:
1. Bewegtem Hintergrund aus KI-Bildern (output/background.mp4)
2. Wort-für-Wort animierten Karaoke-Untertiteln (output/captions.ass)
3. Logo-Overlay (assets/logo.png, optional)
4. Tonspur: output/voiceover_full.mp3
5. Sound-Effekt (assets/pop_sound.wav) beim Effekt-Moment

PRÄZISES TIMING FÜR DEN EFFEKT-MOMENT (überarbeitet): Es wird in
output/captions.json nach der Stelle gesucht, an der der Fachbegriff
GENAU gesprochen wird. NEU: Es reicht nicht mehr, nur das ERSTE Wort
des Fachbegriffs zu finden - bei mehrteiligen Begriffen (z.B. "Blinder
Fleck") muss auch das ZWEITE Wort kurz danach folgen. Grund: Ein
einzelnes Wort (z.B. "blind") kann später im Skript nochmal auftauchen
(z.B. in einem humorvollen CTA-Wortwitz wie "Club der blinden Spiegel")
- ohne diese Prüfung würde der Effekt-Moment fälschlich an dieser
späteren, falschen Stelle statt beim eigentlichen Kern-Teil ausgelöst.
"""

import subprocess
import os
import re
import json

HINTERGRUND = "output/background.mp4"
VOICEOVER = "output/voiceover_full.mp3"
UNTERTITEL = "output/captions.ass"
CAPTIONS_JSON = "output/captions.json"
LOGO = "assets/logo.png"
POP_SOUND = "assets/pop_sound.wav"
FERTIGES_VIDEO = "output/video_final.mp4"

FONT_PFAD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
POP_DAUER = 2.5
POP_SOUND_LAUTSTAERKE = 0.55

BADGE_AKTIV = False

BOUNCE_START_GROESSE = 20
BOUNCE_UEBERSCHWINGEN = 82
BOUNCE_ZIEL_GROESSE = 68
BOUNCE_WACHSEN_DAUER = 0.15
BOUNCE_EINPENDELN_DAUER = 0.12

SUCH_FENSTER_WOERTER = 3


def fachbegriff_ermitteln(skript_daten: dict) -> str:
    thema = skript_daten.get("thema_original", "")
    treffer = re.search(r'\(([^)]+)\)\s*$', thema)
    if treffer:
        return treffer.group(1).strip()
    return skript_daten.get("titel", "")


def wort_normalisieren(text: str) -> str:
    return re.sub(r'[^\wäöüß]', '', text.lower())


def levenshtein_distanz(a: str, b: str) -> int:
    """Zählt, wie viele Einzelbuchstaben-Änderungen nötig wären, um von
    Wort a zu Wort b zu kommen - toleriert kleinere Whisper-
    Erkennungsfehler bei ungewöhnlichen Wörtern (z.B. 'Riktanz' statt
    'Reaktanz')."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    vorherige_zeile = list(range(lb + 1))
    for i in range(1, la + 1):
        aktuelle_zeile = [i] + [0] * lb
        for j in range(1, lb + 1):
            kosten = 0 if a[i - 1] == b[j - 1] else 1
            aktuelle_zeile[j] = min(
                vorherige_zeile[j] + 1,
                aktuelle_zeile[j - 1] + 1,
                vorherige_zeile[j - 1] + kosten,
            )
        vorherige_zeile = aktuelle_zeile
    return vorherige_zeile[lb]


def wort_passt(gesucht_norm: str, kandidat_text: str) -> bool:
    kandidat_norm = wort_normalisieren(kandidat_text)
    if not kandidat_norm:
        return False
    if kandidat_norm == gesucht_norm:
        return True
    # Toleranz für Whisper-Erkennungsfehler bei ungewöhnlichen/
    # fremdsprachigen Wörtern - erlaubt ein paar Buchstaben-Abweichungen,
    # proportional zur Wortlänge
    max_abstand = max(2, len(gesucht_norm) // 3)
    if abs(len(kandidat_norm) - len(gesucht_norm)) <= max_abstand:
        if levenshtein_distanz(gesucht_norm, kandidat_norm) <= max_abstand:
            return True
    return False


def echten_start_zeitpunkt_suchen(fachbegriff: str, fallback: float) -> float:
    """Sucht in den echten Whisper-Zeitstempeln (captions.json) nach der
    Stelle, an der der KOMPLETTE Fachbegriff gesprochen wird (nicht nur
    ein einzelnes, eventuell mehrfach vorkommendes Wort davon)."""
    if not fachbegriff or not os.path.exists(CAPTIONS_JSON):
        return fallback

    fachbegriff_teile = [
        wort_normalisieren(w) for w in re.split(r'[\s\-]+', fachbegriff.strip())
    ]
    fachbegriff_teile = [t for t in fachbegriff_teile if t]
    if not fachbegriff_teile:
        return fallback

    with open(CAPTIONS_JSON, encoding="utf-8") as f:
        woerter = json.load(f)

    erstes_wort = fachbegriff_teile[0]

    if len(fachbegriff_teile) == 1:
        for wort in woerter:
            if wort_passt(erstes_wort, wort["text"]):
                return wort["start"]

        # Sicherheitsnetz: Whisper zerlegt ungewöhnliche Wörter manchmal
        # versehentlich in zwei Teile (z.B. "Re" + "Aktanz" statt
        # "Reaktanz"). Prüfe deshalb zusätzlich, ob zwei aufeinander-
        # folgende Wörter ZUSAMMEN (ähnlich) den gesuchten Begriff ergeben.
        for i in range(len(woerter) - 1):
            kombiniert = wort_normalisieren(woerter[i]["text"]) + wort_normalisieren(woerter[i + 1]["text"])
            max_abstand = max(2, len(erstes_wort) // 3)
            if kombiniert and abs(len(kombiniert) - len(erstes_wort)) <= max_abstand:
                if levenshtein_distanz(erstes_wort, kombiniert) <= max_abstand:
                    return woerter[i]["start"]

        return fallback

    zweites_wort = fachbegriff_teile[1]
    for i, wort in enumerate(woerter):
        if not wort_passt(erstes_wort, wort["text"]):
            continue
        fenster = woerter[i + 1:i + 1 + SUCH_FENSTER_WOERTER]
        if any(wort_passt(zweites_wort, w["text"]) for w in fenster):
            return wort["start"]

    for wort in woerter:
        if wort_passt(erstes_wort, wort["text"]):
            return wort["start"]

    return fallback


def text_fuer_drawtext_escapen(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\u2019")
    )


def bounce_fontsize_ausdruck(start: float) -> str:
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
    kern_start_zeit_geschaetzt = meta.get("kern_start_zeit")
    hintergrund_gesamtdauer = meta.get("hintergrund_gesamtdauer", meta.get("duration"))
    fachbegriff = fachbegriff_ermitteln(skript_daten)

    kern_start_zeit = echten_start_zeitpunkt_suchen(fachbegriff, kern_start_zeit_geschaetzt)
    if kern_start_zeit != kern_start_zeit_geschaetzt:
        print(f"Effekt-Moment-Timing aus echter Transkription übernommen: {kern_start_zeit:.2f}s (Schätzung war {kern_start_zeit_geschaetzt:.2f}s)")

    pop_sound_vorhanden = os.path.exists(POP_SOUND) and kern_start_zeit is not None

    inputs = [
        "-i", HINTERGRUND,
        "-i", VOICEOVER,
    ]

    logo_vorhanden = os.path.exists(LOGO)
    if logo_vorhanden:
        inputs += ["-i", LOGO]

    if pop_sound_vorhanden:
        inputs += ["-i", POP_SOUND]
        pop_sound_index = 3 if logo_vorhanden else 2

    vorstufen_filter = []
    aktuelles_label = "0:v"

    if BADGE_AKTIV and folge_nummer:
        badge_text = text_fuer_drawtext_escapen(f"Fakt #{folge_nummer}")
        vorstufen_filter.append(
            f"[{aktuelles_label}]drawtext=fontfile={FONT_PFAD}:text='{badge_text}':"
            f"fontsize=34:fontcolor=white:x=40:y=50:"
            f"box=1:boxcolor=black@0.35:boxborderw=14[vbadge]"
        )
        aktuelles_label = "vbadge"

    if fachbegriff and kern_start_zeit is not None:
        begriff_text = text_fuer_drawtext_escapen(fachbegriff)
        start = kern_start_zeit
        ende = start + POP_DAUER
        fontsize_ausdruck = bounce_fontsize_ausdruck(start)
        vorstufen_filter.append(
            f"[{aktuelles_label}]drawtext=fontfile={FONT_PFAD}:text='{begriff_text}':"
            f"fontsize='{fontsize_ausdruck}':fontcolor=0xFFD24D:"
            f"x=(w-text_w)/2:y=h*0.22:"
            f"box=1:boxcolor=black@0.45:boxborderw=24:"
            f"enable='between(t,{start:.2f},{ende:.2f})'[vpop]"
        )
        aktuelles_label = "vpop"

    vorstufen_filter.append(f"[{aktuelles_label}]subtitles={UNTERTITEL}[vout1]")

    if logo_vorhanden:
        logo_index = 2
        vorstufen_filter.append(f"[vout1][{logo_index}:v]overlay=W-w-40:40[vout2]")
        finaler_video_output = "[vout2]"
    else:
        finaler_video_output = "[vout1]"

    vorstufen_filter.append(
        f"[1:a]apad=whole_dur={hintergrund_gesamtdauer:.3f}[audio_gepolstert]"
    )
    aktuelles_audio_label = "audio_gepolstert"

    if pop_sound_vorhanden:
        delay_ms = int(kern_start_zeit * 1000)
        vorstufen_filter.append(
            f"[{pop_sound_index}:a]adelay={delay_ms}:all=1,volume={POP_SOUND_LAUTSTAERKE}[popsound]"
        )
        vorstufen_filter.append(
            f"[{aktuelles_audio_label}][popsound]amix=inputs=2:duration=first:normalize=0[aout]"
        )
        finaler_audio_output = "[aout]"
    else:
        finaler_audio_output = f"[{aktuelles_audio_label}]"

    filter_complex = ";".join(vorstufen_filter)

    befehl = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", finaler_video_output,
        "-map", finaler_audio_output,
        "-t", f"{hintergrund_gesamtdauer:.3f}",
        "-c:v", "libx264", "-c:a", "aac",
        FERTIGES_VIDEO,
    ]
    subprocess.run(befehl, check=True)
    print(f"Finales Video erstellt: {FERTIGES_VIDEO}")


if __name__ == "__main__":
    video_zusammensetzen()
