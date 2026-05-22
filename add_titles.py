"""
add_titles.py
-------------
Fügt in jedes .ipynb ohne H1-Titel eine neue erste Zelle mit
"# Titel aus Dateiname" ein. Notebooks die bereits einen H1 haben
werden nicht verändert.

Aufruf:
    python add_titles.py

Das Skript muss im KURS-Ordner liegen (oder den Pfad anpassen).
"""

import json
import os
import re
from pathlib import Path

# ── Konfiguration ─────────────────────────────────────────────
KURS_DIR = Path(__file__).parent   # Ordner in dem das Skript liegt
EXCLUDE_DIRS = {"_build", ".ipynb_checkpoints", "__pycache__",
                "Projekt Mastermind", "Projekt MP3", "Klausur"}
DRY_RUN = False   # True = nur anzeigen, nichts speichern
# ──────────────────────────────────────────────────────────────


def dateiname_zu_titel(stem: str) -> str:
    """
    Wandelt Dateinamen in lesbare Titel um.
    Beispiele:
      01b_namespaces_legb        -> Namespaces & LEGB
      03d_decorators             -> Decorators
      04_Szenario_Aetherion      -> Szenario Aetherion
      aufgaben_12a_web_services  -> Aufgaben: Web Services
    """
    # Führende Nummerierung entfernen (01b_, 03d_, 12a_ usw.)
    stem = re.sub(r'^\d+[a-z]?_', '', stem)
    stem = re.sub(r'^\d+_', '', stem)

    # Aufgaben-Prefix erkennen
    is_aufgabe = stem.lower().startswith('aufgabe')
    if is_aufgabe:
        stem = re.sub(r'^[Aa]ufgaben?_', '', stem)
        stem = re.sub(r'^\d+[a-z]?_', '', stem)  # nochmal nach "Aufgaben_12a_"

    # Unterstriche zu Leerzeichen
    titel = stem.replace('_', ' ').strip()

    # Kapitalisierung: erstes Wort groß, Rest wie im Original
    if titel:
        titel = titel[0].upper() + titel[1:]

    # Präfix zurückfügen
    if is_aufgabe:
        titel = "Aufgaben: " + titel

    return titel


def hat_h1(notebook: dict) -> bool:
    """Prüft ob das Notebook bereits eine H1-Zelle hat."""
    for cell in notebook.get("cells", [])[:5]:
        if cell.get("cell_type") == "markdown":
            src = "".join(cell.get("source", []))
            if re.match(r'^#\s+\S', src.strip()):
                return True
    return False


def neue_titelzelle(titel: str) -> dict:
    """Erstellt eine neue Markdown-Zelle mit H1-Titel."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [f"# {titel}"]
    }


def verarbeite_notebook(pfad: Path) -> bool:
    """
    Liest Notebook, fügt Titelzelle ein wenn nötig.
    Gibt True zurück wenn Datei geändert wurde.
    """
    try:
        with open(pfad, encoding="utf-8") as f:
            nb = json.load(f)
    except Exception as e:
        print(f"  ⚠  Fehler beim Lesen: {pfad.name} – {e}")
        return False

    if hat_h1(nb):
        return False  # Bereits Titel vorhanden

    titel = dateiname_zu_titel(pfad.stem)
    nb["cells"].insert(0, neue_titelzelle(titel))

    if not DRY_RUN:
        with open(pfad, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)

    return True


def main():
    print(f"{'[DRY RUN] ' if DRY_RUN else ''}Durchsuche: {KURS_DIR}\n")

    geaendert = 0
    uebersprungen = 0
    fehler = 0

    for pfad in sorted(KURS_DIR.rglob("*.ipynb")):
        # Ausgeschlossene Ordner überspringen
        if any(ex in pfad.parts for ex in EXCLUDE_DIRS):
            continue
        # Checkpoint-Dateien überspringen
        if ".ipynb_checkpoints" in str(pfad):
            continue

        wurde_geaendert = verarbeite_notebook(pfad)

        rel = pfad.relative_to(KURS_DIR)
        if wurde_geaendert:
            titel = dateiname_zu_titel(pfad.stem)
            print(f"  ✓  {rel}")
            print(f"     → Titel: «{titel}»")
            geaendert += 1
        else:
            uebersprungen += 1

    print(f"\n{'─'*50}")
    print(f"  Geändert:      {geaendert}")
    print(f"  Übersprungen:  {uebersprungen} (bereits Titel vorhanden)")
    if DRY_RUN:
        print("  [DRY RUN] – keine Dateien wurden gespeichert")


if __name__ == "__main__":
    main()
