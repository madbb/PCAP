# MP3-Verwaltung -- Projektstruktur

## Installation

```bash
pip install mutagen
```

## Dateien

```
mp3_verwaltung/
    modell.py      Song + Bibliothek -- Datenmodell, kein I/O, kein GUI
    scanner.py     Liest MP3-Dateien vom Dateisystem mit mutagen
    gui.py         tkinter-Oberflaeche -- starten mit: python gui.py
    test_mp3.py    pytest-Tests -- starten mit: pytest test_mp3.py -v
    bibliothek.json  wird automatisch beim Speichern angelegt
```

## Starten

```bash
# Tests
pytest test_mp3.py -v

# GUI
python gui.py
```

## GUI-Bedienung

| Aktion | Beschreibung |
|---|---|
| Verzeichnis scannen | Oeffnet Ordnerauswahl, liest alle MP3s rekursiv |
| Bibliothek laden | Laedt eine gespeicherte JSON-Datei |
| Bibliothek speichern | Speichert den aktuellen Stand als JSON |
| Statistiken | Songs, Dauer, Interpreten, Alben, Duplikate |
| Als CSV exportieren | Fuer Excel oder LibreOffice |
| Fehlende entfernen | Entfernt Eintraege fuer geloeschte/verschobene Dateien |
| Suchfeld | Echtzeit-Suche in Titel, Interpret, Album, Dateiname |
| Spaltenheader klicken | Sortiert nach dieser Spalte (2. Klick: Richtung umkehren) |
| Doppelklick auf Song | Zeigt alle Details inkl. Dateipfad |

## Architektur

```
modell.py        -- reine Datenlogik, kein I/O, kein GUI
    Song         -- eine Datei mit ihren Metadaten (@dataclass)
    Bibliothek   -- Sammlung mit Suche, Sortierung, Persistenz

scanner.py       -- einzige Stelle die mutagen kennt
    lese_song()           -- eine Datei -> Song
    scanne_verzeichnis()  -- Ordner rekursiv -> [Song], [Fehler]
    erstelle_testdateien() -- Testdaten ohne echte Musik

gui.py           -- tkinter, importiert nur modell + scanner
    ScanDialog        -- Fortschrittsfenster (laeuft in Thread)
    StatistikFenster  -- Statistik-Popup
    MP3App            -- Hauptfenster mit Treeview
```

## Testdaten ohne eigene MP3s

```python
from scanner import erstelle_testdateien
erstelle_testdateien("./testmusik", anzahl=12)
```

Erstellt 12 minimale MP3-Dateien mit verschiedenen Tags (inkl. absichtlich
fehlenden Tags fuer Fallback-Tests) im Ordner `./testmusik`.
