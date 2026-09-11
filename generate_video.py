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

D-ID-Doku: https://docs.d-id.com/reference/createtalk
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

BASE_URL = "https://api.d-id.com"


def video_erstellen(skript_text: str) -> str:
    """Startet die Video-Generierung und gibt die talk_id zurück."""
    payload = {
        "source_url": AVATAR_BILD_URL,
        "script": {
            "type": "text",
            "input": skript_text,
            "provider": {"type": "microsoft", "voice_id": "de-DE-FlorianMultilingualNeural"}
            # Kein eigener "provider" angegeben -> D-ID nutzt die
            # Standard Microsoft-Stimme. Für eine konsistente deutsche
            # Stimme kann optional ergänzt werden:
        },
        "config": {"result_format": "mp4"},
    }
    headers = {
        "Authorization": f"Basic {DID_API_KEY}",
        "Content-Type": "application/json",
    }
    print(f"Avatar-URL Länge: {len(AVATAR_BILD_URL)}, Anfang: '{AVATAR_BILD_URL[:15]}', Ende: '{AVATAR_BILD_URL[-15:]}', hat Leerzeichen: {AVATAR_BILD_URL != AVATAR_BILD_URL.strip()}")
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

    skript_text = daten["vollstaendiges_skript"]

    print("Starte Video-Generierung bei D-ID (Talks API, Avatar Brandon)...")
    talk_id = video_erstellen(skript_text)

    print(f"Warte auf Fertigstellung (talk_id={talk_id})...")
    video_url, dauer = auf_fertigstellung_warten(talk_id)

    ziel_pfad = "output/video_roh.mp4"
    print(f"Lade Video herunter nach {ziel_pfad}...")
    video_herunterladen(video_url, ziel_pfad)

    # Dauer wird für den Hintergrund-Generator gebraucht (passende Länge)
    with open("output/video_meta.json", "w", encoding="utf-8") as f:
        json.dump({"duration": dauer}, f)

    print(f"Video-Generierung abgeschlossen. Dauer: {dauer:.1f}s")


if __name__ == "__main__":
    main()
