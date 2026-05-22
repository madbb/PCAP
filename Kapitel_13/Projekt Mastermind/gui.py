# =============================================================================
# mastermind/gui.py
#
# Grafische Oberflaeche fuer Mastermind mit tkinter.
# Starten mit: python gui.py
#
# Aufbau der Datei:
#   1. Konstanten (Farben, Groessen, Design)
#   2. FarbButton -- ein klickbarer Kreis fuer die Eingabezeile
#   3. VersuchsZeile -- eine Zeile im Spielfeld (Kreise + Bewertungspins)
#   4. FarbAuswahl -- die Farbpalette unten
#   5. MastermindApp -- das Hauptfenster, verbindet alles
#   6. main()
# =============================================================================

import tkinter as tk
from tkinter import messagebox

# logik.py muss im selben Ordner liegen
from logik import (
    Spiel,
    FARBEN,
    STANDARD_LAENGE,
    STANDARD_VERSUCHE,
)


# =============================================================================
# 1. Design-Konstanten
# =============================================================================

# Farbnamen auf Hex-Codes mappen -- tkinter arbeitet mit Hex oder Farbnamen
FARB_HEX = {
    "rot":    "#e53935",
    "blau":   "#1e88e5",
    "gruen":  "#43a047",
    "gelb":   "#fdd835",
    "orange": "#fb8c00",
    "lila":   "#8e24aa",
}

# Platzhalterfarbe fuer noch nicht belegte Felder
LEER_FARBE   = "#2a2a3a"   # dunkles Grau-Blau
LEER_RAND    = "#4a4a5a"   # etwas hellerer Rahmen

# Bewertungspin-Farben
PIN_SCHWARZ  = "#f5f5f5"   # weiss/hellgrau fuer "schwarz" (besser sichtbar auf dunklem BG)
PIN_WEISS    = "#555577"   # gedaempftes Blaugrau fuer "weiss"
PIN_LEER     = "#1e1e2e"   # fast unsichtbar fuer "kein Treffer"

# Hintergrundfarben
BG_HAUPT     = "#12121f"   # fast schwarz, leicht blau
BG_FELD      = "#1a1a2e"   # Spielfeld-Hintergrund
BG_PALETTE   = "#0f0f1e"   # Farbpalette unten

# Akzentfarbe fuer aktive Zeile und Buttons
AKZENT       = "#4fc3f7"

# Groessen in Pixeln
KREIS_R      = 22   # Radius der Spielkreise (halber Durchmesser)
PIN_R        = 7    # Radius der Bewertungspins
ABSTAND      = 60   # Abstand zwischen Kreismittelpunkten in einer Zeile
ZEILEN_H     = 55   # Hoehe einer Versuchszeile
RAND         = 20   # aeusserer Rand


# =============================================================================
# 2. VersuchsZeile -- eine Zeile im Spielfeld
# =============================================================================

class VersuchsZeile:
    """
    Zeichnet eine einzelne Versuchszeile auf dem Canvas.
    Besteht aus:
      - Zeilennummer (Label links)
      - N Farbkreisen (ein Kreis pro Position)
      - 2x2 Bewertungspins (rechts)

    Der Canvas wird von aussen uebergeben -- VersuchsZeile zeichnet sich selbst
    an eine bestimmte y-Position.
    """

    def __init__(self, canvas, y_mitte, laenge, zeilen_nr, aktiv=False):
        """
        canvas    -- tkinter Canvas auf dem gezeichnet wird
        y_mitte   -- vertikale Mitte der Zeile in Canvas-Koordinaten
        laenge    -- Anzahl Positionen (= Anzahl Kreise)
        zeilen_nr -- Beschriftung links (1-basiert)
        aktiv     -- True wenn dies die aktuell spielbare Zeile ist
        """
        self.canvas   = canvas
        self.y        = y_mitte
        self.laenge   = laenge
        self.aktiv    = aktiv

        # IDs der Canvas-Elemente -- wir brauchen sie um die Farbe spaeter zu aendern
        self.kreis_ids = []   # Oval-IDs fuer die Farbkreise
        self.pin_ids   = []   # Oval-IDs fuer die Bewertungspins

        self._zeichne(zeilen_nr)

    def _zeichne(self, zeilen_nr):
        """Zeichnet die Zeile initial (leer)."""
        canvas = self.canvas

        # Hintergrundbalken fuer aktive Zeile -- subtile Hervorhebung
        if self.aktiv:
            x0 = RAND - 8
            x1 = self._pin_bereich_x() + PIN_R * 4 + 10
            canvas.create_rectangle(
                x0, self.y - ZEILEN_H // 2 + 4,
                x1, self.y + ZEILEN_H // 2 - 4,
                fill="#1e2a3a", outline=AKZENT, width=1
            )

        # Zeilennummer links
        canvas.create_text(
            RAND - 4, self.y,
            text=str(zeilen_nr),
            fill="#555577" if not self.aktiv else AKZENT,
            font=("Segoe UI", 9),
            anchor="e"
        )

        # Farbkreise
        for i in range(self.laenge):
            x = self._x_kreis(i)
            oid = canvas.create_oval(
                x - KREIS_R, self.y - KREIS_R,
                x + KREIS_R, self.y + KREIS_R,
                fill=LEER_FARBE, outline=LEER_RAND, width=2
            )
            self.kreis_ids.append(oid)

        # Bewertungspins: 2x2 Raster rechts der Farbkreise
        # Layout: oben-links, oben-rechts, unten-links, unten-rechts
        px_start = self._pin_bereich_x()
        positionen = [
            (px_start,          self.y - PIN_R - 2),
            (px_start + PIN_R * 2 + 4, self.y - PIN_R - 2),
            (px_start,          self.y + PIN_R + 2),
            (px_start + PIN_R * 2 + 4, self.y + PIN_R + 2),
        ]
        for px, py in positionen:
            pid = canvas.create_oval(
                px - PIN_R, py - PIN_R,
                px + PIN_R, py + PIN_R,
                fill=PIN_LEER, outline="#2a2a3a", width=1
            )
            self.pin_ids.append(pid)

    def _x_kreis(self, index):
        """X-Koordinate des Kreismittelpunkts an Position index."""
        # Kreise zentriert ab RAND + etwas Platz fuer die Zeilennummer
        return RAND + 20 + index * ABSTAND + KREIS_R

    def _pin_bereich_x(self):
        """X-Start des Bewertungsbereichs (linker Pin, Mitte)."""
        letzte_kreis_x = self._x_kreis(self.laenge - 1)
        return letzte_kreis_x + KREIS_R + 20

    def setze_farben(self, farbliste):
        """
        Faerbt die Kreise ein.
        farbliste -- Liste von Farb-Strings wie ['rot', 'blau', 'gruen', 'gelb']
        Kann auch None-Eintraege enthalten fuer noch leere Positionen.
        """
        for i, farbe in enumerate(farbliste):
            if farbe is None:
                self.canvas.itemconfig(self.kreis_ids[i], fill=LEER_FARBE, outline=LEER_RAND)
            else:
                hex_farbe = FARB_HEX.get(farbe, "#888888")
                self.canvas.itemconfig(self.kreis_ids[i], fill=hex_farbe, outline="#ffffff")

    def setze_bewertung(self, schwarz, weiss):
        """
        Faerbt die Bewertungspins ein.
        Schwarze Pins zuerst, dann weisse, Rest bleibt dunkel.
        """
        for i, pin_id in enumerate(self.pin_ids):
            if i < schwarz:
                self.canvas.itemconfig(pin_id, fill=PIN_SCHWARZ, outline="#888888")
            elif i < schwarz + weiss:
                self.canvas.itemconfig(pin_id, fill=PIN_WEISS, outline="#666688")
            else:
                self.canvas.itemconfig(pin_id, fill=PIN_LEER, outline="#2a2a3a")

    def breite(self):
        """Gesamtbreite dieser Zeile -- benoetigt fuer Canvas-Groessenberechnung."""
        pin_x = self._pin_bereich_x()
        return pin_x + PIN_R * 2 + RAND + 20


# =============================================================================
# 3. FarbAuswahl -- die Palette mit klickbaren Farbkreisen
# =============================================================================

class FarbAuswahl:
    """
    Zeigt alle verfuegbaren Farben als klickbare Kreise an.
    Beim Klick wird ein Callback aufgerufen mit der gewaehlten Farbe.
    """

    def __init__(self, parent, farben, callback, breite):
        """
        parent   -- uebergeordnetes tkinter-Widget
        farben   -- Liste der Farbnamen
        callback -- Funktion die mit (farbe: str) aufgerufen wird
        breite   -- Gesamtbreite des Bereichs in Pixeln
        """
        self.callback = callback
        self.farben   = farben

        # Canvas fuer die Farbkreise
        hoehe = KREIS_R * 2 + 24
        self.canvas = tk.Canvas(
            parent,
            width=breite, height=hoehe,
            bg=BG_PALETTE, highlightthickness=0
        )
        self.canvas.pack(pady=(0, 8))

        # Abstand zwischen Kreisen so berechnen dass sie gleichmaessig verteilt sind
        n = len(farben)
        schritt = breite // (n + 1)

        for i, farbe in enumerate(farben):
            x = schritt * (i + 1)
            y = hoehe // 2

            # Aeusserer Rahmenkreis (vergroessert sich beim Hover -- wuerde JS brauchen,
            # also hier nur visuell hervorgehoben durch helleren Rand)
            hex_farbe = FARB_HEX[farbe]
            oid = self.canvas.create_oval(
                x - KREIS_R, y - KREIS_R,
                x + KREIS_R, y + KREIS_R,
                fill=hex_farbe, outline="#ffffff", width=2,
                tags=("farbe", farbe)
            )

            # Farbname darunter als kleines Label
            self.canvas.create_text(
                x, y + KREIS_R + 8,
                text=farbe[:3].capitalize(),
                fill="#7a7a90", font=("Segoe UI", 7),
                tags=("label", farbe)
            )

            # Klick-Binding fuer Kreis und Label
            self.canvas.tag_bind(oid,          "<Button-1>", self._on_klick)
            self.canvas.tag_bind(("label", farbe), "<Button-1>", self._on_klick)

            # Cursor aendern wenn Maus drueber
            self.canvas.tag_bind(oid, "<Enter>",
                lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(oid, "<Leave>",
                lambda e: self.canvas.config(cursor=""))

    def _on_klick(self, event):
        """Ermittelt welche Farbe geklickt wurde und ruft den Callback auf."""
        # Tags enthalten die Farbe als zweites Element: ("farbe", "rot")
        tags = self.canvas.gettags(tk.CURRENT)
        for tag in tags:
            if tag in self.farben:
                self.callback(tag)
                return


# =============================================================================
# 4. MastermindApp -- das Hauptfenster
# =============================================================================

class MastermindApp:
    """
    Das Hauptfenster der Anwendung.

    Verwaltet:
    - Das Spielfeld (Canvas mit VersuchsZeilen)
    - Die Eingabezeile (aktuelle Farbeingabe)
    - Die Farbpalette (FarbAuswahl)
    - Den Spielzustand (Spiel-Objekt aus logik.py)
    - Alle Buttons und Labels
    """

    def __init__(self, root, laenge=STANDARD_LAENGE, max_versuche=STANDARD_VERSUCHE):
        """
        root        -- tk.Tk Hauptfenster
        laenge      -- Codelange (Anzahl Positionen)
        max_versuche -- maximale Versuche
        """
        self.root         = root
        self.laenge       = laenge
        self.max_versuche = max_versuche

        # Laufendes Spiel-Objekt
        self.spiel = Spiel(laenge=laenge, max_versuche=max_versuche)

        # Aktuelle Eingabe: Liste von Farben oder None fuer leere Position
        # Startzustand: alle Positionen leer
        self.aktuelle_eingabe = [None] * laenge

        # Alle VersuchsZeilen -- wir brauchen sie um sie spaeter zu aktualisieren
        self.zeilen = []

        # Canvas-Groesse berechnen:
        # Breite: RAND + Zeilennummer + N Kreise + Pins + RAND
        # Hoehe: RAND + N Zeilen + RAND
        beispiel_zeile = VersuchsZeile.__new__(VersuchsZeile)
        beispiel_zeile.laenge = laenge
        self._canvas_breite = RAND + 20 + (laenge * ABSTAND) + (KREIS_R * 2) + 80
        self._canvas_hoehe  = RAND + max_versuche * ZEILEN_H + RAND

        self._baue_ui()

    # -------------------------------------------------------------------------
    # UI aufbauen
    # -------------------------------------------------------------------------

    def _baue_ui(self):
        """Baut das gesamte Fenster auf."""
        self.root.title("Mastermind")
        self.root.configure(bg=BG_HAUPT)
        self.root.resizable(False, False)

        # Titel
        tk.Label(
            self.root,
            text="MASTERMIND",
            bg=BG_HAUPT, fg=AKZENT,
            font=("Segoe UI", 18, "bold"),
            pady=12
        ).pack()

        # Status-Label (zeigt Versuche uebrig, Gewinn/Verlust-Meldungen)
        self.status_var = tk.StringVar(value=self._status_text())
        tk.Label(
            self.root,
            textvariable=self.status_var,
            bg=BG_HAUPT, fg="#c5cae9",
            font=("Segoe UI", 10)
        ).pack(pady=(0, 8))

        # Spielfeld-Canvas
        self.canvas = tk.Canvas(
            self.root,
            width=self._canvas_breite,
            height=self._canvas_hoehe,
            bg=BG_FELD, highlightthickness=0
        )
        self.canvas.pack(padx=RAND, pady=(0, 4))

        # Alle Versuchszeilen zeichnen
        for i in range(self.max_versuche):
            # Zeilen von oben: erste Zeile ist Versuch 1, letzte ist Versuch max
            y = RAND + i * ZEILEN_H + ZEILEN_H // 2
            aktiv = (i == 0)   # nur die erste Zeile ist beim Start aktiv
            zeile = VersuchsZeile(
                self.canvas, y, self.laenge,
                zeilen_nr=i + 1, aktiv=aktiv
            )
            self.zeilen.append(zeile)

        # Trennlinie
        tk.Frame(self.root, bg="#2a2a3a", height=1).pack(fill="x", padx=RAND)

        # Eingabebereich: zeigt die aktuelle Eingabe visuell
        self._baue_eingabebereich()

        # Trennlinie
        tk.Frame(self.root, bg="#2a2a3a", height=1).pack(fill="x", padx=RAND)

        # Farbpalette
        tk.Label(
            self.root,
            text="Farbe waehlen:",
            bg=BG_HAUPT, fg="#7a7a90",
            font=("Segoe UI", 9)
        ).pack(pady=(8, 2))

        FarbAuswahl(
            self.root,
            farben=FARBEN,
            callback=self._farbe_gewaehlt,
            breite=self._canvas_breite
        )

        # Buttons
        self._baue_buttons()

    def _baue_eingabebereich(self):
        """
        Zeigt die aktuell zusammengestellte Eingabe als kleine Kreise an.
        Darunter steht ein Hinweis welche Position als naechstes gewaehlt wird.
        """
        rahmen = tk.Frame(self.root, bg=BG_HAUPT)
        rahmen.pack(pady=6)

        tk.Label(
            rahmen,
            text="Dein naechster Versuch:",
            bg=BG_HAUPT, fg="#7a7a90",
            font=("Segoe UI", 9)
        ).pack()

        # Canvas fuer die Eingabekreise
        eingabe_h = KREIS_R * 2 + 8
        self.eingabe_canvas = tk.Canvas(
            rahmen,
            width=self._canvas_breite,
            height=eingabe_h,
            bg=BG_HAUPT, highlightthickness=0
        )
        self.eingabe_canvas.pack()

        # Kreise initial zeichnen
        self.eingabe_kreis_ids = []
        schritt = self._canvas_breite // (self.laenge + 1)
        for i in range(self.laenge):
            x = schritt * (i + 1)
            y = eingabe_h // 2
            oid = self.eingabe_canvas.create_oval(
                x - KREIS_R, y - KREIS_R,
                x + KREIS_R, y + KREIS_R,
                fill=LEER_FARBE, outline=LEER_RAND, width=2
            )
            self.eingabe_kreis_ids.append(oid)

            # Positionsnummer darunter
            self.eingabe_canvas.create_text(
                x, y + KREIS_R + 8,
                text=str(i + 1),
                fill="#444466", font=("Segoe UI", 8)
            )

        # Klick auf Eingabekreis -> diese Position leeren
        for i, oid in enumerate(self.eingabe_kreis_ids):
            self.eingabe_canvas.tag_bind(
                oid, "<Button-1>",
                lambda e, idx=i: self._position_leeren(idx)
            )

    def _baue_buttons(self):
        """Baut die Aktions-Buttons (Bestaetigen, Zurueck, Neu)."""
        btn_rahmen = tk.Frame(self.root, bg=BG_HAUPT)
        btn_rahmen.pack(pady=10)

        # Gemeinsame Button-Optionen
        btn_opt = dict(
            bg="#1e2a3a", fg="#e8eaf6",
            font=("Segoe UI", 10),
            relief="flat",
            padx=14, pady=6,
            cursor="hand2"
        )

        self.btn_absenden = tk.Button(
            btn_rahmen,
            text="Versuch absenden",
            command=self._versuch_absenden,
            activebackground=AKZENT,
            **btn_opt
        )
        self.btn_absenden.pack(side="left", padx=6)

        tk.Button(
            btn_rahmen,
            text="Letzte Farbe zurueck",
            command=self._letzte_farbe_zurueck,
            **btn_opt
        ).pack(side="left", padx=6)

        tk.Button(
            btn_rahmen,
            text="Neues Spiel",
            command=self._neues_spiel,
            **btn_opt
        ).pack(side="left", padx=6)

    # -------------------------------------------------------------------------
    # Spiellogik-Callbacks
    # -------------------------------------------------------------------------

    def _farbe_gewaehlt(self, farbe):
        """
        Wird aufgerufen wenn der Spieler in der Palette eine Farbe anklickt.
        Sucht die naechste freie Position in der aktuellen Eingabe und belegt sie.
        """
        if self.spiel.ist_beendet:
            return

        # Naechste freie Position finden
        for i in range(self.laenge):
            if self.aktuelle_eingabe[i] is None:
                self.aktuelle_eingabe[i] = farbe
                self._update_eingabe_anzeige()
                return

        # Alle Positionen belegt -- keine Aktion

    def _position_leeren(self, index):
        """Leert eine bestimmte Position in der Eingabe (Klick auf Eingabekreis)."""
        if self.spiel.ist_beendet:
            return
        self.aktuelle_eingabe[index] = None
        self._update_eingabe_anzeige()

    def _letzte_farbe_zurueck(self):
        """Entfernt die zuletzt gesetzte Farbe (rueckwaerts durch die Positionen)."""
        if self.spiel.ist_beendet:
            return
        # Letzte belegte Position finden (von rechts)
        for i in range(self.laenge - 1, -1, -1):
            if self.aktuelle_eingabe[i] is not None:
                self.aktuelle_eingabe[i] = None
                self._update_eingabe_anzeige()
                return

    def _versuch_absenden(self):
        """
        Wertet die aktuelle Eingabe als Versuch aus.
        Prueft ob alle Positionen belegt sind.
        Aktualisiert das Spielfeld und prueft auf Spielende.
        """
        if self.spiel.ist_beendet:
            return

        # Alle Positionen muessen belegt sein
        if None in self.aktuelle_eingabe:
            messagebox.showwarning(
                "Ungueltig",
                f"Bitte alle {self.laenge} Positionen auswaehlen."
            )
            return

        # Versuch an die Spiellogik uebergeben
        versuch = list(self.aktuelle_eingabe)
        schwarz, weiss = self.spiel.versuch_ausfuehren(versuch)

        # Aktuelle Zeile (die zuletzt gespielte) aktualisieren
        zeilen_index = self.spiel.anzahl_versuche - 1
        self.zeilen[zeilen_index].setze_farben(versuch)
        self.zeilen[zeilen_index].setze_bewertung(schwarz, weiss)

        # Eingabe zuruecksetzen
        self.aktuelle_eingabe = [None] * self.laenge
        self._update_eingabe_anzeige()

        # Naechste Zeile als aktiv markieren (Neuzeichnen noetig)
        self._markiere_aktive_zeile()

        # Status aktualisieren
        self.status_var.set(self._status_text())

        # Spielende pruefen
        if self.spiel.ist_beendet:
            self._zeige_spielende()

    def _neues_spiel(self):
        """Startet eine neue Partie -- alle Canvas-Elemente werden neu gezeichnet."""
        self.spiel            = Spiel(laenge=self.laenge, max_versuche=self.max_versuche)
        self.aktuelle_eingabe = [None] * self.laenge
        self.zeilen           = []

        # Canvas komplett leeren und neu zeichnen
        self.canvas.delete("all")
        for i in range(self.max_versuche):
            y    = RAND + i * ZEILEN_H + ZEILEN_H // 2
            aktiv = (i == 0)
            zeile = VersuchsZeile(
                self.canvas, y, self.laenge,
                zeilen_nr=i + 1, aktiv=aktiv
            )
            self.zeilen.append(zeile)

        # Eingabekreise leeren
        self._update_eingabe_anzeige()

        # Status zuruecksetzen
        self.status_var.set(self._status_text())

    # -------------------------------------------------------------------------
    # Anzeige-Updates
    # -------------------------------------------------------------------------

    def _update_eingabe_anzeige(self):
        """Aktualisiert die Farben der Eingabekreise entsprechend aktuelle_eingabe."""
        for i, farbe in enumerate(self.aktuelle_eingabe):
            oid = self.eingabe_kreis_ids[i]
            if farbe is None:
                self.eingabe_canvas.itemconfig(oid, fill=LEER_FARBE, outline=LEER_RAND)
            else:
                self.eingabe_canvas.itemconfig(
                    oid, fill=FARB_HEX[farbe], outline="#ffffff"
                )

    def _markiere_aktive_zeile(self):
        """
        Hebt die naechste zu spielende Zeile hervor.
        Wir koennen den Hintergrundbalken nicht einfach aendern (Canvas-Objekte sind statisch),
        also zeichnen wir einen neuen Highlightbalken auf die naechste Zeile.
        """
        naechste = self.spiel.anzahl_versuche
        if naechste >= self.max_versuche:
            return  # Spiel vorbei, keine naechste Zeile

        y = RAND + naechste * ZEILEN_H + ZEILEN_H // 2
        x0 = RAND - 8
        x1 = self._canvas_breite - RAND + 8
        # Highlight-Rechteck hinter die Zeile zeichnen
        # lowered = hinter allen bestehenden Elementen
        rect_id = self.canvas.create_rectangle(
            x0, y - ZEILEN_H // 2 + 4,
            x1, y + ZEILEN_H // 2 - 4,
            fill="#1e2a3a", outline=AKZENT, width=1
        )
        self.canvas.lower(rect_id)   # hinter alle anderen Elemente schieben

        # Zeilennummer der naechsten Zeile in Akzentfarbe setzen
        # (die Zeile wurde beim Zeichnen mit grauer Nummer erstellt)
        # Da wir die Text-IDs nicht einzeln gespeichert haben, zeichnen wir
        # einen neuen Text darueber
        self.canvas.create_text(
            RAND - 4, y,
            text=str(naechste + 1),
            fill=AKZENT,
            font=("Segoe UI", 9),
            anchor="e"
        )

    def _status_text(self):
        """Gibt den aktuellen Statustext zurueck."""
        if self.spiel.gewonnen:
            return f"Gewonnen in {self.spiel.anzahl_versuche} Versuch(en)!"
        if self.spiel.ist_beendet:
            return "Nicht geschafft -- Neues Spiel?"
        verbleibend = self.spiel.versuche_uebrig
        return f"Versuch {self.spiel.anzahl_versuche + 1} von {self.max_versuche}  |  {verbleibend} uebrig"

    def _zeige_spielende(self):
        """Zeigt eine Meldung am Spielende und veraet den Geheimcode bei Niederlage."""
        if self.spiel.gewonnen:
            messagebox.showinfo(
                "Gewonnen!",
                f"Glueckwunsch!\nErraten in {self.spiel.anzahl_versuche} Versuch(en)."
            )
        else:
            # Geheimcode verraten
            code_text = "  ".join(f.capitalize() for f in self.spiel.geheimcode)
            messagebox.showinfo(
                "Verloren",
                f"Leider nicht geschafft.\n\nDer Geheimcode war:\n{code_text}"
            )


# =============================================================================
# 5. Einstiegspunkt
# =============================================================================

def main():
    root = tk.Tk()

    # Fenstermindestgroesse -- verhindert dass Widgets abgeschnitten werden
    root.minsize(400, 600)

    app = MastermindApp(root)

    # Fenster in Bildschirmmitte positionieren
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth()  // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()
