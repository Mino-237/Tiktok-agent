"""
Generiert täglich ein Thema + Skript für die Serie "Warum tun wir das?".
Nutzt die Anthropic API (Claude), um einen Rohentwurf zu erstellen.

Das Skript ist bewusst NICHT vollautomatisch final - der Sinn ist,
dass du (oder ein kurzer manueller Review-Schritt) den Text noch
mit eigener Meinung/Formulierung anreicherst, bevor er ins Video geht.
Das hilft auch dabei, nicht als "reiner KI-Recycling-Content" zu gelten.
"""

import os
import json
import random
from datetime import datetime
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Startpunkt-Themenpool. Wird bei Bedarf AUTOMATISCH um neue Themen
# erweitert (siehe pool_bei_bedarf_erweitern() weiter unten) - du musst
# hier nichts nachpflegen. Diese Liste ist nur der Anfang, damit der
# Kanal von Tag 1 an Varianz hat.
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

# Diese Beschreibung wird genutzt, wenn Claude automatisch NEUE Themen
# nachgeneriert - passt die "Handschrift" des Kanals an, falls du die
# Nische änderst (z.B. auf Finanzen oder Geschichte statt Psychologie).
KANAL_NISCHE = "Alltagspsychologie - kognitive Verzerrungen, Gewohnheiten und soziale Dynamiken, die erklären, warum Menschen sich so verhalten, wie sie es tun"

# Dateien, in denen der wachsende Themenpool und die Nutzungs-Historie
# gespeichert werden. Beide werden vom GitHub-Actions-Workflow nach
# jedem Lauf automatisch zurück ins Repository committed.
THEMEN_POOL_DATEI = "themen_pool.json"
THEMEN_HISTORIE_DATEI = "themen_historie.json"

# Sobald weniger als so viele unbenutzte Themen übrig sind, generiert
# Claude automatisch neue nach - dadurch geht dem Kanal nie der Stoff aus.
MINDEST_PUFFER = 8
NEUE_THEMEN_PRO_NACHSCHUB = 20

SYSTEM_PROMPT = """Du hilfst dabei, ein 60-90 Sekunden Skript für ein TikTok-Format
namens "Warum tun wir das?" zu entwerfen. Das Format erklärt Alltagspsychologie
verständlich und mit einem konkreten Beispiel.

STRUKTUR (immer einhalten):
1. HOOK: Eine provokante Frage direkt an den Zuschauer (1 Satz)
2. PHÄNOMEN: Das psychologische Phänomen kurz benennen (1-2 Sätze)
3. ERKLÄRUNG: Warum passiert das im Gehirn/Verhalten (2-3 Sätze, einfache Sprache)
4. BEISPIEL: Ein konkretes, alltagsnahes Beispiel (2-3 Sätze)
5. CTA: Ein Satz, der zum Kommentieren einlädt

WICHTIG:
- Einfache, gesprochene Sprache, keine Fachbegriffe ohne Erklärung
- Insgesamt 190-230 Wörter (für ~75-95 Sekunden Sprechzeit, WICHTIG: unbedingt über 65 Sekunden, TikTok Creator Rewards verlangt mindestens 60 Sekunden)
- Antworte NUR mit validem JSON, keine Markdown-Codeblöcke, kein Vorspann.

Format:
{
  "titel": "kurzer Arbeitstitel",
  "hook": "...",
  "phaenomen": "...",
  "erklaerung": "...",
  "beispiel": "...",
  "cta": "...",
  "vollstaendiges_skript": "Der komplette Text am Stück, so wie er gesprochen werden soll"
}
"""


def generiere_skript(thema: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Thema für heute: {thema}"}
        ],
    )
    text = response.content[0].text.strip()
    # Falls Claude trotz Anweisung Codeblock-Fences liefert, entfernen wir sie sicherheitshalber
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def pool_laden() -> list:
    """Lädt den aktuellen (ggf. bereits erweiterten) Themenpool von Disk,
    oder legt ihn beim allerersten Lauf mit dem Startpool an."""
    if os.path.exists(THEMEN_POOL_DATEI):
        with open(THEMEN_POOL_DATEI, encoding="utf-8") as f:
            return json.load(f)
    return list(THEMEN_POOL_START)


def pool_speichern(pool: list):
    with open(THEMEN_POOL_DATEI, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)


def neue_themen_generieren(bereits_vorhandene_themen: list, anzahl: int) -> list:
    """
    Lässt Claude eine Liste neuer, noch nicht verwendeter Themen für die
    Kanal-Nische generieren. Wird automatisch aufgerufen, sobald der
    Puffer an unbenutzten Themen zur Neige geht - dadurch geht dem Kanal
    nie der Stoff aus, ohne dass manuell etwas nachgepflegt werden muss.
    """
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
    """
    Wählt ein Thema, das noch nicht kürzlich verwendet wurde. Falls der
    Puffer an unbenutzten Themen zur Neige geht, lässt Claude automatisch
    neue Themen nachgenerieren und erweitert den Pool dauerhaft - der
    Kanal läuft dadurch unbegrenzt weiter, ohne dass Themen manuell
    nachgepflegt werden müssen.
    """
    pool = pool_laden()

    if os.path.exists(THEMEN_HISTORIE_DATEI):
        with open(THEMEN_HISTORIE_DATEI, encoding="utf-8") as f:
            historie = json.load(f)
    else:
        historie = []

    verfuegbare_themen = [t for t in pool if t not in historie]

    # Puffer wird knapp -> automatisch neue Themen nachgenerieren
    if len(verfuegbare_themen) < MINDEST_PUFFER:
        print(f"Nur noch {len(verfuegbare_themen)} unbenutzte Themen übrig - generiere {NEUE_THEMEN_PRO_NACHSCHUB} neue nach...")
        try:
            neue_themen = neue_themen_generieren(pool, NEUE_THEMEN_PRO_NACHSCHUB)
            pool.extend(neue_themen)
            pool_speichern(pool)
            verfuegbare_themen = [t for t in pool if t not in historie]
            print(f"Pool erweitert um {len(neue_themen)} neue Themen. Insgesamt jetzt {len(pool)} Themen.")
        except Exception as e:
            # Falls die Nachgenerierung fehlschlägt (z.B. API-Problem),
            # nicht den ganzen Lauf abbrechen - einfach mit dem
            # bestehenden Pool weitermachen. Beim nächsten Lauf wird es
            # erneut versucht.
            print(f"Nachgenerierung fehlgeschlagen ({e}), nutze bestehenden Pool weiter.")

    # Falls trotz allem alle Themen verbraucht sind (z.B. Nachgenerierung
    # fehlgeschlagen und Pool war schon komplett durch) -> Zyklus neu starten
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

    # Wird im Hauptverzeichnis (nicht in output/) gespeichert, damit die
    # Datei zwischen den zwei getrennten Workflow-Läufen (Generieren und
    # Veröffentlichen) bestehen bleibt - output/ wird nicht committed.
    ausgabe_pfad = "pending_script.json"
    with open(ausgabe_pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)

    print(f"Skript erstellt: {daten['titel']}")
    print(f"Gespeichert unter: {ausgabe_pfad}")


if __name__ == "__main__":
    main()
