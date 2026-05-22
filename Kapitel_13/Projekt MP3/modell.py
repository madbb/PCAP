# =============================================================================
# mp3_verwaltung/modell.py
#
# Datenmodell fuer die MP3-Verwaltung.
# Enthaelt: Song (einzelne Datei), Bibliothek (Sammlung von Songs).
#
# Kein I/O, kein tkinter, kein print() -- nur Datenstrukturen und Logik.
# Das macht alle Klassen hier direkt testbar und unabhaengig von der Darstellung.
# =============================================================================

from __future__ import annotations   # erlaubt Typhinweise die auf die eigene Klasse zeigen

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


# =============================================================================
# 1. Song -- repraesentiert eine einzelne MP3-Datei
# =============================================================================

@dataclass
class Song:
    """
    Repraesentiert eine einzelne MP3-Datei mit ihren Metadaten.

    Alle Felder ausser 'pfad' koennen fehlen -- nicht jede MP3-Datei hat
    vollstaendige ID3-Tags. Fehlende Werte werden als None oder 0 gespeichert,
    nie als leerer String, damit Pruefungen wie `if song.titel` zuverlaessig
    funktionieren.

    @dataclass erledigt __init__, __repr__ und __eq__ automatisch -- wir
    muessen sie nicht selbst schreiben.
    """

    # Pflichtfeld: der absolute Pfad zur Datei (als String fuer JSON-Kompatibilitaet)
    pfad: str

    # Optionale Metadaten -- koennen fehlen wenn die Datei keine ID3-Tags hat
    titel:    Optional[str]   = None
    interpret: Optional[str]  = None
    album:    Optional[str]   = None
    jahr:     Optional[str]   = None   # als String weil ID3 manchmal '2024' oder '2024-01-01' liefert
    dauer:    float           = 0.0    # Laenge in Sekunden

    # ------------------------------------------------------------------
    # Darstellungshilfen
    # ------------------------------------------------------------------

    @property
    def titel_anzeige(self) -> str:
        """Titel fuer die Anzeige -- faellt auf Dateiname zurueck wenn kein Tag."""
        return self.titel or Path(self.pfad).stem

    @property
    def interpret_anzeige(self) -> str:
        """Interpret fuer die Anzeige -- 'Unbekannt' wenn kein Tag."""
        return self.interpret or "Unbekannt"

    @property
    def album_anzeige(self) -> str:
        return self.album or "Unbekannt"

    @property
    def jahr_anzeige(self) -> str:
        return self.jahr or "–"

    @property
    def dauer_anzeige(self) -> str:
        """Dauer als 'mm:ss'-String. 0 Sekunden wird als '–' angezeigt."""
        if not self.dauer:
            return "–"
        minuten  = int(self.dauer) // 60
        sekunden = int(self.dauer) % 60
        return f"{minuten}:{sekunden:02d}"

    @property
    def dateiname(self) -> str:
        """Nur der Dateiname ohne Verzeichnis."""
        return Path(self.pfad).name

    # ------------------------------------------------------------------
    # Serialisierung: Song <-> Dictionary (fuer JSON-Speicherung)
    # ------------------------------------------------------------------

    def als_dict(self) -> dict:
        """
        Wandelt den Song in ein einfaches Dictionary um.
        Dieses Dictionary kann direkt mit json.dump() gespeichert werden.
        """
        return asdict(self)   # @dataclass liefert das kostenlos ueber asdict()

    @classmethod
    def aus_dict(cls, daten: dict) -> Song:
        """
        Erstellt einen Song aus einem Dictionary (z.B. aus einer JSON-Datei).
        Unbekannte Schluessel im Dictionary werden ignoriert -- das schuetzt
        vor Fehlern wenn das Dateiformat sich aendert.
        """
        bekannte_felder = {f for f in cls.__dataclass_fields__}
        gefiltert = {k: v for k, v in daten.items() if k in bekannte_felder}
        return cls(**gefiltert)

    # ------------------------------------------------------------------
    # Suche
    # ------------------------------------------------------------------

    def enthaelt(self, suchbegriff: str) -> bool:
        """
        Gibt True zurueck wenn der Suchbegriff (Teilstring, case-insensitive)
        in Titel, Interpret, Album oder Dateiname vorkommt.
        """
        begrif = suchbegriff.lower()
        felder = [
            self.titel_anzeige,
            self.interpret_anzeige,
            self.album_anzeige,
            self.dateiname,
        ]
        return any(begrif in f.lower() for f in felder)

    # ------------------------------------------------------------------
    # Existenzpruefung
    # ------------------------------------------------------------------

    def existiert(self) -> bool:
        """True wenn die Datei auf dem Dateisystem noch vorhanden ist."""
        return Path(self.pfad).is_file()

    def __str__(self) -> str:
        return f"{self.interpret_anzeige} – {self.titel_anzeige} ({self.dauer_anzeige})"


# =============================================================================
# 2. Bibliothek -- Sammlung von Songs mit Such- und Sortierfunktionen
# =============================================================================

class Bibliothek:
    """
    Haelt eine Sammlung von Song-Objekten.

    Verantwortlich fuer:
    - Suchen und Filtern
    - Sortieren
    - Statistiken
    - Serialisierung (speichern / laden als JSON)
    - Verwalten von Duplikaten und veralteten Eintraegen

    Die Bibliothek speichert Songs intern als Liste. Fuer alle Abfragen
    wird die Liste durchlaufen -- das reicht fuer Sammlungen bis ca. 50.000
    Songs ohne spuerbare Verzoegerung.
    """

    SORTIERFELDER = ["titel", "interpret", "album", "jahr", "dauer"]

    def __init__(self):
        self._songs: list[Song] = []

    # ------------------------------------------------------------------
    # Songs hinzufuegen und entfernen
    # ------------------------------------------------------------------

    def hinzufuegen(self, song: Song) -> None:
        """Fuegt einen Song zur Bibliothek hinzu."""
        self._songs.append(song)

    def alle_hinzufuegen(self, songs: list[Song]) -> None:
        """Fuegt eine Liste von Songs hinzu."""
        self._songs.extend(songs)

    def leeren(self) -> None:
        """Entfernt alle Songs aus der Bibliothek."""
        self._songs.clear()

    def entferne_fehlende(self) -> list[Song]:
        """
        Entfernt alle Songs deren Dateien nicht mehr existieren.
        Gibt die Liste der entfernten Songs zurueck.

        Nuetzlich beim Programmstart: wenn der Nutzer Dateien verschoben
        oder geloescht hat seit dem letzten Speichern.
        """
        fehlende = [s for s in self._songs if not s.existiert()]
        self._songs = [s for s in self._songs if s.existiert()]
        return fehlende

    # ------------------------------------------------------------------
    # Abfragen
    # ------------------------------------------------------------------

    @property
    def anzahl(self) -> int:
        """Anzahl Songs in der Bibliothek."""
        return len(self._songs)

    def alle(self) -> list[Song]:
        """Gibt alle Songs zurueck (Kopie der Liste)."""
        return list(self._songs)

    def suchen(self, suchbegriff: str) -> list[Song]:
        """
        Gibt alle Songs zurueck die den Suchbegriff enthalten.
        Sucht in Titel, Interpret, Album und Dateiname.
        Case-insensitive, Teilstrings werden gefunden.
        """
        if not suchbegriff.strip():
            return self.alle()
        return [s for s in self._songs if s.enthaelt(suchbegriff)]

    def filtern_nach_interpret(self, interpret: str) -> list[Song]:
        """Gibt alle Songs eines bestimmten Interpreten zurueck."""
        return [s for s in self._songs
                if s.interpret and interpret.lower() in s.interpret.lower()]

    def filtern_nach_album(self, album: str) -> list[Song]:
        """Gibt alle Songs eines bestimmten Albums zurueck."""
        return [s for s in self._songs
                if s.album and album.lower() in s.album.lower()]

    def sortieren(self, nach: str = "interpret", absteigend: bool = False) -> list[Song]:
        """
        Gibt die Songs sortiert nach einem Feld zurueck.

        nach       -- eines von: titel, interpret, album, jahr, dauer
        absteigend -- True fuer absteigende Sortierung

        Songs mit fehlendem Sortierfeld werden ans Ende einsortiert.
        """
        if nach not in self.SORTIERFELDER:
            raise ValueError(f"Unbekanntes Sortierfeld: '{nach}'. "
                             f"Moeglich: {self.SORTIERFELDER}")

        def sort_key(song: Song):
            wert = getattr(song, nach)
            # None-Werte ans Ende: bei aufsteigend "" < alles, bei absteigend "zzz" > alles
            if wert is None:
                return "zzz" if not absteigend else ""
            # Strings kleinschreiben fuer case-insensitive Sortierung
            return str(wert).lower()

        return sorted(self._songs, key=sort_key, reverse=absteigend)

    def duplikate(self) -> list[list[Song]]:
        """
        Findet Songs mit identischem Titel UND Interpret (case-insensitive).
        Gibt eine Liste von Gruppen zurueck -- jede Gruppe enthaelt die
        Duplikate zueinander.

        Songs ohne Titel oder Interpret werden nicht als Duplikate erkannt.
        """
        gruppen: dict[str, list[Song]] = {}

        for song in self._songs:
            if not song.titel or not song.interpret:
                continue
            # Schluessel: normalisierter "Interpret|Titel"
            schluessel = f"{song.interpret.lower()}|{song.titel.lower()}"
            gruppen.setdefault(schluessel, []).append(song)

        # Nur Gruppen mit mehr als einem Song zurueckgeben
        return [gruppe for gruppe in gruppen.values() if len(gruppe) > 1]

    # ------------------------------------------------------------------
    # Statistiken
    # ------------------------------------------------------------------

    def statistiken(self) -> dict:
        """
        Berechnet Statistiken ueber die Bibliothek.
        Gibt ein Dictionary zurueck mit:
            anzahl_songs    -- Gesamtzahl
            gesamtdauer_sek -- Gesamtdauer in Sekunden
            gesamtdauer_str -- Gesamtdauer als 'Xh Ym'
            interpreten     -- Anzahl eindeutiger Interpreten
            alben           -- Anzahl eindeutiger Alben
            ohne_metadaten  -- Songs ohne Titel oder Interpret
        """
        gesamtdauer = sum(s.dauer for s in self._songs)
        stunden     = int(gesamtdauer) // 3600
        minuten     = (int(gesamtdauer) % 3600) // 60

        interpreten = {s.interpret for s in self._songs if s.interpret}
        alben       = {s.album for s in self._songs if s.album}
        ohne_meta   = [s for s in self._songs if not s.titel or not s.interpret]

        return {
            "anzahl_songs":    self.anzahl,
            "gesamtdauer_sek": gesamtdauer,
            "gesamtdauer_str": f"{stunden}h {minuten}min",
            "interpreten":     len(interpreten),
            "alben":           len(alben),
            "ohne_metadaten":  len(ohne_meta),
        }

    def alle_interpreten(self) -> list[str]:
        """Gibt alle vorhandenen Interpreten alphabetisch sortiert zurueck."""
        return sorted({s.interpret for s in self._songs if s.interpret},
                      key=str.lower)

    def alle_alben(self) -> list[str]:
        """Gibt alle vorhandenen Alben alphabetisch sortiert zurueck."""
        return sorted({s.album for s in self._songs if s.album},
                      key=str.lower)

    # ------------------------------------------------------------------
    # Persistenz: speichern und laden als JSON
    # ------------------------------------------------------------------

    def speichern(self, pfad: str | Path) -> None:
        """
        Speichert die Bibliothek als JSON-Datei.

        Jeder Song wird als Dictionary gespeichert. Das JSON bleibt
        menschenlesbar durch indent=2.

        Wirft OSError wenn die Datei nicht geschrieben werden kann.
        """
        pfad = Path(pfad)
        daten = [song.als_dict() for song in self._songs]

        with open(pfad, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, indent=2)

    def laden(self, pfad: str | Path) -> int:
        """
        Laedt eine zuvor gespeicherte Bibliothek aus einer JSON-Datei.
        Ersetzt den aktuellen Inhalt der Bibliothek vollstaendig.

        Gibt die Anzahl geladener Songs zurueck.
        Wirft FileNotFoundError wenn die Datei nicht existiert.
        Wirft json.JSONDecodeError wenn die Datei kein gueltiges JSON enthaelt.
        """
        pfad = Path(pfad)

        with open(pfad, "r", encoding="utf-8") as f:
            daten = json.load(f)

        self._songs = [Song.aus_dict(d) for d in daten]
        return len(self._songs)

    def exportieren_csv(self, pfad: str | Path) -> None:
        """
        Exportiert die Bibliothek als CSV-Datei.
        Kann in Excel oder LibreOffice Calc geoeffnet werden.
        """
        import csv
        pfad = Path(pfad)

        spalten = ["titel", "interpret", "album", "jahr", "dauer_anzeige", "pfad"]

        with open(pfad, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(spalten)   # Kopfzeile
            for song in self._songs:
                writer.writerow([
                    song.titel_anzeige,
                    song.interpret_anzeige,
                    song.album_anzeige,
                    song.jahr_anzeige,
                    song.dauer_anzeige,
                    song.pfad,
                ])
