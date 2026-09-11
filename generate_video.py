"""
Erstellt aus dem Skript ein Avatar-Video via D-ID Talks API.

WICHTIG: Wir nutzen die TALKS API (nicht die Clips API) mit dem Avatar
"Brandon" (V2 Standard-Avatar). Grund: Clips API / "V3 Pro Avatars" (wie
der ursprünglich geplante Avatar "Frank") sind auf dem D-ID Lite-Plan
NICHT verfügbar und bleiben für immer im Status "created" hängen, ohne
klare Fehlermeldung. V2-Avatare wie Brandon funktionieren zuverlässig
auf Lite.

Avatar-Bild liegt öffentlich im GitHub-Pages Rechtstexte-Repo (dasselbe,
das auch für Terms/Privacy genutzt wird).

STIMME: de-DE-FlorianMultilingualNeural (natürlicher/moderner als die
ältere de-DE-ConradNeural-Stimme).

NATÜRLICHERER KLANG: Statt den kompletten Text als einen einzigen Block
vorzulesen, wird das Skript aus seinen 5 einzelnen Abschnitten (Hook,
Phänomen, Erklärung, Beispiel, CTA) zusammengesetzt und zwischen jedem
Abschnitt eine kurze SSML-Sprechpause eingefügt. Das sorgt für einen
Rhythmus, der eher nach "jemand erzählt/fragt etwas" klingt als nach
"jemand liest einen Text ab". Die Frage im Hook bekommt durch das
Fragezeichen automatisch die natürliche, ansteigende Frage-Betonung von
Azure TTS - dafür ist keine zusätzliche SSML-Auszeichnung nötig.

D-ID-Doku: https://docs.d-id.com/reference/createtalk
D-ID SSML/Pausen-Doku: https://docs.d-id.com/reference/microsoft-azure
"""

import os
import time
import json
import requests

DID_API_KEY = os.environ["DID_API_KEY"]  # Format: "email:key" o.ä., wird als "Basic <KEY>" gesendet (KEIN zusätzliches Base64 nötig)
# Öffentliche URL zum Avatar-Bild (Brandon). Immer dasselbe Bild nutzen,
# für ein konsistentes "Kanal-Gesicht".
AVATAR_BILD_URL = os.environ.get(
    "DID_AVATAR_IMAGE_URL",
    "https://mino-237.github.io/meine-tiktok-app-legal/Brandon-avatar.png",
)

STIMME = "de-DE-FlorianMultilingualNeural"

# TikTok Creator Rewards verlangt mindestens 60 Sekunden Videolänge.
MINDEST_DAUER_SEKUNDEN = 60

BASE_URL = "https://api.d-id.com"


def escape_fuer_ssml(text: str) -> str:
    """Ersetzt XML-Sonderzeichen, damit sie im SSML-Input nicht versehentlich
    als Markup interpretiert werden."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def ssml_input_erstellen(daten: dict) -> str:
    """Baut den SSML-Input aus den 5 Skript-Abschnitten, mit kurzen
    Sprechpausen dazwischen für einen natürlicheren Sprechrhythmus."""
    abschnitte = [
        daten["hook"],
        daten["phaenomen"],
        daten["erklaerung"],
        daten["beispiel"],
        daten["cta"],
    ]
    pause = '<break time="550ms"/>'
    return pause.join(escape_fuer_ssml(a.strip()) for a in abschnitte)


def video_erstellen(daten: dict) -> str:
    """Startet die Video-Generierung und gibt die talk_id zurück."""
    ssml_input = ssml_input_erstellen(daten)
    payload = {
        "source_url": AVATAR_BILD_URL,
        "script": {
            "type": "text",
            "ssml": True,
            "input": ssml_input,
            "provider": {"type": "microsoft", "voice_id": STIMME},
        },
        "config": {"result_format": "mp4"},
    }
    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.post(f"{BASE_URL}/talks", json=payload, headers=headers)
    if not r.ok:
        print(f"D-ID Antwort (Status {r.status_code}): {r.text}")
    r.raise_for_status()
    return r.json()["id"]


def auf_fertigstellung_warten(talk_id: str, timeout_sekunden: int = 600) -> tuple:
    """Pollt den Status, bis das Video fertig ist. Gibt (Download-URL, Dauer in Sekunden) zurück."""
    headers = {"Authorization": f"Basic {DID_API_KEY}"}
    start = time.time()
    while time.time() - start < timeout_sekunden:
        r = requests.get(f"{BASE_URL}/talks/{talk_id}", headers=headers)
        r.raise_for_status()
        daten = r.json()
        status = daten.get("status")
        if status == "done":
            return daten["result_url"], daten.get("duration", 0)
        if status == "error":
            raise RuntimeError(f"D-ID Video-Generierung fehlgeschlagen: {daten}")
        time.sleep(10)
    raise TimeoutError("Video wurde nicht rechtzeitig fertig.")


def video_herunterladen(video_url: str, ziel_pfad: str):
    r = requests.get(video_url, stream=True)
    r.raise_for_status()
    os.makedirs(os.path.dirname(ziel_pfad), exist_ok=True)
    with open(ziel_pfad, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)


def main():
    with open("pending_script.json", encoding="utf-8") as f:
        daten = json.load(f)

    print("Starte Video-Generierung bei D-ID (Talks API, Avatar Brandon)...")
    talk_id = video_erstellen(daten)

    print(f"Warte auf Fertigstellung (talk_id={talk_id})...")
    video_url, dauer = auf_fertigstellung_warten(talk_id)

    if dauer < MINDEST_DAUER_SEKUNDEN:
        raise ValueError(
            f"Video ist nur {dauer:.1f}s lang (unter dem "
            f"{MINDEST_DAUER_SEKUNDEN}s-Minimum für TikTok Creator Rewards). "
            f"Skript in pending_script.json verlängern und Workflow 2 "
            f"erneut starten."
        )

    ziel_pfad = "output/video_roh.mp4"
    print(f"Lade Video herunter nach {ziel_pfad}...")
    video_herunterladen(video_url, ziel_pfad)

    # Dauer wird für den Hintergrund-Generator gebraucht (passende Länge)
    with open("output/video_meta.json", "w", encoding="utf-8") as f:
        json.dump({"duration": dauer}, f)

    print(f"Video-Generierung abgeschlossen. Dauer: {dauer:.1f}s")


if __name__ == "__main__":
    main()
