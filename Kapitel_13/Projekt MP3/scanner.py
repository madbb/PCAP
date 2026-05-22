# =============================================================================
# mp3_verwaltung/scanner.py
#
# Liest MP3-Dateien vom Dateisystem und extrahiert ihre Metadaten.
#
# Abhaengigkeit: pip install mutagen
#
# Dieser Modul ist der einzige Teil des Programms der mit mutagen arbeitet.
# Alles andere (Bibliothek, GUI) kennt mutagen nicht -- sie arbeiten nur
# mit Song-Objekten aus modell.py.
# =============================================================================

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, ID3NoHeaderError

from modell import Song


# =============================================================================
# Metadaten aus einer einzelnen MP3-Datei lesen
# =============================================================================

def lese_song(pfad: Path) -> Song:
    """
    Liest eine einzelne MP3-Datei und gibt ein Song-Objekt zurueck.

    Wenn die Datei keine ID3-Tags hat oder ein Tag fehlt, wird der
    entsprechende Wert als None gesetzt -- kein Absturz, kein leerer String.

    Die Dauer wird aus den Audio-Informationen gelesen (nicht aus den Tags),
    das ist zuverlaessiger.

    ID3-Tag-Schluessel (die wichtigsten):
        TIT2  -- Titel
        TPE1  -- Interpret (Artist)
        TALB  -- Album
        TDRC  -- Aufnahmedatum/Jahr
        TRCK  -- Track-Nummer
    """

    # --- Audiodaten (Dauer, Bitrate) ---
    # MP3() liest die technischen Informationen unabhaengig von den Tags
    try:
        audio = MP3(pfad)
        dauer = audio.info.length   # float: Sekunden
    except Exception:
        # Datei konnte nicht als MP3 geoeffnet werden -- trotzdem einen Song
        # erstellen, nur ohne Dauer
        dauer = 0.0

    # --- ID3-Tags (Metadaten) ---
    titel     = None
    interpret = None
    album     = None
    jahr      = None

    try:
        tags = ID3(pfad)

        # Jeder Tag-Zugriff ist einzeln abgesichert -- so faellt ein
        # fehlender Tag nicht die gesamte Datei
        titel     = _lese_tag(tags, "TIT2")
        interpret = _lese_tag(tags, "TPE1")
        album     = _lese_tag(tags, "TALB")
        jahr      = _lese_tag_jahr(tags)

    except ID3NoHeaderError:
        # Datei hat gar keine ID3-Tags -- das ist normal und kein Fehler.
        # Alle Felder bleiben None.
        pass
    except Exception:
        # Unerwarteter Fehler beim Tag-Lesen -- ignorieren, weitermachen
        pass

    return Song(
        pfad=str(pfad.resolve()),   # absoluter Pfad als String
        titel=titel,
        interpret=interpret,
        album=album,
        jahr=jahr,
        dauer=dauer,
    )


def _lese_tag(tags: ID3, schluessel: str) -> Optional[str]:
    """
    Liest einen einzelnen ID3-Tag-Wert als String.
    Gibt None zurueck wenn der Tag nicht existiert oder leer ist.

    mutagen gibt Tag-Objekte zurueck, nicht direkt Strings.
    Die str()-Konvertierung extrahiert den Textinhalt.
    """
    try:
        wert = str(tags[schluessel])
        return wert.strip() or None   # leere Strings werden zu None
    except KeyError:
        return None


def _lese_tag_jahr(tags: ID3) -> Optional[str]:
    """
    Liest das Jahr aus dem TDRC-Tag.

    TDRC kann verschiedene Formate enthalten: '2024', '2024-01-15', '2024-01'.
    Wir extrahieren nur die ersten 4 Zeichen (das Jahr).
    """
    try:
        wert = str(tags["TDRC"]).strip()
        if wert:
            return wert[:4]   # nur das Jahr, nicht den vollstaendigen Timestamp
        return None
    except KeyError:
        return None


# =============================================================================
# Verzeichnis rekursiv scannen
# =============================================================================

def scanne_verzeichnis(
    verzeichnis: str | Path,
    fortschritt_callback: Optional[Callable[[int, int, str], None]] = None,
) -> tuple[list[Song], list[str]]:
    """
    Durchsucht ein Verzeichnis rekursiv nach MP3-Dateien und liest
    ihre Metadaten.

    verzeichnis          -- Pfad zum zu scannenden Ordner
    fortschritt_callback -- optionale Funktion die waehrend des Scannens
                           aufgerufen wird: callback(aktuell, gesamt, dateiname)
                           Damit kann die GUI einen Fortschrittsbalken anzeigen.

    Gibt ein Tupel zurueck:
        (liste_von_songs, liste_von_fehlermeldungen)

    Songs koennen auch dann zurueckgegeben werden wenn einzelne Dateien
    Probleme hatten -- Fehler werden in der Fehlerliste gesammelt, nicht
    als Exception geworfen. Das Programm laeuft weiter.
    """
    verzeichnis = Path(verzeichnis)

    if not verzeichnis.exists():
        raise FileNotFoundError(f"Verzeichnis nicht gefunden: {verzeichnis}")
    if not verzeichnis.is_dir():
        raise NotADirectoryError(f"Ist kein Verzeichnis: {verzeichnis}")

    # Alle .mp3-Dateien sammeln (rglob geht rekursiv in alle Unterordner)
    # rglob('*.mp3') ist case-sensitive auf Linux -- wir pruefen daher auch *.MP3
    mp3_dateien = sorted(
        list(verzeichnis.rglob("*.mp3")) +
        list(verzeichnis.rglob("*.MP3"))
    )

    # Doppelte entfernen (tritt auf wenn Dateiname gemischte Gross-/Kleinschreibung hat)
    mp3_dateien = list(dict.fromkeys(mp3_dateien))

    gesamt   = len(mp3_dateien)
    songs    = []
    fehler   = []

    for i, pfad in enumerate(mp3_dateien, start=1):
        # Fortschritt melden wenn ein Callback uebergeben wurde
        if fortschritt_callback:
            fortschritt_callback(i, gesamt, pfad.name)

        try:
            song = lese_song(pfad)
            songs.append(song)
        except Exception as e:
            # Einzelne fehlerhafte Datei nicht den gesamten Scan abbrechen lassen
            fehler.append(f"{pfad.name}: {e}")

    return songs, fehler


# =============================================================================
# Testdateien erstellen (fuer Entwicklung ohne echte MP3-Sammlung)
# =============================================================================

def erstelle_testdateien(verzeichnis: str | Path, anzahl: int = 10) -> list[Path]:
    """
    Erstellt minimale MP3-Testdateien mit verschiedenen ID3-Tags.
    Nuetzlich zum Entwickeln und Testen ohne echte Musikdateien.

    Die erzeugten Dateien sind keine echten Audiodateien -- nur die
    minimale Byte-Struktur die mutagen als MP3 akzeptiert, plus ID3-Tags.

    Gibt die Liste der erstellten Pfade zurueck.
    """
    from mutagen.id3 import TIT2, TPE1, TALB, TDRC

    verzeichnis = Path(verzeichnis)
    verzeichnis.mkdir(parents=True, exist_ok=True)

    # Beispieldaten -- absichtlich mit Luecken um Fallback-Logik zu testen
    testdaten = [
        ("Bohemian Rhapsody",        "Queen",            "A Night at the Opera", "1975"),
        ("Stairway to Heaven",       "Led Zeppelin",     "Led Zeppelin IV",      "1971"),
        ("Hotel California",         "Eagles",           "Hotel California",     "1977"),
        ("Smells Like Teen Spirit",  "Nirvana",          "Nevermind",            "1991"),
        ("Like a Rolling Stone",     "Bob Dylan",        None,                   "1965"),
        ("Purple Haze",              "Jimi Hendrix",     "Are You Experienced",  "1967"),
        (None,                       "The Beatles",      "Abbey Road",           "1969"),   # kein Titel
        ("Imagine",                  None,               "Imagine",              "1971"),   # kein Interpret
        ("Blue (Da Ba Dee)",         "Eiffel 65",        "Europop",              "1998"),
        ("Yesterday",                "The Beatles",      "Help!",                "1965"),
        ("Thriller",                 "Michael Jackson",  "Thriller",             "1982"),
        ("Like a Prayer",            "Madonna",          "Like a Prayer",        "1989"),
    ]

    # Wenn mehr als die Testdaten benoetigt werden, einfach wiederholen
    erstellte = []

    for i in range(anzahl):
        eintrag = testdaten[i % len(testdaten)]
        titel, interpret, album, jahr = eintrag

        # Dateiname: entweder Titel oder generisch
        dateiname = f"{titel or f'song_{i+1:02d}'}.mp3"
        # Sonderzeichen aus Dateinamen entfernen
        dateiname = "".join(c for c in dateiname if c.isalnum() or c in " ._-").strip()
        pfad = verzeichnis / dateiname

        # Minimaler MP3-Frame -- 4 Bytes Header + leere Audiodaten
        # Das ist technisch kein abspielbares Audio, aber mutagen liest es
        mp3_header = bytes([0xFF, 0xFB, 0x90, 0x00])   # MPEG1, Layer3, 128kbps, 44.1kHz
        with open(pfad, "wb") as f:
            f.write(mp3_header + bytes(128))

        # ID3-Tags schreiben
        tags = ID3()
        if titel:
            tags["TIT2"] = TIT2(encoding=3, text=titel)
        if interpret:
            tags["TPE1"] = TPE1(encoding=3, text=interpret)
        if album:
            tags["TALB"] = TALB(encoding=3, text=album)
        if jahr:
            tags["TDRC"] = TDRC(encoding=3, text=jahr)

        tags.save(pfad)
        erstellte.append(pfad)

    return erstellte
