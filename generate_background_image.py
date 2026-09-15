"""
Erzeugt den Hintergrund: PRO SKRIPT-ABSCHNITT (Hook, Kern, CTA - das
neue verschlankte 3-Teile-Format für 20-30s Videos) wird ein eigenes,
thematisch passendes KI-Bild generiert (GPT Image 2) - im Stil einer
minimalistischen, illustrierten Erklär-Video-Figur (kein Foto-Realismus).

Die 3 Bilder werden nacheinander mit sanftem Zoom (Ken-Burns-Effekt) zu
einem einzigen Hintergrund-Video zusammengesetzt.

WICHTIGER FFMPEG-HINWEIS (siehe hintergrund_video_erstellen):
Jedes Bild-Input bekommt eine FESTE Framerate (-framerate FPS) und der
zoompan-Filter arbeitet mit d=1 (ein Ausgabebild pro Eingabebild, mit
kleinem Zoom-Schritt pro Bild). Wichtig, um einen bekannten
ffmpeg-Fallstrick zu vermeiden (siehe frühere Version dieser Datei für
Details zum Bug, den das behebt).

KOSTEN-HINWEIS: 3 Bilder statt vorher 5 pro Video - günstiger als der
vorherige Ansatz (~$0,12 statt ~$0,20 pro Video bei Medium-Qualität).
"""

import os
import json
import subprocess
import base64
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

BREITE, HOEHE = 1080, 1920
FPS = 30
MINDEST_DAUER_PRO_ABSCHNITT = 4.0  # Sekunden - Video ist insgesamt kürzer, also kleinerer Mindestwert

# Reihenfolge MUSS zur Struktur in generate_script.py passen
ABSCHNITTE = [
    ("hook", "Hook / einleitende Frage"),
    ("kern", "Kern-Erklärung des psychologischen Phänomens"),
    ("cta", "Abschließende Einladung zum Kommentieren"),
]

STIL_BESCHREIBUNG = (
    "Flat, modern illustrated digital art style featuring a simple, "
    "minimalist animated explainer-video character (stylized, symbolic, "
    "NOT a realistic face or photo), deep blue and purple color palette, "
    "soft glowing light, dreamlike and symbolic atmosphere, no text, no "
    "words, no letters, no logos, vertical portrait composition. "
    "Consistent, cohesive art style matching the rest of an illustration "
    "series for the same short video."
)


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


def abschnitts_dauern_berechnen(skript_daten: dict, gesamt_dauer: float) -> list:
    """Verteilt die verfügbare Gesamtdauer proportional zur Wortanzahl
    jedes Abschnitts, mit einer Mindestdauer pro Abschnitt."""
    woerter_pro_abschnitt = [
        len(skript_daten[feld].split()) for feld, _ in ABSCHNITTE
    ]
    gesamt_woerter = sum(woerter_pro_abschnitt) or 1

    ziel_gesamt = gesamt_dauer + 1  # kleiner Puffer

    roh_dauern = [
        ziel_gesamt * anzahl / gesamt_woerter for anzahl in woerter_pro_abschnitt
    ]
    return [max(MINDEST_DAUER_PRO_ABSCHNITT, d) for d in roh_dauern]


def hintergrund_video_erstellen(bild_pfade_und_dauern: list, ziel_pfad: str):
    """Baut aus mehreren Bildern + individuellen Anzeigedauern ein
    einziges Video mit Ken-Burns-Zoom pro Bild und nahtlosem Übergang."""
    inputs = []
    filter_teile = []

    for idx, (bild_pfad, dauer) in enumerate(bild_pfade_und_dauern):
        inputs += [
            "-framerate", str(FPS),
            "-loop", "1",
            "-t", str(dauer),
            "-i", bild_pfad,
        ]
        filter_teile.append(
            f"[{idx}:v]scale=2160:3840,"
            f"zoompan=z='min(zoom+0.0007,1.15)':"
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

    abschnitts_dauern = abschnitts_dauern_berechnen(skript_daten, dauer)

    bild_pfade_und_dauern = []
    for (feld, label), abschnitt_dauer in zip(ABSCHNITTE, abschnitts_dauern):
        abschnitt_text = skript_daten[feld]
        prompt = bild_prompt_erstellen(thema, label, abschnitt_text)
        ziel_pfad = f"output/hintergrund_{feld}.png"
        print(f"Generiere Bild für Abschnitt '{label}' ({abschnitt_dauer:.1f}s)...")
        bild_generieren(prompt, ziel_pfad)
        bild_pfade_und_dauern.append((ziel_pfad, abschnitt_dauer))

    print("Setze Hintergrund-Video aus 3 Bildern zusammen (Ken-Burns-Zoom)...")
    hintergrund_video_erstellen(bild_pfade_und_dauern, "output/background.mp4")

    print(f"Hintergrund erstellt: {sum(d for _, d in bild_pfade_und_dauern):.1f}s (3 Abschnitte)")


if __name__ == "__main__":
    main()



if __name__ == "__main__":
    main()
