# Webbasierte Systeme - Gruppe 11

Entwicklung einer Flask-Anwendung mit Datenbankanbindung

## Projektstruktur

Der Projektordner enthält standardmäßig folgende Dateien und Verzeichnisse:

* **db**:
  * **db_credentials.py**: enthält Verbindungsinformationen zur Datenbank
  * **db_schema.sql**: enthält SQL-Befehle zur Erzeugung der Datenbank
* **static**:
  * enthält alle statischen Dateien wie CSS-Dateien und Bilder
* **templates**:
  * enthält alle HTML-Templates
* **.gitignore**: enthält alle Dateien und Verzeichnisse, die nicht in die Versionskontrolle mit Git aufgenommen werden sollen
* **LICENSE**: enthält Lizenzbedingungen für das gesamte Projekt
* **README.md**: Diese Datei, enthält die Projektdokumentation im Markdown-Format
* **ss-2024-11.py**: enthält die eigentliche Flask-Anwendung

## Projektanforderungen

### Mindestanforderungen

* [x] Nutzer-Registration und Login
* [x] Admin-Bereich mit Daten- und Nutzerverwaltung
* [x] Einfügen, Ändern und Löschen von Daten: Jeder Nutzer sollte nur seine eigenen Daten, Admin alle Daten bearbeiten können (Name, E-Mail,Passwort, Nutzername)
* [x] Beiträge erstellen (Ort bewerten, kommentieren und eigene Bilder einfügen können) -> diese sind unter der jeweiligen Stadt aufgelistet
* [x] Nutzer können bereits erstellte Beiträge bewerten (Like), kommentieren, melden und speichern)
* [x] Städteliste (Bewertung mit 5 Sterne)
* [x] Speichern von Reisezielen (Merkliste im Nutzerbereich)
* [x] Menüleiste mit Länderliste, Städteliste, beliebteste Orte, Profil/Merkliste


### Optionale Anforderungen

* [ ] Sharing Funktion (Beiträge, Orte teilen können)
* [ ] Empfelungen für Hotels, Events, Sehenswürdigkeiten (optionale Bewertungskriterien bei Beitragserstellung)
* [ ] Filter (Kosten, Land, Lage)
* [ ] Städtebewertung mit verschiedenen Kriterien (Kosten, Lage, Essen, gesamt,...)
* [ ] wird ein gespeicherte Beitrag geändert, bekommt der Nutzer eine Benachrichtigung
* [x] Weltkarte (Nadeln führen zur Seite der Länder mit Ortsliste)
