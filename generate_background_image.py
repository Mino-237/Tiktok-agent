"""
Erzeugt den Hintergrund: PRO SKRIPT-ABSCHNITT wird ein eigenes,
thematisch passendes KI-Bild generiert (GPT Image 2) - im Stil einer
minimalistischen, illustrierten Erklär-Video-Figur (kein Foto-Realismus).

Der "Kern"-Abschnitt wird automatisch anhand seiner Sätze in mehrere
Teilbilder aufgeteilt (KERN_TEILE_ANZAHL), damit im textreichsten Teil
mehr Bildwechsel passieren, statt dass ein einziges Bild fast die ganze
Videolänge stehen bleibt.

NEU - ZOOM-PUNCH BEIM HOOK: Das allererste Bild (Hook) bekommt einen
schnellen, auffälligen Zoom-Punch in den ersten ~0,7 Sekunden (statt des
gewohnten sanften Ken-Burns-Zooms), um einen stärkeren "Scroll-Stopp"-
Moment zu erzeugen. Danach geht der Zoom nahtlos in den normalen,
sanften Zoom über. Alle anderen Abschnitte behalten den gewohnten
sanften Zoom.

Die Bilder werden nacheinander mit Zoom-Effekt zu einem einzigen
Hintergrund-Video zusammengesetzt.
"""

import os
import re
import json
import math
import subprocess
import base64
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

BREITE, HOEHE = 1080, 1920
FPS = 30
MINDEST_DAUER_PRO_ABSCHNITT = 3.5  # Sekunden
KERN_TEILE_ANZAHL = 2  # in wie viele Teilbilder der "Kern"-Abschnitt aufgeteilt wird

# Zoom-Punch-Einstellungen für den Hook (erstes Bild)
PUNCH_DAUER_FRAMES = 20  # ca. 0,67s bei 30 FPS - Dauer des schnellen Zoom-Punches
PUNCH_ZOOM_ZIEL = 1.28   # wie stark reingezoomt wird, bevor der sanfte Zoom übernimmt

STIL_BESCHREIBUNG = (
    "Flat, modern illustrated digital art style featuring a simple, "
    "minimalist animated explainer-video character (stylized, symbolic, "
    "NOT a realistic face or photo), deep blue and purple color palette, "
    "soft glowing light, dreamlike and symbolic atmosphere, no text, no "
    "words, no letters, no logos, vertical portrait composition. "
    "Consistent, cohesive art style matching the rest of an illustration "
    "series for the same short video."
)


def kern_in_teile_splitten(kern_text: str, anzahl_teile: int = KERN_TEILE_ANZAHL) -> list:
    """Teilt den Kern-Text anhand von Satzgrenzen in ungefähr gleich
    lange Teile auf. Falls zu wenige Sätze vorhanden sind, wird der Text
    unverändert als ein einziges Teil zurückgegeben."""
    saetze = [s.strip() for s in re.split(r'(?<=[.!?])\s+', kern_text.strip()) if s.strip()]
    if len(saetze) <= 1:
        return [kern_text.strip()]

    saetze_pro_teil = math.ceil(len(saetze) / anzahl_teile)
    teile = [
        " ".join(saetze[i:i + saetze_pro_teil])
        for i in range(0, len(saetze), saetze_pro_teil)
    ]
    return teile


def abschnitte_erstellen(skript_daten: dict) -> list:
    """Baut die Liste aller Bild-Abschnitte: Hook, die aufgeteilten
    Kern-Teile, und CTA - jeweils als (Label, Text)-Paar."""
    abschnitte = [("Hook / einleitende Frage", skript_daten["hook"])]

    kern_teile = kern_in_teile_splitten(skript_daten["kern"])
    for i, teil_text in enumerate(kern_teile, start=1):
        abschnitte.append((f"Kern-Erklärung Teil {i}/{len(kern_teile)}", teil_text))

    abschnitte.append(("Abschließende Einladung zum Kommentieren", skript_daten["cta"]))
    return abschnitte


def bild_prompt_erstellen(thema: str, abschnitt_label: str, abschnitt_text: str) -> str:
    return (
        f"{STIL_BESCHREIBUNG} This specific illustration represents the "
        f"'{abschnitt_label}' moment of a short explainer video about the "
        f"psychological concept '{thema}'. Scene context: {abschnitt_text}"
    )


def bild_generieren(prompt: str, ziel_pfad: str):
    response = client.images.generate(
        model="gpt-image-2",
        prompt=prompt,
        size="1024x1536",
        quality="medium",
        n=1,
    )
    bild_base64 = response.data[0].b64_json
    with open(ziel_pfad, "wb") as f:
        f.write(base64.b64decode(bild_base64))


def abschnitts_dauern_berechnen(abschnitte: list, gesamt_dauer: float) -> list:
    """Verteilt die verfügbare Gesamtdauer proportional zur Wortanzahl
    jedes Abschnitts, mit einer Mindestdauer pro Abschnitt."""
    woerter_pro_abschnitt = [len(text.split()) for _, text in abschnitte]
    gesamt_woerter = sum(woerter_pro_abschnitt) or 1

    ziel_gesamt = gesamt_dauer + 1  # kleiner Puffer

    roh_dauern = [
        ziel_gesamt * anzahl / gesamt_woerter for anzahl in woerter_pro_abschnitt
    ]
    return [max(MINDEST_DAUER_PRO_ABSCHNITT, d) for d in roh_dauern]


def zoom_ausdruck_erstellen(ist_hook: bool) -> str:
    """Baut den zoompan-Zoom-Ausdruck. Der Hook bekommt einen schnellen
    Zoom-Punch in den ersten PUNCH_DAUER_FRAMES Frames, danach (bzw. bei
    allen anderen Abschnitten von Anfang an) den gewohnten sanften Zoom."""
    if ist_hook:
        punch_rate = (PUNCH_ZOOM_ZIEL - 1) / PUNCH_DAUER_FRAMES
        return (
            f"if(lte(on,{PUNCH_DAUER_FRAMES}),"
            f"1+on*{punch_rate:.5f},"
            f"min({PUNCH_ZOOM_ZIEL}+(on-{PUNCH_DAUER_FRAMES})*0.0007,1.5))"
        )
    return "min(zoom+0.0007,1.15)"


def hintergrund_video_erstellen(bild_pfade_und_dauern: list, ziel_pfad: str):
    """Baut aus mehreren Bildern + individuellen Anzeigedauern ein
    einziges Video mit Zoom-Effekt pro Bild und nahtlosem Übergang.
    Das erste Bild (Hook) bekommt einen schnellen Zoom-Punch, alle
    anderen den gewohnten sanften Ken-Burns-Zoom."""
    inputs = []
    filter_teile = []

    for idx, (bild_pfad, dauer) in enumerate(bild_pfade_und_dauern):
        inputs += [
            "-framerate", str(FPS),
            "-loop", "1",
            "-t", str(dauer),
            "-i", bild_pfad,
        ]
        zoom_ausdruck = zoom_ausdruck_erstellen(ist_hook=(idx == 0))
        filter_teile.append(
            f"[{idx}:v]scale=2160:3840,"
            f"zoompan=z='{zoom_ausdruck}':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d=1:s={BREITE}x{HOEHE}:fps={FPS},setsar=1[v{idx}]"
        )

    concat_eingaenge = "".join(f"[v{idx}]" for idx in range(len(bild_pfade_und_dauern)))
    filter_complex = (
        ";".join(filter_teile)
        + f";{concat_eingaenge}concat=n={len(bild_pfade_und_dauern)}:v=1:a=0[vout]"
    )

    befehl = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        ziel_pfad,
    ]
    subprocess.run(befehl, check=True)


def main():
    with open("output/video_meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    dauer = meta["duration"]

    with open("pending_script.json", encoding="utf-8") as f:
        skript_daten = json.load(f)
    thema = skript_daten.get("thema_original", skript_daten.get("titel", ""))

    abschnitte = abschnitte_erstellen(skript_daten)
    abschnitts_dauern = abschnitts_dauern_berechnen(abschnitte, dauer)

    bild_pfade_und_dauern = []
    for idx, ((label, abschnitt_text), abschnitt_dauer) in enumerate(zip(abschnitte, abschnitts_dauern)):
        prompt = bild_prompt_erstellen(thema, label, abschnitt_text)
        ziel_pfad = f"output/hintergrund_{idx}.png"
        print(f"Generiere Bild für Abschnitt '{label}' ({abschnitt_dauer:.1f}s)...")
        bild_generieren(prompt, ziel_pfad)
        bild_pfade_und_dauern.append((ziel_pfad, abschnitt_dauer))

    print(f"Setze Hintergrund-Video aus {len(bild_pfade_und_dauern)} Bildern zusammen (Hook mit Zoom-Punch)...")
    hintergrund_video_erstellen(bild_pfade_und_dauern, "output/background.mp4")

    print(f"Hintergrund erstellt: {sum(d for _, d in bild_pfade_und_dauern):.1f}s ({len(bild_pfade_und_dauern)} Abschnitte)")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
