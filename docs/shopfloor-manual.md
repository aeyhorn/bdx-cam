# Kurzanleitung Shopfloor-Tester (Frontend)

Dieses Manual beschreibt den Standardablauf fuer Shopfloor-Mitarbeiter im `BDXPostOffice` Frontend.

Begriffe:
- `Standardfall`: singulaere Betrachtung eines einzelnen Maschinen-/Prozessproblems.
- `Programmierfall`: Fall aus der Teileprogrammierung (inkl. NC/STEP/Dateianhaengen), der mit Standardfaellen verknuepft werden kann.

## 1. Anmelden

1. Frontend im Browser oeffnen (z. B. `http://<server>:8080`).
2. Mit deinem Benutzer anmelden.
3. Im linken Menue zu `Problem melden` wechseln.

## 2. Neuen Standardfall erfassen (wichtigster Ablauf)

Auf der Seite `Problem melden`:

1. **Maschine und Programmumgebung** auswaehlen.
2. **NC-Programmname** eintragen.
3. **Dringlichkeit** auswaehlen.
4. **Kurzbeschreibung** des Problems eintragen.
5. Optional: `Weitere Angaben` aufklappen und Zusatzinfos erfassen (Projekt, Satznummer, erwartetes/tatsaechliches Verhalten usw.).
6. Standardfall speichern.

Hinweis: Titel kann leer bleiben; das System verwendet dann den Programmnamen.

## 3. Eigene Standardfaelle nachverfolgen

1. Im Menue `Meine Standardfaelle` oeffnen.
2. Standardfall in der Liste suchen.
3. Status pruefen (z. B. Neu, In Bearbeitung, Geloest).
4. Bei Rueckfragen Kommentare oder Zusatzinfos nachreichen (falls freigeschaltet).

## 4. Dateien am Standardfall nutzen

In der Standardfall-Detailansicht koennen je nach Berechtigung Anhaenge genutzt werden:

- NC-/Textdateien hochladen
- Zuordnung zu Projekt/Typ setzen
- Textdateien direkt anzeigen/bearbeiten
- Dateien herunterladen oder loeschen

Wenn ein Download mit Auth-Fehler scheitert, Seite neu laden und erneut anmelden.

## 5. Programmierfaelle (nur Engineering/Admin)

Falls du als Tester zusaetzliche Rechte hast:

1. `Programmierfaelle` oeffnen.
2. Eintrag doppelklicken -> `Programmierfall-Container`.
3. NC/STEP-Dateien hochladen, anzeigen, herunterladen oder loeschen.

## 6. Gute Praxis fuer Shopfloor-Meldungen

- Pro Problem einen eigenen Standardfall anlegen.
- NC-Programmname exakt wie an der Maschine verwenden.
- Kurz und konkret schreiben: *Was wurde erwartet? Was ist passiert?*
- Wenn moeglich Satznummer, Screenshot oder NC-Ausschnitt ergaenzen.

## 7. Schnelle Fehlerhilfe

- **Keine Daten sichtbar** -> Browser mit `Ctrl+F5` neu laden.
- **Nicht angemeldet / Not authenticated** -> neu einloggen.
- **Speichern nicht sichtbar** -> Standardfall erneut oeffnen und Status/Kommentar pruefen.

