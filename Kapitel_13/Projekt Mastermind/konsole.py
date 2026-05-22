# =============================================================================
# mastermind/konsole.py
#
# Konsolenversion von Mastermind.
# Importiert nur aus logik.py -- kein GUI-Code hier.
# Kann eigenstaendig gestartet werden: python konsole.py
# =============================================================================

from logik import (
    Spiel,
    normalisiere_eingabe,
    FARBEN,
    STANDARD_LAENGE,
    STANDARD_VERSUCHE,
)


# -----------------------------------------------------------------------------
# Darstellungshilfen -- formatieren Spielzustand als Text
# -----------------------------------------------------------------------------

FARB_SYMBOLE = {
    "rot":    "[R]",
    "blau":   "[B]",
    "gruen":  "[G]",
    "gelb":   "[Ge]",
    "orange": "[O]",
    "lila":   "[L]",
}


def farbe_als_text(farbe):
    """Gibt das Kurzsymbol fuer eine Farbe zurueck."""
    return FARB_SYMBOLE.get(farbe, f"[{farbe[:2].upper()}]")


def versuch_als_text(versuch):
    """Formatiert eine Farbliste als lesbaren String: [R] [B] [G] [Ge]"""
    return "  ".join(farbe_als_text(f) for f in versuch)


def zeige_verlauf(spiel):
    """Gibt alle bisherigen Versuche mit Bewertungen aus."""
    print()
    print("  Nr.  Versuch                    S  W")
    print("  " + "-" * 44)
    for eintrag in spiel.verlauf():
        nr       = eintrag["nr"]
        versuch  = versuch_als_text(eintrag["versuch"])
        schwarz  = eintrag["schwarz"]
        weiss    = eintrag["weiss"]
        print(f"  {nr:2d}.  {versuch:<26}  {schwarz}  {weiss}")
    print()


def zeige_hinweislegende():
    """Erklaert das Bewertungssystem einmalig beim Spielstart."""
    print(
        "\n  Bewertung nach jedem Versuch:\n"
        "    S = Schwarz: richtige Farbe, richtige Position\n"
        "    W = Weiss:   richtige Farbe, falsche Position\n"
        "\n  Ziel: 4x Schwarz (S=4)\n"
    )


def zeige_farbhilfe():
    """Gibt die verfuegbaren Farben und Abkuerzungen aus."""
    print(
        "\n  Verfuegbare Farben (Name oder Abkuerzung, getrennt durch Leerzeichen):\n"
        "    rot (r)   blau (b)   gruen (g)   gelb (ge)   orange (o)   lila (l)\n"
        "\n  Beispiel: rot blau gruen gelb   oder:  r b g ge\n"
    )


# -----------------------------------------------------------------------------
# Hauptspielschleife
# -----------------------------------------------------------------------------

def spielrunde(laenge=STANDARD_LAENGE, max_versuche=STANDARD_VERSUCHE):
    """
    Fuehrt eine vollstaendige Spielrunde durch.
    Gibt True zurueck wenn der Spieler gewonnen hat, sonst False.
    """
    spiel = Spiel(laenge=laenge, max_versuche=max_versuche)

    print("\n" + "=" * 50)
    print("  MASTERMIND")
    print("=" * 50)
    print(f"  Errate den Geheimcode ({laenge} Farben, {max_versuche} Versuche)")

    zeige_hinweislegende()
    zeige_farbhilfe()

    while not spiel.ist_beendet:
        verbleibend = spiel.versuche_uebrig
        print(f"  Versuch {spiel.anzahl_versuche + 1} von {max_versuche}  ({verbleibend} uebrig)")

        # Eingabe lesen -- Schleife bis valide Eingabe kommt
        while True:
            try:
                raw = input("  Dein Versuch: ").strip()

                # Spieler kann das Spiel abbrechen
                if raw.lower() in ("quit", "exit", "q"):
                    print("\n  Spiel abgebrochen.")
                    print(f"  Der Geheimcode war: {versuch_als_text(spiel.geheimcode)}")
                    return False

                versuch = normalisiere_eingabe(raw, laenge=laenge)
                break  # valide Eingabe -> Schleife verlassen

            except ValueError as fehler:
                print(f"\n  Fehler: {fehler}\n")

        # Versuch ausfuehren und Ergebnis anzeigen
        schwarz, weiss = spiel.versuch_ausfuehren(versuch)
        print(f"  -> Schwarz: {schwarz}  Weiss: {weiss}")

        # Nach jedem Versuch den vollstaendigen Verlauf anzeigen
        zeige_verlauf(spiel)

    # Spielende
    if spiel.gewonnen:
        print(f"  Glueckwunsch! Erraten in {spiel.anzahl_versuche} Versuch(en)!\n")
    else:
        print(f"  Leider nicht geschafft. Der Code war: {versuch_als_text(spiel.geheimcode)}\n")

    return spiel.gewonnen


def main():
    """Einstiegspunkt fuer die Konsolenversion. Ermoeglicht mehrere Runden."""
    siege    = 0
    niederlagen = 0

    while True:
        gewonnen = spielrunde()

        if gewonnen:
            siege += 1
        else:
            niederlagen += 1

        print(f"  Statistik: {siege} gewonnen, {niederlagen} verloren")
        print()

        antwort = input("  Nochmal spielen? (j/n): ").strip().lower()
        if antwort not in ("j", "ja", "y", "yes"):
            print("\n  Tschuess!\n")
            break


if __name__ == "__main__":
    main()
