# =============================================================================
# mp3_verwaltung/test_mp3.py
#
# Tests fuer modell.py und scanner.py
# Ausfuehren mit: pytest test_mp3.py -v
#
# Der Scanner-Test erstellt echte Testdateien im tmp-Verzeichnis --
# das erlaubt echte Ende-zu-Ende-Tests ohne eine echte MP3-Sammlung.
# =============================================================================

import json
import tempfile
from pathlib import Path

import pytest

from modell import Song, Bibliothek


# =============================================================================
# Fixtures -- werden vor jedem Test frisch erstellt
# =============================================================================

@pytest.fixture
def song_vollstaendig():
    """Song mit allen Metadaten."""
    return Song(
        pfad="/musik/queen/bohemian.mp3",
        titel="Bohemian Rhapsody",
        interpret="Queen",
        album="A Night at the Opera",
        jahr="1975",
        dauer=354.0,
    )


@pytest.fixture
def song_ohne_meta():
    """Song ohne jegliche Metadaten -- nur der Pfad ist bekannt."""
    return Song(pfad="/musik/unbekannt.mp3")


@pytest.fixture
def bibliothek_mit_songs(song_vollstaendig):
    """Bibliothek mit mehreren Songs fuer Such- und Sortiertests."""
    bib = Bibliothek()
    bib.hinzufuegen(Song(pfad="/a.mp3", titel="Stairway to Heaven",
                         interpret="Led Zeppelin", album="Led Zeppelin IV", jahr="1971", dauer=482.0))
    bib.hinzufuegen(Song(pfad="/b.mp3", titel="Hotel California",
                         interpret="Eagles", album="Hotel California", jahr="1977", dauer=391.0))
    bib.hinzufuegen(song_vollstaendig)
    bib.hinzufuegen(Song(pfad="/c.mp3", titel="Bohemian Rhapsody",
                         interpret="Queen", album="Live at Wembley", jahr="1986", dauer=360.0))
    return bib


# =============================================================================
# Tests: Song
# =============================================================================

class TestSong:

    def test_titel_anzeige_mit_tag(self, song_vollstaendig):
        """titel_anzeige gibt den ID3-Titel zurueck wenn vorhanden."""
        assert song_vollstaendig.titel_anzeige == "Bohemian Rhapsody"

    def test_titel_anzeige_fallback_dateiname(self, song_ohne_meta):
        """titel_anzeige faellt auf den Dateinamen zurueck wenn kein Titel."""
        assert song_ohne_meta.titel_anzeige == "unbekannt"

    def test_interpret_anzeige_fallback(self, song_ohne_meta):
        assert song_ohne_meta.interpret_anzeige == "Unbekannt"

    def test_dauer_anzeige_format(self, song_vollstaendig):
        """5:54 fuer 354 Sekunden."""
        assert song_vollstaendig.dauer_anzeige == "5:54"

    def test_dauer_anzeige_null(self, song_ohne_meta):
        assert song_ohne_meta.dauer_anzeige == "–"

    def test_dauer_anzeige_mit_fuehrender_null(self):
        s = Song(pfad="/a.mp3", dauer=63.0)
        assert s.dauer_anzeige == "1:03"

    def test_enthaelt_titel(self, song_vollstaendig):
        assert song_vollstaendig.enthaelt("bohemian") is True
        assert song_vollstaendig.enthaelt("RHAPSODY") is True

    def test_enthaelt_interpret(self, song_vollstaendig):
        assert song_vollstaendig.enthaelt("queen") is True

    def test_enthaelt_nicht(self, song_vollstaendig):
        assert song_vollstaendig.enthaelt("nirvana") is False

    def test_enthaelt_teilstring(self, song_vollstaendig):
        assert song_vollstaendig.enthaelt("Bohemi") is True

    def test_serialisierung_roundtrip(self, song_vollstaendig):
        """als_dict() -> aus_dict() muss identischen Song liefern."""
        d = song_vollstaendig.als_dict()
        rekonstruiert = Song.aus_dict(d)
        assert rekonstruiert == song_vollstaendig

    def test_aus_dict_ignoriert_unbekannte_felder(self):
        """Zukunftssicherheit: unbekannte Felder im JSON werden ignoriert."""
        d = {
            "pfad": "/a.mp3",
            "titel": "Test",
            "unbekanntes_feld": "wird ignoriert",
        }
        song = Song.aus_dict(d)
        assert song.titel == "Test"


# =============================================================================
# Tests: Bibliothek
# =============================================================================

class TestBibliothek:

    def test_hinzufuegen(self, bibliothek_mit_songs):
        assert bibliothek_mit_songs.anzahl == 4

    def test_leeren(self, bibliothek_mit_songs):
        bibliothek_mit_songs.leeren()
        assert bibliothek_mit_songs.anzahl == 0

    def test_suchen_findet_treffer(self, bibliothek_mit_songs):
        ergebnis = bibliothek_mit_songs.suchen("queen")
        assert len(ergebnis) == 2
        assert all("queen" in s.interpret.lower() for s in ergebnis)

    def test_suchen_leer_gibt_alle(self, bibliothek_mit_songs):
        ergebnis = bibliothek_mit_songs.suchen("")
        assert len(ergebnis) == bibliothek_mit_songs.anzahl

    def test_suchen_kein_treffer(self, bibliothek_mit_songs):
        ergebnis = bibliothek_mit_songs.suchen("zzzniemand")
        assert ergebnis == []

    def test_suchen_case_insensitive(self, bibliothek_mit_songs):
        assert len(bibliothek_mit_songs.suchen("QUEEN")) == 2
        assert len(bibliothek_mit_songs.suchen("Queen")) == 2

    def test_sortieren_nach_interpret(self, bibliothek_mit_songs):
        sortiert = bibliothek_mit_songs.sortieren(nach="interpret")
        interpreten = [s.interpret for s in sortiert]
        assert interpreten == sorted(interpreten, key=str.lower)

    def test_sortieren_absteigend(self, bibliothek_mit_songs):
        sortiert = bibliothek_mit_songs.sortieren(nach="titel", absteigend=True)
        titel = [s.titel for s in sortiert]
        assert titel == sorted(titel, key=str.lower, reverse=True)

    def test_sortieren_unbekanntes_feld(self, bibliothek_mit_songs):
        with pytest.raises(ValueError):
            bibliothek_mit_songs.sortieren(nach="nichtexistent")

    def test_duplikate_erkennung(self, bibliothek_mit_songs):
        """Bohemian Rhapsody von Queen erscheint zweimal."""
        duplikate = bibliothek_mit_songs.duplikate()
        assert len(duplikate) == 1
        assert len(duplikate[0]) == 2

    def test_keine_duplikate(self):
        bib = Bibliothek()
        bib.hinzufuegen(Song(pfad="/a.mp3", titel="A", interpret="X"))
        bib.hinzufuegen(Song(pfad="/b.mp3", titel="B", interpret="Y"))
        assert bib.duplikate() == []

    def test_statistiken_gesamtdauer(self, bibliothek_mit_songs):
        stats = bibliothek_mit_songs.statistiken()
        erwartet = sum(s.dauer for s in bibliothek_mit_songs.alle())
        assert stats["gesamtdauer_sek"] == pytest.approx(erwartet)

    def test_statistiken_anzahl(self, bibliothek_mit_songs):
        stats = bibliothek_mit_songs.statistiken()
        assert stats["anzahl_songs"] == 4

    def test_statistiken_interpreten(self, bibliothek_mit_songs):
        stats = bibliothek_mit_songs.statistiken()
        assert stats["interpreten"] == 3   # Queen, Led Zeppelin, Eagles

    def test_alle_interpreten_alphabetisch(self, bibliothek_mit_songs):
        interpreten = bibliothek_mit_songs.alle_interpreten()
        assert interpreten == sorted(interpreten, key=str.lower)

    def test_persistenz_roundtrip(self, bibliothek_mit_songs):
        """speichern() -> laden() muss identische Bibliothek liefern."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            pfad = Path(f.name)

        try:
            bibliothek_mit_songs.speichern(pfad)

            neue_bib = Bibliothek()
            anzahl = neue_bib.laden(pfad)

            assert anzahl == bibliothek_mit_songs.anzahl
            original  = sorted(bibliothek_mit_songs.alle(), key=lambda s: s.pfad)
            geladen   = sorted(neue_bib.alle(), key=lambda s: s.pfad)
            assert original == geladen

        finally:
            pfad.unlink(missing_ok=True)

    def test_laden_nicht_existierende_datei(self):
        bib = Bibliothek()
        with pytest.raises(FileNotFoundError):
            bib.laden("/existiert/nicht.json")

    def test_csv_export(self, bibliothek_mit_songs):
        """CSV-Export erstellt eine lesbare Datei mit Kopfzeile."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            pfad = Path(f.name)

        try:
            bibliothek_mit_songs.exportieren_csv(pfad)
            zeilen = pfad.read_text(encoding="utf-8").splitlines()
            assert zeilen[0].startswith("titel")   # Kopfzeile vorhanden
            assert len(zeilen) == bibliothek_mit_songs.anzahl + 1   # +1 fuer Kopfzeile

        finally:
            pfad.unlink(missing_ok=True)


# =============================================================================
# Tests: Scanner (mit echten Testdateien)
# =============================================================================

class TestScanner:
    """
    Diese Tests erstellen echte MP3-Testdateien im tmp-Verzeichnis.
    Sie testen den kompletten Weg von der Datei bis zum Song-Objekt.
    """

    @pytest.fixture(autouse=True)
    def testverzeichnis(self, tmp_path):
        """Erstellt Testdateien vor jedem Test und raeumt danach auf."""
        from scanner import erstelle_testdateien
        self.verz = tmp_path / "musik"
        self.testdateien = erstelle_testdateien(self.verz, anzahl=5)

    def test_scan_findet_dateien(self):
        from scanner import scanne_verzeichnis
        songs, fehler = scanne_verzeichnis(self.verz)
        assert len(songs) == 5
        assert fehler == []

    def test_scan_liefert_song_objekte(self):
        from scanner import scanne_verzeichnis
        songs, _ = scanne_verzeichnis(self.verz)
        assert all(isinstance(s, Song) for s in songs)

    def test_scan_liest_pfad(self):
        from scanner import scanne_verzeichnis
        songs, _ = scanne_verzeichnis(self.verz)
        pfade = [Path(s.pfad) for s in songs]
        assert all(p.exists() for p in pfade)

    def test_scan_liest_metadaten(self):
        from scanner import scanne_verzeichnis
        songs, _ = scanne_verzeichnis(self.verz)
        # Mindestens ein Song sollte einen Titel haben (Testdaten enthalten Tags)
        hat_titel = any(s.titel is not None for s in songs)
        assert hat_titel

    def test_scan_nicht_existierendes_verzeichnis(self):
        from scanner import scanne_verzeichnis
        with pytest.raises(FileNotFoundError):
            scanne_verzeichnis("/existiert/nicht")

    def test_scan_fortschritt_callback(self):
        from scanner import scanne_verzeichnis
        aufrufe = []

        def callback(aktuell, gesamt, name):
            aufrufe.append((aktuell, gesamt))

        songs, _ = scanne_verzeichnis(self.verz, fortschritt_callback=callback)
        assert len(aufrufe) == len(songs)
        assert aufrufe[-1][0] == aufrufe[-1][1]   # letzter Aufruf: aktuell == gesamt

    def test_scan_unterordner_rekursiv(self, tmp_path):
        """rglob() findet auch MP3s in Unterordnern -- eigener Pfad, kein autouse-Overlap."""
        from scanner import erstelle_testdateien, scanne_verzeichnis
        basis       = tmp_path / "basis"
        unterordner = basis / "tief" / "verschachtelt"
        erstelle_testdateien(unterordner, anzahl=3)

        songs, _ = scanne_verzeichnis(basis)
        assert len(songs) == 3
