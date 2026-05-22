# =============================================================================
# mastermind/logik.py
#
# Die gesamte Spiellogik -- kein print(), kein tkinter, kein I/O.
# Alle Funktionen hier sind reine Funktionen: gleiche Eingabe, gleiche Ausgabe.
# Das macht sie einfach testbar und unabhaengig von der Darstellung.
# =============================================================================

import random

# -----------------------------------------------------------------------------
# Spielkonstanten
# Die Konstanten sind hier definiert damit GUI und Logik denselben Wert nutzen.
# -----------------------------------------------------------------------------

FARBEN = ["rot", "blau", "gruen", "gelb", "orange", "lila"]

# Farben als Abkuerzungen -- der Spieler kann beides eingeben
ABKUERZUNGEN = {
    "r": "rot",
    "b": "blau",
    "g": "gruen",
    "ge": "gelb",
    "o": "orange",
    "l": "lila",
}

STANDARD_LAENGE    = 4   # Anzahl Positionen im Geheimcode
STANDARD_VERSUCHE  = 10  # maximale Anzahl Versuche


# -----------------------------------------------------------------------------
# Geheimcode erzeugen
# -----------------------------------------------------------------------------

def erzeuge_code(laenge=STANDARD_LAENGE, farben=None, seed=None):
    """
    Gibt eine zufaellige Farbkombination als Liste zurueck.

    laenge  -- Anzahl Positionen (Standard: 4)
    farben  -- Liste moeglicher Farben (Standard: FARBEN)
    seed    -- optionaler Zufallsseed fuer reproduzierbare Ergebnisse (Tests)

    Beispiel:
        erzeuge_code(seed=42)  ->  ['lila', 'rot', 'orange', 'blau']
    """
    if farben is None:
        farben = FARBEN

    if seed is not None:
        random.seed(seed)

    # random.choices erlaubt Wiederholungen -- genau das will Mastermind
    return random.choices(farben, k=laenge)


# -----------------------------------------------------------------------------
# Eingabe normalisieren und validieren
# -----------------------------------------------------------------------------

def normalisiere_eingabe(text, laenge=STANDARD_LAENGE, farben=None):
    """
    Parst einen Eingabe-String und gibt eine bereinigte Farbliste zurueck.
    Wirft ValueError mit erklaerenden Meldungen bei ungueltigem Input.

    Der Spieler kann Farbnamen oder Abkuerzungen eingeben, gross oder klein:
        'rot blau rot gruen'
        'R B R G'
        'r b r g'

    Gibt eine Liste wie ['rot', 'blau', 'rot', 'gruen'] zurueck.
    """
    if farben is None:
        farben = FARBEN

    # Leerzeichen am Rand entfernen, alles kleinschreiben, bei Leerzeichen teilen
    teile = text.strip().lower().split()

    if len(teile) != laenge:
        raise ValueError(
            f"Bitte genau {laenge} Farben eingeben, getrennt durch Leerzeichen. "
            f"Du hast {len(teile)} eingegeben."
        )

    ergebnis = []
    for token in teile:
        # Zuerst pruefen ob es eine bekannte Abkuerzung ist
        if token in ABKUERZUNGEN:
            ergebnis.append(ABKUERZUNGEN[token])
        # Dann pruefen ob es ein vollstaendiger Farbname ist
        elif token in farben:
            ergebnis.append(token)
        else:
            gueltig = ", ".join(farben)
            kurz    = ", ".join(f"{k}={v}" for k, v in ABKUERZUNGEN.items())
            raise ValueError(
                f"'{token}' ist keine gueltige Farbe.\n"
                f"Gueltige Farben: {gueltig}\n"
                f"Abkuerzungen: {kurz}"
            )

    return ergebnis


# -----------------------------------------------------------------------------
# Kernlogik: Bewertung eines Versuchs
# -----------------------------------------------------------------------------

def bewerte(geheimcode, versuch):
    """
    Berechnet die schwarzen und weissen Treffer fuer einen Versuch.

    Schwarz = richtige Farbe an richtiger Position
    Weiss   = richtige Farbe an falscher Position

    Die wichtige Regel: Jede Farbe kann nur einmal als Treffer zaehlen.
    Schwarze Treffer haben Vorrang vor weissen -- ein schwarz gezaehltes
    Element zaehlt nicht nochmal als weiss.

    Gibt ein Tupel (schwarz, weiss) zurueck.

    Beispiele:
        bewerte(['r','b','r','g'], ['r','r','b','y']) -> (1, 1)
        bewerte(['r','r','b','g'], ['r','r','r','r']) -> (2, 0)
        bewerte(['r','b','g','y'], ['b','g','y','r']) -> (0, 4)
    """
    # Sicherheitscheck: beide Listen muessen gleich lang sein
    assert len(geheimcode) == len(versuch), "Laenge von Code und Versuch muss gleich sein"

    laenge = len(geheimcode)

    # Wir arbeiten mit Kopien -- die Originale werden nicht veraendert.
    # None markiert eine Position als 'verbraucht'.
    code_rest    = list(geheimcode)
    versuch_rest = list(versuch)

    # --- Schritt 1: Schwarze Treffer ---
    # Exakte Uebereinstimmungen (richtige Farbe, richtige Position).
    # Diese werden zuerst gezaehlt und verbraucht damit sie nicht
    # doppelt als weisse Treffer zaehlen.
    schwarz = 0
    for i in range(laenge):
        if versuch_rest[i] == code_rest[i]:
            schwarz += 1
            # Position in beiden Listen als verbraucht markieren
            code_rest[i]    = None
            versuch_rest[i] = None

    # --- Schritt 2: Weisse Treffer ---
    # Fuer jede noch nicht verbrauchte Position im Versuch pruefen ob
    # die Farbe irgendwo noch im restlichen Code vorkommt.
    weiss = 0
    for i in range(laenge):
        farbe = versuch_rest[i]
        if farbe is None:
            # Diese Position wurde bereits als schwarz gezaehlt
            continue
        if farbe in code_rest:
            weiss += 1
            # Die erste Fundstelle im Code verbrauchen
            code_rest[code_rest.index(farbe)] = None

    return schwarz, weiss


# -----------------------------------------------------------------------------
# Spielzustand -- eine Klasse die eine Partie haelt
# -----------------------------------------------------------------------------

class Spiel:
    """
    Haelt den kompletten Zustand einer laufenden Partie.

    Attribute:
        geheimcode  -- die zu erratende Farbkombination (List)
        max_versuche -- maximale Anzahl Versuche (int)
        versuche    -- Liste aller bisherigen Versuche (List[List[str]])
        bewertungen -- Liste der Bewertungen zu jedem Versuch (List[Tuple[int,int]])
        gewonnen    -- True wenn der letzte Versuch korrekt war
        laenge      -- Anzahl Positionen
    """

    def __init__(self, laenge=STANDARD_LAENGE, max_versuche=STANDARD_VERSUCHE,
                 farben=None, seed=None):
        self.laenge        = laenge
        self.max_versuche  = max_versuche
        self.farben        = farben or FARBEN
        self.geheimcode    = erzeuge_code(laenge=laenge, farben=self.farben, seed=seed)
        self.versuche      = []   # jeder Versuch: List[str]
        self.bewertungen   = []   # zu jedem Versuch: (schwarz, weiss)
        self.gewonnen      = False

    @property
    def anzahl_versuche(self):
        """Anzahl bisher gemachter Versuche."""
        return len(self.versuche)

    @property
    def versuche_uebrig(self):
        """Verbleibende Versuche."""
        return self.max_versuche - self.anzahl_versuche

    @property
    def ist_beendet(self):
        """True wenn das Spiel vorbei ist (gewonnen oder keine Versuche mehr)."""
        return self.gewonnen or self.anzahl_versuche >= self.max_versuche

    def versuch_ausfuehren(self, versuch):
        """
        Fuehrt einen Versuch aus und speichert ihn mit seiner Bewertung.

        versuch -- Liste von Farb-Strings, z.B. ['rot', 'blau', 'rot', 'gruen']

        Gibt das Bewertungs-Tupel (schwarz, weiss) zurueck.
        Wirft RuntimeError wenn das Spiel bereits beendet ist.
        """
        if self.ist_beendet:
            raise RuntimeError("Das Spiel ist bereits beendet.")

        ergebnis = bewerte(self.geheimcode, versuch)
        schwarz, _ = ergebnis

        self.versuche.append(versuch)
        self.bewertungen.append(ergebnis)

        # Gewonnen wenn alle Positionen schwarz (= exakt korrekt)
        if schwarz == self.laenge:
            self.gewonnen = True

        return ergebnis

    def verlauf(self):
        """
        Gibt den vollstaendigen Spielverlauf als Liste von Dicts zurueck.
        Jedes Dict: {'nr': int, 'versuch': List[str], 'schwarz': int, 'weiss': int}
        """
        ergebnis = []
        for i, (versuch, (schwarz, weiss)) in enumerate(
            zip(self.versuche, self.bewertungen), start=1
        ):
            ergebnis.append({
                "nr":      i,
                "versuch": versuch,
                "schwarz": schwarz,
                "weiss":   weiss,
            })
        return ergebnis
