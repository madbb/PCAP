# Mastermind -- Projektstruktur

## Dateien

```
mastermind/
    logik.py      Spiellogik -- keine GUI, kein I/O. Reine Funktionen + Spiel-Klasse.
    konsole.py    Konsolenversion. Starten mit: python konsole.py
    gui.py        GUI-Version mit tkinter.   Starten mit: python gui.py
    tests.py      Unittests fuer die Logik.  Starten mit: python tests.py -v
```

## Starten

```bash
# Tests
python test.py -v

# Konsolenversion
python konsole.py

# GUI
python gui.py
```

## Architektur

Die wichtigste Entwurfsentscheidung: logik.py hat kein print(), kein tkinter, keinen Input().
Die Spiellogik gibt Werte zurueck -- die Darstellung (Konsole oder GUI) entscheidet wie sie angezeigt werden.

```
logik.py
    erzeuge_code()          ->  List[str]
    normalisiere_eingabe()  ->  List[str]  oder ValueError
    bewerte()               ->  (int, int)   schwarz, weiss
    Spiel                   ->  Zustandsklasse

konsole.py   importiert logik.py, gibt alles mit print() aus
gui.py       importiert logik.py, zeigt alles mit tkinter Canvas an
tests.py     importiert logik.py, testet direkt
```

## GUI-Bedienung

1. In der Farbpalette unten eine Farbe anklicken
2. Wiederholen bis alle 4 Positionen belegt sind
3. "Versuch absenden" klicken
4. Bewertungspins ablesen:
   - Helle Pins = richtige Farbe, richtige Position (Schwarz)
   - Gedaempfte Pins = richtige Farbe, falsche Position (Weiss)
5. Eingabekreise anklicken um einzelne Positionen zu leeren
6. "Letzte Farbe zurueck" entfernt die zuletzt gesetzte Farbe
7. "Neues Spiel" startet eine neue Runde

## Die schwierige Stelle: Bewertungslogik

Die bewerte()-Funktion zaehlt Schwarz- und Weisstreffers korrekt ohne Doppelzaehlung.
Der Algorithmus:

1. Schwarze Treffer: alle exakten Positionen markieren als "verbraucht"
2. Weisse Treffer: fuer jede noch nicht verbrauchte Position im Versuch
   pruefen ob die Farbe noch im restlichen Code vorkommt -- wenn ja, weiss und verbraucht

Dieser Zweiphasen-Ansatz verhindert dass eine Farbe sowohl schwarz als auch weiss zaehlt.
