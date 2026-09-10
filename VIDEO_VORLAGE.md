# Video-Vorlage: "Warum tun wir das?"

Kanal-Format für Alltagspsychologie-Videos, KI-generiert mit D-ID (Avatar "Frank").

---

## Skript-Struktur (immer gleich, 130-170 Wörter, ~60-75 Sekunden)

| Teil | Zweck | Länge |
|---|---|---|
| **1. Hook** | Provokante Frage direkt an den Zuschauer | 1 Satz |
| **2. Phänomen** | Das psychologische Phänomen benennen | 1-2 Sätze |
| **3. Erklärung** | Warum passiert das im Gehirn/Verhalten - einfache Sprache | 2-3 Sätze |
| **4. Beispiel** | Konkretes Alltagsbeispiel | 2-3 Sätze |
| **5. CTA** | Einladung zum Kommentieren | 1 Satz |

---

## Beispiel-Skript (Muster)

> **Hook:** "Warum lügst du dir selbst öfter an als anderen?"
>
> **Phänomen:** Das nennt man Selbsttäuschung - wir glauben unsere eigenen Ausreden oft williger als die von anderen.
>
> **Erklärung:** Unser Gehirn will Widersprüche zwischen dem, was wir tun, und dem, was wir über uns denken, vermeiden. Also biegen wir uns die Wahrheit passend zurecht, ohne es zu merken.
>
> **Beispiel:** Du sagst "Ich hab einfach keine Zeit fürs Fitnessstudio" - obwohl du täglich eine Stunde scrollst. Nicht gelogen, aber auch nicht ganz ehrlich.
>
> **CTA:** Erwischst du dich manchmal dabei? Schreib's in die Kommentare.

---

## Visuelle Vorgaben (Konsistenz = Wiedererkennungswert)

- **Hintergrund:** Bewegter, abstrakter Partikel-Hintergrund (prozedural erzeugt, dunkelblau/violett)
- **Avatar:** Brandon (V2 Standard-Avatar), oval, klein, unten rechts positioniert
- **Untertitel:** Wort-für-Wort Karaoke-Stil (weiß → gelb beim Sprechen), unten mittig
- **Logo-Overlay:** Oben rechts, gleichbleibendes Branding
- **Format:** Hochformat 1080x1920 (TikTok-Standard)

---

## Themenpool (erweiterbar in `generate_script.py`)

- Warum du dir selbst öfter etwas vormachst als anderen (Selbsttäuschung)
- Warum wir Dinge aufschieben, obwohl wir wissen, dass es uns schadet (Prokrastination)
- Warum eine einzige schlechte Erinnerung zehn gute überstrahlt (Negativity Bias)
- Warum wir Fremden vertrauen, nur weil sie selbstbewusst wirken (Halo-Effekt)
- Warum Entscheidungen leichter fallen, wenn es weniger Optionen gibt (Choice Overload)
- Warum wir eigene Fehler bei anderen sofort erkennen (Blinder Fleck)
- Warum Gruppenzwang stärker wirkt, als wir zugeben wollen (Konformität)
- Warum wir uns an Anfang und Ende eines Erlebnisses am meisten erinnern (Peak-End-Regel)

---

## Checkliste vor jedem Post (im täglichen Review-Schritt, ca. 2 Min.)

Der Code stoppt automatisch nach der Skript-Generierung und wartet auf
deine Freigabe (siehe README.md, Abschnitt "Dein täglicher Ablauf").
Bevor du Workflow "2 - Video erstellen" startest, kurz prüfen:

- [ ] Skript folgt der 5-Teile-Struktur
- [ ] Unter 170 Wörtern (sonst zu lang für 60-75 Sek.)
- [ ] **Mindestens 1-2 Sätze in eigenen Worten angepasst** - das ist der
      wichtigste Punkt, damit der Content nicht als reiner
      KI-Output/Recycling gilt (siehe "Warum das als originell zählt" oben)
- [ ] Video mindestens 60 Sekunden lang (Voraussetzung für TikTok Creator Rewards)
- [ ] Logo-Overlay sichtbar
- [ ] Kein Thema, das kürzlich schon behandelt wurde (wird automatisch
      durch `themen_historie.json` verhindert, trotzdem gegenlesen)
