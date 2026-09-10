"""
Erstellt eine .ass Untertitel-Datei mit Wort-für-Wort Karaoke-Hervorhebung
aus den Zeitstempeln in output/captions.json.

Nutzt das .ass Format (Advanced SubStation Alpha), das native
Karaoke-Tags (\\k) unterstützt - ffmpegs "subtitles"-Filter (via libass)
rendert diese automatisch als wortweise eingefärbten Text, ohne dass wir
jedes Frame einzeln zeichnen müssen.
"""

import json

# Primärfarbe = noch nicht gesprochenes Wort (weiß)
# Sekundärfarbe = bereits gesprochenes/aktuelles Wort (Akzentfarbe, gelb-orange)
# Farben im .ass-Format sind &HAABBGGRR (umgekehrte Reihenfolge zu RGB!)
ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,68,&H00FFFFFF,&H0000D7FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,0,2,60,60,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def sekunden_zu_ass_zeit(sek: float) -> str:
    h = int(sek // 3600)
    m = int((sek % 3600) // 60)
    s = sek % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def zeilen_gruppieren(woerter: list, woerter_pro_zeile: int = 4) -> list:
    """Fasst Wörter zu kurzen Zeilen zusammen (bessere Lesbarkeit als
    Wort-für-Wort in eigenen Zeilen)."""
    gruppen = []
    for i in range(0, len(woerter), woerter_pro_zeile):
        gruppen.append(woerter[i:i + woerter_pro_zeile])
    return gruppen


def ass_erstellen(woerter: list, ziel_pfad: str):
    zeilen = [ASS_HEADER]
    gruppen = zeilen_gruppieren(woerter)

    for gruppe in gruppen:
        start = gruppe[0]["start"]
        ende = gruppe[-1]["end"]
        karaoke_text = ""
        for wort in gruppe:
            dauer_centisekunden = max(1, int((wort["end"] - wort["start"]) * 100))
            text = wort["text"].strip()
            karaoke_text += f"{{\\k{dauer_centisekunden}}}{text} "
        zeile = f"Dialogue: 0,{sekunden_zu_ass_zeit(start)},{sekunden_zu_ass_zeit(ende)},Default,,0,0,0,,{karaoke_text.strip()}\n"
        zeilen.append(zeile)

    with open(ziel_pfad, "w", encoding="utf-8") as f:
        f.writelines(zeilen)


def main():
    with open("output/captions.json", encoding="utf-8") as f:
        woerter = json.load(f)
    ass_erstellen(woerter, "output/captions.ass")
    print(f"Untertitel-Datei erstellt: output/captions.ass ({len(woerter)} Wörter)")


if __name__ == "__main__":
    main()
