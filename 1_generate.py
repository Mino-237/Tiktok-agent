"""
SCHRITT 1 von 2: Generiert nur das Skript und stoppt dann.

Läuft täglich automatisch (siehe .github/workflows/1_generate.yml).
Erstellt danach ein GitHub Issue, über das du benachrichtigt wirst
(E-Mail-Benachrichtigung, falls in deinen GitHub-Einstellungen aktiviert)
und das Skript vor der Veröffentlichung noch bearbeiten/prüfen kannst.

Video-Erstellung und TikTok-Upload passieren NICHT automatisch, sondern
erst in Schritt 2 (2_publish.py), den du manuell über den "Run workflow"
Button in GitHub Actions startest, nachdem du das Skript geprüft hast.

Das ist wichtig, damit die Inhalte nicht als reiner, unbearbeiteter
KI-Output gelten (siehe VIDEO_VORLAGE.md, Abschnitt "Checkliste") -
TikTok Creator Rewards setzen erkennbar eigene Handschrift voraus.
"""

import generate_script

if __name__ == "__main__":
    generate_script.main()
