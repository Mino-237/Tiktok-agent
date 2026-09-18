"""
Generiert täglich (mehrmals täglich, manuell gestartet) ein Thema +
Kurz-Skript für die Serie "Warum tun wir das?". Nutzt die Anthropic API
(Claude), um einen Rohentwurf zu erstellen.

NEU - FOLGEN-ZÄHLER: Jedes Skript bekommt eine fortlaufende Folgen-
Nummer (video_zaehler.json), die NIE zurückgesetzt wird (anders als
die Themen-Historie, die bei einem neuen Zyklus geleert wird). Wird im
Video als kleines "Fakt #N"-Badge angezeigt (siehe compose_video.py) -
motiviert zum Folgen, um keine Folge zu verpassen.

WACHSTUMSPHASE-FORMAT: Verschlanktes 3-Teile-Format (Hook/Kern/CTA) für
20-30 Sekunden Videos.
"""

import os
import json
import random
from datetime import datetime
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

THEMEN_POOL_START = [
    "Warum du dir selbst öfter etwas vormachst als anderen (Selbsttäuschung)",
    "Warum wir Dinge aufschieben, obwohl wir wissen, dass es uns schadet (Prokrastination)",
    "Warum eine einzige schlechte Erinnerung zehn gute überstrahlt (Negativity Bias)",
    "Warum wir Fremden vertrauen, nur weil sie selbstbewusst wirken (Halo-Effekt)",
    "Warum Entscheidungen leichter fallen, wenn es weniger Optionen gibt (Choice Overload)",
    "Warum wir eigene Fehler bei anderen sofort erkennen (Blinder Fleck)",
    "Warum Gruppenzwang stärker wirkt, als wir zugeben wollen (Konformität)",
    "Warum wir uns an Anfang und Ende eines Erlebnisses am meisten erinnern (Peak-End-Regel)",
    "Warum wir teurere Dinge automatisch für besser halten (Preis-Qualitäts-Heuristik)",
    "Warum wir an einer schlechten Entscheidung festhalten, nur weil wir schon investiert haben (Sunk-Cost-Fallacy)",
    "Warum wir Dinge glauben, nur weil wir sie oft genug hören (Mere-Exposure-Effekt)",
    "Warum wir bei Gruppenentscheidungen schlechter entscheiden als allein (Groupthink)",
    "Warum wir uns an ein Trauma manchmal besser erinnern als an schöne Momente (Flashbulb Memory)",
    "Warum wir Menschen mögen, die uns ähnlich sind (Ähnlichkeits-Anziehung)",
    "Warum wir nach einer wichtigen Entscheidung deren Vorteile übertreiben (Kognitive Dissonanz)",
    "Warum wir Risiken bei Flugzeugen überschätzen und beim Autofahren unterschätzen (Verfügbarkeitsheuristik)",
    "Warum wir bei einem vollen Terminkalender produktiver wirken, aber weniger schaffen (Parkinson'sches Gesetz)",
    "Warum wir Fremden auf der Straße seltener helfen, wenn mehr Leute dabei sind (Bystander-Effekt)",
    "Warum wir uns an Anfänger-Fehler nicht erinnern, wenn wir Experten werden (Curse of Knowledge)",
    "Warum wir bei Multitasking eigentlich langsamer werden (Aufmerksamkeitsrestpartikel)",
]

KANAL_NISCHE = "Alltagspsychologie - kognitive Verzerrungen, Gewohnheiten und soziale Dynamiken, die erklären, warum Menschen sich so verhalten, wie sie es tun"

THEMEN_POOL_DATEI = "themen_pool.json"
THEMEN_HISTORIE_DATEI = "themen_historie.json"
ZAEHLER_DATEI = "video_zaehler.json"  # fortlaufend, wird NIE zurückgesetzt

MINDEST_PUFFER = 8
NEUE_THEMEN_PRO_NACHSCHUB = 20

MINDEST_WOERTER = 55
MAX_GENERIERUNGS_VERSUCHE = 3

SYSTEM_PROMPT = """Du hilfst dabei, ein KURZES 20-30 Sekunden Skript für ein TikTok-Format
namens "Warum tun wir das?" zu entwerfen. Das Format erklärt Alltagspsychologie
schnell, knackig und auf den Punkt - ideal für schnelles Scrollen.

STRUKTUR (immer einhalten, nur 3 Teile - Zeit ist knapp!):
1. HOOK: Eine provokante Frage direkt an den Zuschauer (1 kurzer Satz)
2. KERN: Das psychologische Phänomen benennen UND in einem Fluss erklären,
   warum es passiert - kompakt, ohne ausführliches Beispiel (3-4 Sätze)
3. CTA: Besteht aus ZWEI kurzen Teilen, die sich natürlich aneinanderreihen:
   a) Ein KURZER Übergangssatz (3-5 Wörter) - Reaktion/Fazit zum Thema,
      z.B. "Ziemlich verrückt, oder?" (abwechslungsreich, nicht immer gleich)
   b) Eine Like-und-Folgen-Einladung, angelehnt an genau diesen Wortlaut:
      "Lass doch gerne ein Like da und folge mir für mehr Psychologie-
      Wissen." Der Wortlaut darf leicht variiert werden, aber die
      Grundstruktur "Like da lassen" + "folge mir für mehr..." muss
      erhalten bleiben. KEINE separate Aufforderung zum Kommentieren.

WICHTIG:
- Einfache, gesprochene Sprache, keine Fachbegriffe ohne Erklärung
- Insgesamt MINDESTENS 55 Wörter, gerne bis 80 Wörter (für ~20-30
  Sekunden Sprechzeit). Diese Mindestanzahl ist eine HARTE Vorgabe.
- KEIN ausführliches Alltagsbeispiel - dafür ist bei dieser Kürze keine
  Zeit. Der "Aha-Moment" muss direkt im KERN stecken.
- Der komplette CTA (Übergangssatz + Like/Folgen-Einladung) sollte
  insgesamt nicht mehr als ca. 20 Wörter umfassen.
- Antworte NUR mit validem JSON, keine Markdown-Codeblöcke, kein Vorspann.

Format:
{
  "titel": "kurzer Arbeitstitel",
  "hook": "...",
  "kern": "...",
  "cta": "... (Übergangssatz + Like-/Folgen-Einladung, alles in einem Feld)",
  "vollstaendiges_skript": "Der komplette Text am Stück, so wie er gesprochen werden soll"
}
"""


def generiere_skript(thema: str) -> dict:
    """Lässt Claude ein Skript generieren und prüft danach die tatsächliche
    Wortanzahl. Falls das Skript trotz Vorgabe zu kurz ausfällt, wird bis
    zu MAX_GENERIERUNGS_VERSUCHE-mal neu generiert."""
    for versuch in range(1, MAX_GENERIERUNGS_VERSUCHE + 1):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"Thema für heute: {thema}"}
            ],
        )
        text = response.content[0].text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        daten = json.loads(text)

        woerter_anzahl = len(daten["vollstaendiges_skript"].split())
        if woerter_anzahl >= MINDEST_WOERTER:
            print(f"Skript hat {woerter_anzahl} Wörter (Versuch {versuch}/{MAX_GENERIERUNGS_VERSUCHE}) - ausreichend lang.")
            return daten

        print(
            f"Skript zu kurz ({woerter_anzahl} von mindestens {MINDEST_WOERTER} "
            f"Wörtern, Versuch {versuch}/{MAX_GENERIERUNGS_VERSUCHE}) - generiere erneut..."
        )

    raise ValueError(
        f"Konnte nach {MAX_GENERIERUNGS_VERSUCHE} Versuchen kein Skript mit "
        f"mindestens {MINDEST_WOERTER} Wörtern generieren. Bitte manuell prüfen."
    )


def naechste_folgen_nummer() -> int:
    """Liest den aktuellen Zählerstand, erhöht ihn um 1 und speichert
    ihn zurück. Wird NIE zurückgesetzt (anders als die Themen-Historie),
    damit die Folgen-Nummer im Video immer weiterzählt."""
    if os.path.exists(ZAEHLER_DATEI):
        with open(ZAEHLER_DATEI, encoding="utf-8") as f:
            zaehler_daten = json.load(f)
        nummer = zaehler_daten.get("anzahl", 0) + 1
    else:
        nummer = 1

    with open(ZAEHLER_DATEI, "w", encoding="utf-8") as f:
        json.dump({"anzahl": nummer}, f)

    return nummer


def pool_laden() -> list:
    if os.path.exists(THEMEN_POOL_DATEI):
        with open(THEMEN_POOL_DATEI, encoding="utf-8") as f:
            return json.load(f)
    return list(THEMEN_POOL_START)


def pool_speichern(pool: list):
    with open(THEMEN_POOL_DATEI, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)


def neue_themen_generieren(bereits_vorhandene_themen: list, anzahl: int) -> list:
    prompt = f"""Generiere {anzahl} neue, unterschiedliche Themen-Ideen für einen TikTok-Kanal
zum Thema "{KANAL_NISCHE}".

Jedes Thema soll im Format sein wie: "Warum [Verhalten/Phänomen] (Fachbegriff)"
- Genau wie diese Beispiele: "Warum wir Dingen mehr Wert beimessen, sobald sie uns gehören (Besitztumseffekt)"

WICHTIG:
- Keines der folgenden, bereits verwendeten Themen wiederholen oder zu stark ähneln:
{chr(10).join(f"- {t}" for t in bereits_vorhandene_themen)}

- Antworte NUR mit einem validen JSON-Array aus Strings, keine Markdown-Codeblöcke, kein Vorspann.
Beispiel: ["Warum ...", "Warum ...", ...]
"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def thema_ohne_wiederholung_waehlen() -> str:
    pool = pool_laden()

    if os.path.exists(THEMEN_HISTORIE_DATEI):
        with open(THEMEN_HISTORIE_DATEI, encoding="utf-8") as f:
            historie = json.load(f)
    else:
        historie = []

    verfuegbare_themen = [t for t in pool if t not in historie]

    if len(verfuegbare_themen) < MINDEST_PUFFER:
        print(f"Nur noch {len(verfuegbare_themen)} unbenutzte Themen übrig - generiere {NEUE_THEMEN_PRO_NACHSCHUB} neue nach...")
        try:
            neue_themen = neue_themen_generieren(pool, NEUE_THEMEN_PRO_NACHSCHUB)
            pool.extend(neue_themen)
            pool_speichern(pool)
            verfuegbare_themen = [t for t in pool if t not in historie]
            print(f"Pool erweitert um {len(neue_themen)} neue Themen. Insgesamt jetzt {len(pool)} Themen.")
        except Exception as e:
            print(f"Nachgenerierung fehlgeschlagen ({e}), nutze bestehenden Pool weiter.")

    if not verfuegbare_themen:
        historie = []
        verfuegbare_themen = pool

    gewaehltes_thema = random.choice(verfuegbare_themen)

    historie.append(gewaehltes_thema)
    with open(THEMEN_HISTORIE_DATEI, "w", encoding="utf-8") as f:
        json.dump(historie, f, ensure_ascii=False, indent=2)

    return gewaehltes_thema


def main():
    thema = thema_ohne_wiederholung_waehlen()
    daten = generiere_skript(thema)
    daten["thema_original"] = thema
    daten["datum"] = datetime.now().strftime("%Y-%m-%d")
    daten["folge_nummer"] = naechste_folgen_nummer()

    ausgabe_pfad = "pending_script.json"
    with open(ausgabe_pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)

    print(f"Skript erstellt: {daten['titel']} (Folge #{daten['folge_nummer']})")
    print(f"Gespeichert unter: {ausgabe_pfad}")


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
