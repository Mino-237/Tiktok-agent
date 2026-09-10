# TikTok Video-Generator – "Warum tun wir das?"

Halbautomatisierter Video-Generator mit manuellem Freigabe-Schritt:
Claude generiert täglich ein Skript, du prüfst/bearbeitest es kurz, dann
erstellt D-ID daraus ein Avatar-Video, das zu einem fertigen TikTok-Video
zusammengesetzt wird (bewegter Hintergrund, ovaler Avatar, Wort-für-Wort
Karaoke-Untertitel, Logo). Das fertige Video lädst du manuell in der
TikTok-App hoch (dauert ca. 1 Minute).

**Warum kein automatischer TikTok-Upload?** TikTok hat den Antrag auf
automatisiertes Posten für dieses Projekt abgelehnt - die Content
Posting API ist laut TikTok nicht für "personal or company internal use"
vorgesehen (siehe PROJEKTUEBERBLICK.md, Abschnitt "Wichtige Änderung").
Die Alternative (kostenpflichtige Drittanbieter-API, ca. 30-50€/Monat)
war wirtschaftlich nicht sinnvoll. Der manuelle Upload-Schritt ist dafür
komplett kostenlos und dauert nur eine Minute pro Tag.

**Visuelles Format:** Bewegter abstrakter Partikel-Hintergrund, der
Avatar (Brandon) erscheint klein und oval unten rechts, darunter laufen
animierte Untertitel im Karaoke-Stil (Wort für Wort hervorgehoben) mit,
oben rechts optional ein Logo.

## Ablauf (zwei getrennte Schritte)

**Schritt 1 - läuft täglich automatisch:**
```
1_generate.py  →  generate_script.py  (Claude API)
              →  erstellt GitHub Issue zur Benachrichtigung
```
Speichert das Ergebnis in `pending_script.json` und stoppt dort. Du
bekommst eine Benachrichtigung (GitHub Issue, siehe unten für
E-Mail-Weiterleitung).

**Schritt 2 - startest DU manuell, nach Prüfung:**
```
2_create_video.py
  →  generate_video.py        (D-ID Talks API, Avatar Brandon)
  →  generate_background.py   (bewegter Partikel-Hintergrund, prozedural)
  →  transcribe_captions.py   (Wort-Zeitstempel via faster-whisper, lokal)
  →  create_captions.py       (Karaoke-Untertitel .ass Datei)
  →  compose_video.py         (alles zusammensetzen)
```
Gehe dafür in GitHub zu "Actions" → Workflow "2 - Video erstellen" →
"Run workflow". Dauert insgesamt ca. 5-8 Minuten. Das fertige Video
steht danach als Download bereit (siehe "Artifacts" am Ende des
Workflow-Laufs).

## Dein täglicher Ablauf (ca. 3 Minuten)

1. Benachrichtigung erhalten (GitHub Issue oder E-Mail)
2. `pending_script.json` im Repository öffnen, Text kurz lesen und bei
   Bedarf 1-2 Sätze in eigenen Worten anpassen (Stift-Symbol zum Bearbeiten)
3. Änderungen committen ("Commit changes")
4. In GitHub zu "Actions" → "2 - Video erstellen" → "Run workflow" gehen
5. Nach ca. 5-8 Minuten: Workflow-Lauf öffnen, unter "Artifacts" die
   Datei `tiktok-video-...` herunterladen
6. Video in der TikTok-App hochladen (wie ein normaler Post)

## Einmalige Einrichtung

### 0. E-Mail-Benachrichtigung für neue Issues aktivieren (empfohlen)
Damit du nicht jeden Tag manuell ins Repository schauen musst: Unter
deinen GitHub-Einstellungen → Notifications → sicherstellen, dass
"Issues" E-Mail-Benachrichtigungen aktiviert sind. Dann bekommst du bei
jedem neuen Freigabe-Issue automatisch eine E-Mail.

### 1. Anthropic API Key
- Auf https://console.anthropic.com einen API-Key erstellen

### 2. D-ID Account
- Auf https://www.d-id.com registrieren
- WICHTIG: Der kostenlose Trial-Plan reicht NICHT für die API (nur zum
  Testen in der Weboberfläche). Für die API ist mindestens der "Lite"
  Plan nötig (~$4,70/Monat) - im Dashboard unter "Plan & billing"
- Im Dashboard unter Account-Einstellungen → API keys den API-Key holen
  und SOFORT kopieren (wird nur einmal angezeigt!)
- WICHTIG: Nur "V2 Avatars" (Talks API, z.B. "Brandon") nutzen, NICHT
  "V3 Pro Avatars" (Clips API) - Pro-Avatare funktionieren auf dem
  Lite-Plan nicht zuverlässig (bleiben im Status "created" hängen)
- Avatar-Bild als PNG/JPG öffentlich hochladen (z.B. im selben
  GitHub-Pages-Repo wie die Rechtstexte) und die URL notieren

### 3. Logo vorbereiten (optional)
- Eigenes Logo als `assets/logo.png` ablegen (transparenter Hintergrund empfohlen)
- Position: oben rechts, kollidiert nicht mit Avatar/Untertiteln
- Falls keine Datei vorhanden ist, wird das Video einfach ohne Logo erstellt

### 4. GitHub Repository einrichten
1. Dieses Projekt in ein neues GitHub-Repo pushen (als **Public** Repo
   anlegen - private Repos haben ein begrenztes kostenloses
   GitHub-Actions-Zeitkontingent, öffentliche Repos sind unbegrenzt
   kostenlos)
2. Unter **Settings → Secrets and variables → Actions** folgende Secrets anlegen:
   - `ANTHROPIC_API_KEY`
   - `DID_API_KEY`, `DID_AVATAR_IMAGE_URL`

   (`GITHUB_TOKEN` für die Issue-Erstellung brauchst du NICHT manuell
   anzulegen - den stellt GitHub Actions automatisch bereit.)
3. Fertig – Workflow "1 - Skript generieren" läuft ab jetzt automatisch
   täglich, Workflow "2 - Video erstellen" startest du manuell nach Prüfung

## Lokal testen

```bash
cp .env.example .env
# .env mit echten Keys befüllen
pip install -r requirements.txt
export $(cat .env | xargs)  # lädt die .env-Variablen in die Shell
python 1_generate.py       # Schritt 1: nur Skript generieren
python 2_create_video.py   # Schritt 2: Video erstellen
```

## Video-Format anpassen

Alle visuellen Elemente lassen sich unabhängig anpassen:

- **Hintergrund-Farben/Stil:** `generate_background.py` → `FARBPALETTE`
  und `HINTERGRUND_FARBE`
- **Avatar-Größe/Position:** `compose_video.py` → `AVATAR_GROESSE`,
  `AVATAR_ABSTAND_RECHTS`, `AVATAR_ABSTAND_UNTEN`
- **Untertitel-Stil (Farbe, Schriftgröße, Position):** `create_captions.py`
  → `ASS_HEADER` (Format ist Advanced SubStation Alpha - "PrimaryColour"
  = noch nicht gesprochenes Wort, "SecondaryColour" = aktuell gesprochenes
  Wort, Farben im Format `&HAABBGGRR`, also umgekehrte Reihenfolge zu RGB)
- **Wörter pro Untertitel-Zeile:** `create_captions.py` → `zeilen_gruppieren()`

**Bekannte Einschränkung:** Der ovale Avatar-Ausschnitt nutzt `colorkey`,
um den weißen Hintergrund von Brandons Foto zu entfernen. Bei sehr hellen
Lichtreflexen im Gesicht (z.B. starke Stirn-Highlights) können vereinzelt
minimale Artefakte auftreten - in unseren Tests war das mit den aktuellen
Einstellungen (`colorkey=0xFFFFFF:0.08:0.0`) kaum noch sichtbar. Bei Bedarf
in `compose_video.py` leicht nachjustieren.

## Zeitplan ändern

In `.github/workflows/1_generate.yml` die `cron`-Zeile anpassen.
Format: `Minute Stunde Tag Monat Wochentag` (immer UTC).
Hilfreich: https://crontab.guru

## Themen anpassen

Der Kanal generiert seine Themen **komplett automatisch** - du musst
nichts manuell nachpflegen:

- Startet mit 20 Themen in `generate_script.py` (`THEMEN_POOL_START`)
- Sobald weniger als 8 unbenutzte Themen übrig sind, lässt der Code
  Claude automatisch 20 neue, passende Themen generieren und speichert
  sie dauerhaft in `themen_pool.json`
- `themen_historie.json` verhindert Wiederholungen, bis der gesamte
  (wachsende) Pool einmal durch ist
- Der GitHub-Actions-Workflow committed beide Dateien nach jedem Lauf
  automatisch zurück ins Repository

**Nische ändern:** Passe `KANAL_NISCHE` in `generate_script.py` an (z.B.
auf "Finanztipps" oder "Geschichte" statt Psychologie) - neu generierte
Themen orientieren sich daran. Für einen kompletten Themenwechsel kannst
du zusätzlich `themen_pool.json` und `themen_historie.json` im Repo
löschen, dann startet der Kanal mit frischem Pool und `SYSTEM_PROMPT`
sollte ebenfalls angepasst werden (Skript-Struktur/Format).

**Qualitätskontrolle:** Es lohnt sich, alle paar Monate stichprobenartig
ein paar automatisch generierte Themen in `themen_pool.json` zu
überfliegen, um sicherzugehen, dass die Qualität passt - notwendig ist
das aber nicht für den laufenden Betrieb.

## Rechtlicher Hinweis

Keine Rechts- oder Finanzberatung. TikToks Monetarisierungs-Richtlinien
(Follower-/View-Schwellen, Originalitäts-Kriterien) können sich ändern –
vor dem produktiven Einsatz die aktuellen Bedingungen auf dem TikTok
Creator Portal prüfen.
