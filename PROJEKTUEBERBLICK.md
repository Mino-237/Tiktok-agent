# Projektüberblick: TikTok Video-Generator "Warum tun wir das?"

Stand: September 2026

---

## ⚠️ Wichtige Änderung: Kein automatischer TikTok-Upload mehr

Der ursprüngliche Plan war ein komplett automatisiertes Posten via
TikTok Content Posting API. **TikTok hat den Audit-Antrag abgelehnt**
mit der Begründung: die API ist nicht für "personal or company internal
use" vorgesehen - ein einzelner Creator, der auf sein eigenes Konto
postet, fällt laut TikTok in diese abgelehnte Kategorie.

**Geprüfte Alternativen:**
- Drittanbieter-API (z.B. Upload-Post): technisch möglich, aber der
  API-Zugang kostet dort ca. 30-50€/Monat - bei den erwarteten
  Anfangs-Einnahmen aus TikTok Creator Rewards (siehe Abschnitt 8)
  wirtschaftlich nicht sinnvoll
- TikTok Business-Account + erneuter Audit-Versuch: kostenlos, aber
  nicht garantiert erfolgreich

**Entscheidung:** Das Projekt läuft jetzt mit einem **manuellen letzten
Schritt** - der Code erstellt weiterhin automatisch Skript und fertiges
Video, du lädst das fertige Video dann selbst in der TikTok-App hoch
(ca. 1 Minute Aufwand pro Tag). Das ist komplett kostenlos und
zuverlässig, kein Audit nötig.

**Vorteil dieser Änderung:** Das Projekt ist dadurch auch technisch
deutlich einfacher und robuster geworden - kein OAuth-Token-Management,
kein Sandbox/Production-Unterschied, keine TikTok-Developer-App mehr
nötig.

---

## 1. Was das Projekt macht

**Täglich automatisch (Workflow "1 - Skript generieren"):**
1. Ein neues Alltagspsychologie-Thema + Skript wird generiert (Claude API)
2. Ein GitHub Issue benachrichtigt dich zur Prüfung

**Danach von dir manuell gestartet (Workflow "2 - Video erstellen"),
nach kurzer Prüfung/Bearbeitung des Skripts:**
3. Ein Avatar-Video wird erstellt (D-ID, Avatar "Brandon")
4. Ein bewegter Partikel-Hintergrund wird generiert
5. Das Video wird transkribiert (Wort-Zeitstempel)
6. Karaoke-Untertitel werden erstellt
7. Alles wird zu einem fertigen Video zusammengesetzt (Hintergrund +
   ovaler Avatar unten rechts + Untertitel + Logo)
8. Das fertige Video steht als Download bereit (GitHub Actions Artifact)

**Der letzte Schritt (Video in TikTok hochladen) machst du manuell.**

---

## 2. Aktueller Status

| Baustein | Status |
|---|---|
| Rechtstexte (Terms/Privacy) live | ✅ Erledigt (bleibt als Referenz bestehen, auch ohne TikTok-Audit) |
| D-ID Account + funktionierender Avatar | ✅ Erledigt (Lite-Plan, Avatar "Brandon") |
| Visuelles Format (Hintergrund, Avatar-Ausschnitt, Karaoke-Untertitel) | ✅ Erledigt, getestet |
| Automatische Themen-Generierung | ✅ Erledigt (kein manueller Nachschub nötig) |
| Kompletter Code fertig | ✅ Erledigt (siehe Abschnitt 5) |
| TikTok Content Posting API Audit | ❌ Abgelehnt (personal use nicht erlaubt) |
| `tiktok-agent` GitHub-Repo mit Secrets | ⏳ **Noch zu tun** |
| Live-Betrieb gestartet | ⏳ Noch zu tun |

---

## 3. Genutzte Accounts & Kosten

| Dienst | Zweck | Kosten | Login/Zugang |
|---|---|---|---|
| **Anthropic API** (console.anthropic.com) | Skript-Generierung | Nutzungsbasiert, ca. Cent-Beträge/Monat | Separat vom Claude.ai-Abo! |
| **D-ID** (d-id.com) | Avatar-Video-Erstellung | Lite-Plan, $4,70/Monat | E-Mail: aminahme34@gmail.com |
| **TikTok-Konto** (mino_pale) | Wo die Videos gepostet werden (manuell) | Kostenlos | Normaler TikTok-Login |
| **GitHub** | Code-Hosting + täglicher Cronjob | Kostenlos (bei Public Repo) | github.com, User: Mino-237 |

**Gesamtkosten: ca. $4,70-5/Monat** (nur D-ID, da kein TikTok-API-Zugang
mehr gebraucht wird).

**Wichtig:** Claude Pro/Claude.ai-Abo wird für den Agent **nicht**
gebraucht - nur der separate API-Key.

---

## 4. GitHub-Repositories

### `meine-tiktok-app-legal` (bereits live)
- Zweck: Avatar-Bild (Brandon-avatar.png) - wird bei jedem Video-Lauf
  vom Code abgerufen. Die Rechtstexte (Terms/Privacy) selbst werden
  nicht mehr aktiv gebraucht (kein TikTok-Audit mehr nötig), können
  aber bestehen bleiben.
- **Muss dauerhaft bestehen bleiben** wegen des Avatar-Bildes
- Live unter: `https://mino-237.github.io/meine-tiktok-app-legal/`

### `tiktok-agent` (noch anzulegen)
- Zweck: Der Video-Generierungs-Code + täglicher Cronjob
- Wird aus dem zuletzt gelieferten ZIP erstellt
- **Als "Public" Repository anlegen** (private Repos haben begrenztes
  kostenloses GitHub-Actions-Zeitkontingent)

---

## 5. Code-Struktur (im ZIP)

**Schritt 1 (täglich automatisch):**
```
1_generate.py  →  generate_script.py  (Claude API, Themen-Auto-Nachschub)
              →  GitHub Issue zur Benachrichtigung
```

**Schritt 2 (manuell, nach Prüfung):**
```
2_create_video.py
  →  generate_video.py        (D-ID Talks API, Avatar Brandon)
  →  generate_background.py   (bewegter Partikel-Hintergrund, prozedural)
  →  transcribe_captions.py   (Wort-Zeitstempel via faster-whisper, lokal)
  →  create_captions.py       (Karaoke-Untertitel .ass Datei)
  →  compose_video.py         (alles zusammensetzen)
```

- **`.github/workflows/1_generate.yml`** - täglicher Cronjob (15:00 UTC), nur Skript-Generierung
- **`.github/workflows/2_create_video.yml`** - nur manuell startbar ("Run workflow"-Button), erstellt Video als Download-Artifact
- **`themen_pool.json`** / **`themen_historie.json`** - wachsen automatisch, verhindern Wiederholungen
- **`VIDEO_VORLAGE.md`** - Referenz für das Skript-Format
- **`README.md`** - komplette technische Setup-Anleitung

---

## 6. Was noch zu tun ist

1. **`tiktok-agent` als GitHub-Repository anlegen** (als Public Repo, Code aus dem ZIP hochladen)
2. **Secrets in GitHub eintragen** (Settings → Secrets and variables → Actions):
   - `ANTHROPIC_API_KEY`
   - `DID_API_KEY`, `DID_AVATAR_IMAGE_URL`
3. **E-Mail-Benachrichtigung für Issues aktivieren** (GitHub-Einstellungen → Notifications)
4. Fertig - Workflow 1 läuft automatisch täglich, du bestätigst/bearbeitest
   das Skript, startest Workflow 2 manuell, lädst das Video herunter und
   postest es in der TikTok-App

---

## 7. Wichtige Lektionen von diesem Projekt

- **HeyGen und D-ID Trial-Pläne unterstützen nur die Weboberfläche, nicht die API** - für Automatisierung ist immer ein bezahlter Plan nötig
- **D-ID "V3 Pro Avatare" (Clips API) funktionieren nicht auf dem Lite-Plan** - nur "V2 Avatare" (Talks API) sind Lite-kompatibel
- **TikToks Content Posting API lehnt "personal/internal use" grundsätzlich ab** - Einzelpersonen, die für ihr eigenes Konto automatisieren wollen, sind offenbar nicht die Zielgruppe dieser API, unabhängig von Sandbox-Tests, die vorher erfolgreich liefen
- **ffmpeg's `geq`-Filter mit `alpha(X,Y)`-Referenz ist unzuverlässig** - für Alpha-Masken-Kombinationen zuverlässiger: `alphaextract` + `blend=all_mode=multiply` + `alphamerge`
- **`colorkey`-Similarity zu hoch eingestellt entfernt auch helle Hautreflexe** - konservative Werte (z.B. `0.08:0.0`) sind für echte Gesichter sicherer

---

## 8. Monetarisierung (zur Erinnerung)

TikTok Creator Rewards Program Voraussetzungen:
- 10.000 Follower
- 100.000 Views in 30 Tagen
- 18+ Jahre, Account aus berechtigtem Land (Deutschland zählt dazu)
- Videos mindestens 60 Sekunden lang

Realistische Erwartung: Eher kleiner Nebenverdienst am Anfang, kein Ersatzeinkommen. Wichtig: Content muss originell wirken (eigene Formulierung, konsistentes Format, kein reiner KI-Rohtext) - siehe `VIDEO_VORLAGE.md` für die Struktur, die genau darauf ausgelegt ist. Der manuelle Video-Upload (statt Vollautomatik) unterstützt das zusätzlich, da du das Video vor dem Posten noch einmal siehst.
