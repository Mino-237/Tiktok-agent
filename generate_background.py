"""
Erzeugt einen bewegten, abstrakten Partikel-Hintergrund passend zur
Video-Länge. Komplett prozedural erzeugt (kein Stock-Footage, keine
Urheberrechts-Bedenken).
"""

import subprocess
import json
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BREITE, HOEHE = 1080, 1920
FPS = 30
FARBPALETTE = [(88, 101, 242), (147, 112, 219), (72, 61, 139), (60, 90, 180)]
HINTERGRUND_FARBE = (14, 14, 28)


class Partikel:
    def __init__(self):
        self.x = random.uniform(0, BREITE)
        self.y = random.uniform(0, HOEHE)
        self.radius = random.uniform(160, 320)
        self.farbe = random.choice(FARBPALETTE)
        self.phase_x = random.uniform(0, math.pi * 2)
        self.phase_y = random.uniform(0, math.pi * 2)
        self.geschwindigkeit = random.uniform(0.15, 0.3)

    def position(self, t):
        x = self.x + math.sin(t * self.geschwindigkeit + self.phase_x) * 140
        y = self.y + math.cos(t * self.geschwindigkeit * 0.8 + self.phase_y) * 140
        return x, y


def frame_rendern(partikel_liste, t):
    layer = Image.new("RGB", (BREITE, HOEHE), HINTERGRUND_FARBE)
    draw = ImageDraw.Draw(layer)
    for p in partikel_liste:
        x, y = p.position(t)
        bbox = [x - p.radius, y - p.radius, x + p.radius, y + p.radius]
        draw.ellipse(bbox, fill=p.farbe)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=90))
    grund = Image.new("RGB", (BREITE, HOEHE), HINTERGRUND_FARBE)
    return Image.blend(grund, layer, alpha=0.75)


def hintergrund_erstellen(dauer_sekunden: float, ziel_pfad: str):
    anzahl_frames = int((dauer_sekunden + 1) * FPS)
    partikel_liste = [Partikel() for _ in range(5)]

    befehl = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{BREITE}x{HOEHE}", "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        ziel_pfad,
    ]
    prozess = subprocess.Popen(befehl, stdin=subprocess.PIPE)

    for frame_nr in range(anzahl_frames):
        t = frame_nr / FPS
        img = frame_rendern(partikel_liste, t)
        prozess.stdin.write(np.array(img).tobytes())

    prozess.stdin.close()
    prozess.wait()


def main():
    with open("output/video_meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    dauer = meta["duration"]
    hintergrund_erstellen(dauer, "output/background.mp4")
    print(f"Hintergrund erstellt: {dauer:.1f}s")


if __name__ == "__main__":
    main()
