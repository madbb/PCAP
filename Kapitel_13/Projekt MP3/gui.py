# =============================================================================
# mp3_verwaltung/gui.py
#
# Grafische Oberflaeche fuer die MP3-Verwaltung.
# Starten mit: python gui.py
#
# Aufbau:
#   1. Design-Konstanten
#   2. ScanDialog  -- Fortschrittsfenster beim Scannen
#   3. StatistikFenster -- zeigt Bibliotheksstatistiken
#   4. MP3App -- das Hauptfenster
#   5. main()
#
# Abhaengigkeiten: modell.py, scanner.py (beide im selben Ordner)
# pip install mutagen
# =============================================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path

from modell import Bibliothek, Song
from scanner import scanne_verzeichnis


# =============================================================================
# 1. Design-Konstanten
# =============================================================================

BG        = "#12121f"     # Haupthintergrund
BG_PANEL  = "#1a1a2e"     # Seitenleiste / Panels
BG_ENTRY  = "#0f0f1e"     # Eingabefelder
AKZENT    = "#4fc3f7"     # Hauptakzentfarbe
TXT       = "#e8eaf6"     # Haupttextfarbe
TXT_GRAU  = "#7a7a90"     # gedaempfter Text
TXT_GRUEN = "#81c784"     # Erfolg / Bestaetigung
TXT_ROT   = "#ef9a9a"     # Fehler / Warnung
AUSWAHL   = "#1e3a5a"     # selektierte Zeile im Treeview

FONT_NORMAL = ("Segoe UI", 10)
FONT_KLEIN  = ("Segoe UI", 9)
FONT_BOLD   = ("Segoe UI", 10, "bold")
FONT_TITEL  = ("Segoe UI", 14, "bold")

# Treeview-Spalten: (id, anzeigetext, breite, ausrichtung)
SPALTEN = [
    ("titel",     "Titel",     280, "w"),
    ("interpret", "Interpret", 160, "w"),
    ("album",     "Album",     160, "w"),
    ("jahr",      "Jahr",       55, "center"),
    ("dauer",     "Dauer",      55, "center"),
]

# Pfad fuer die gespeicherte Bibliothek (neben gui.py)
BIBLIOTHEK_DATEI = Path(__file__).parent / "bibliothek.json"


# =============================================================================
# 2. ScanDialog -- Fortschrittsfenster waehrend des Scannens
# =============================================================================

class ScanDialog(tk.Toplevel):
    """
    Modales Fenster das den Scan-Fortschritt anzeigt.

    Da der Scan in einem eigenen Thread laeuft (damit die GUI nicht einfriert),
    kommuniziert der Scan-Thread ueber die Methode aktualisieren() mit diesem
    Fenster. tkinter ist nicht thread-safe -- deshalb nutzen wir after() um
    Updates in den Haupt-Thread zu delegieren.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Verzeichnis wird gescannt...")
        self.configure(bg=BG)
        self.resizable(False, False)

        # Verhindert Interaktion mit dem Hauptfenster waehrend des Scans
        self.grab_set()
        self.transient(parent)

        # Fortschrittsanzeige
        tk.Label(self, text="Scanne MP3-Dateien...",
                 bg=BG, fg=TXT, font=FONT_BOLD, pady=12).pack()

        self._datei_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self._datei_var,
                 bg=BG, fg=TXT_GRAU, font=FONT_KLEIN,
                 width=50, anchor="w", padx=20).pack()

        self._fortschritt = ttk.Progressbar(
            self, mode="determinate", length=400
        )
        self._fortschritt.pack(padx=20, pady=8)

        self._zaehler_var = tk.StringVar(value="0 / 0")
        tk.Label(self, textvariable=self._zaehler_var,
                 bg=BG, fg=TXT_GRAU, font=FONT_KLEIN).pack(pady=(0, 12))

        # Fenster zentrieren
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  // 2) - 220
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 60
        self.geometry(f"+{x}+{y}")

    def aktualisieren(self, aktuell: int, gesamt: int, dateiname: str):
        """
        Aktualisiert die Anzeige. Wird aus dem Scan-Thread ueber after() aufgerufen.
        """
        self._datei_var.set(dateiname[:60] + "..." if len(dateiname) > 60 else dateiname)
        self._zaehler_var.set(f"{aktuell} / {gesamt}")
        if gesamt > 0:
            self._fortschritt["value"] = (aktuell / gesamt) * 100
        self.update_idletasks()


# =============================================================================
# 3. StatistikFenster
# =============================================================================

class StatistikFenster(tk.Toplevel):
    """Zeigt Bibliotheksstatistiken in einem separaten Fenster."""

    def __init__(self, parent, bibliothek: Bibliothek):
        super().__init__(parent)
        self.title("Bibliothek-Statistiken")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)

        stats = bibliothek.statistiken()

        tk.Label(self, text="Bibliothek-Statistiken",
                 bg=BG, fg=AKZENT, font=FONT_TITEL, pady=16).pack()

        # Eintraege als Label-Paare
        daten = [
            ("Songs gesamt",     str(stats["anzahl_songs"])),
            ("Gesamtdauer",      stats["gesamtdauer_str"]),
            ("Interpreten",      str(stats["interpreten"])),
            ("Alben",            str(stats["alben"])),
            ("Ohne Metadaten",   str(stats["ohne_metadaten"])),
            ("Duplikate",        str(len(bibliothek.duplikate()))),
        ]

        rahmen = tk.Frame(self, bg=BG_PANEL, padx=30, pady=16)
        rahmen.pack(padx=20, pady=(0, 16))

        for bezeichnung, wert in daten:
            zeile = tk.Frame(rahmen, bg=BG_PANEL)
            zeile.pack(fill="x", pady=3)
            tk.Label(zeile, text=bezeichnung + ":",
                     bg=BG_PANEL, fg=TXT_GRAU, font=FONT_NORMAL,
                     width=18, anchor="w").pack(side="left")
            tk.Label(zeile, text=wert,
                     bg=BG_PANEL, fg=TXT, font=FONT_BOLD,
                     anchor="w").pack(side="left")

        tk.Button(self, text="Schliessen",
                  command=self.destroy,
                  bg=BG_PANEL, fg=TXT, font=FONT_NORMAL,
                  relief="flat", padx=14, pady=6).pack(pady=(0, 16))

        # Zentrieren
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  // 2) - (self.winfo_width()  // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")


# =============================================================================
# 4. MP3App -- das Hauptfenster
# =============================================================================

class MP3App:
    """
    Hauptfenster der MP3-Verwaltung.

    Aufbau des Fensters:
        [Toolbar: Scan | Laden | Speichern | Statistiken | Export]
        [Suchleiste]
        [Treeview: Songliste -- fuellt den Rest]
        [Statusleiste]

    Die Bibliothek (modell.Bibliothek) ist das einzige Datenobjekt.
    Die GUI liest daraus und schreibt zurueck -- nie direkt auf Songs.
    """

    def __init__(self, root: tk.Tk):
        self.root        = root
        self.bibliothek  = Bibliothek()
        self._sortiert_nach     = "interpret"
        self._sortiert_absteigend = False

        self._baue_ui()
        self._lade_beim_start()

    # -------------------------------------------------------------------------
    # UI aufbauen
    # -------------------------------------------------------------------------

    def _baue_ui(self):
        self.root.title("MP3-Verwaltung")
        self.root.configure(bg=BG)
        self.root.minsize(820, 500)

        # ttk-Style anpassen -- Treeview bekommt das dunkle Design
        self._konfiguriere_style()

        # Toolbar
        self._baue_toolbar()

        # Suchleiste
        self._baue_suchleiste()

        # Hauptbereich: Songliste
        self._baue_songliste()

        # Statusleiste
        self._baue_statusleiste()

    def _konfiguriere_style(self):
        """Passt den ttk-Style fuer den Treeview an das dunkle Design an."""
        style = ttk.Style()

        # Hintergrund des Treeview
        style.configure("Treeview",
            background=BG_PANEL,
            foreground=TXT,
            fieldbackground=BG_PANEL,
            rowheight=24,
            font=FONT_KLEIN,
            borderwidth=0,
        )
        style.configure("Treeview.Heading",
            background=BG,
            foreground=AKZENT,
            font=FONT_BOLD,
            relief="flat",
        )
        # Selektierte Zeile
        style.map("Treeview",
            background=[("selected", AUSWAHL)],
            foreground=[("selected", TXT)],
        )
        # Scrollbar
        style.configure("Vertical.TScrollbar",
            background=BG_PANEL,
            troughcolor=BG,
            arrowcolor=TXT_GRAU,
        )

    def _baue_toolbar(self):
        """Obere Leiste mit allen Aktions-Buttons."""
        toolbar = tk.Frame(self.root, bg=BG, pady=8)
        toolbar.pack(fill="x", padx=12)

        def btn(text, cmd, farbe=AKZENT):
            return tk.Button(
                toolbar, text=text, command=cmd,
                bg=BG_PANEL, fg=farbe,
                font=FONT_NORMAL, relief="flat",
                padx=12, pady=5, cursor="hand2",
                activebackground=BG_ENTRY,
            )

        btn("Verzeichnis scannen",  self._scan_starten).pack(side="left", padx=(0, 4))
        btn("Bibliothek laden",     self._laden).pack(side="left", padx=4)
        btn("Bibliothek speichern", self._speichern).pack(side="left", padx=4)

        # Trennlinie
        tk.Frame(toolbar, bg=TXT_GRAU, width=1).pack(side="left", fill="y", padx=8, pady=4)

        btn("Statistiken",  self._zeige_statistiken, TXT_GRAU).pack(side="left", padx=4)
        btn("Als CSV exportieren", self._exportieren_csv, TXT_GRAU).pack(side="left", padx=4)

        # Veraltete Eintraege pruefen (rechts in der Toolbar)
        btn("Fehlende entfernen", self._fehlende_entfernen, TXT_ROT).pack(side="right", padx=4)

    def _baue_suchleiste(self):
        """Suchfeld unterhalb der Toolbar."""
        such_rahmen = tk.Frame(self.root, bg=BG, pady=4)
        such_rahmen.pack(fill="x", padx=12)

        tk.Label(such_rahmen, text="Suche:",
                 bg=BG, fg=TXT_GRAU, font=FONT_NORMAL).pack(side="left", padx=(0, 6))

        self._such_var = tk.StringVar()
        # Suche wird bei jeder Aenderung ausgeloest -- kein Enter noetig
        self._such_var.trace_add("write", lambda *_: self._suche_aktualisieren())

        such_feld = tk.Entry(
            such_rahmen,
            textvariable=self._such_var,
            bg=BG_ENTRY, fg=TXT,
            insertbackground=AKZENT,
            font=FONT_NORMAL,
            relief="flat",
            width=40,
        )
        such_feld.pack(side="left", ipady=4, padx=(0, 8))

        # Sortieroptionen
        tk.Label(such_rahmen, text="Sortieren:",
                 bg=BG, fg=TXT_GRAU, font=FONT_NORMAL).pack(side="left", padx=(8, 4))

        self._sort_var = tk.StringVar(value="interpret")
        sort_optionen = ["titel", "interpret", "album", "jahr", "dauer"]

        sort_menu = ttk.Combobox(
            such_rahmen,
            textvariable=self._sort_var,
            values=sort_optionen,
            state="readonly",
            width=10,
            font=FONT_NORMAL,
        )
        sort_menu.pack(side="left", padx=(0, 4))
        sort_menu.bind("<<ComboboxSelected>>", lambda _: self._liste_aktualisieren())

        # Auf-/Absteigend
        self._absteigend_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            such_rahmen,
            text="absteigend",
            variable=self._absteigend_var,
            command=self._liste_aktualisieren,
            bg=BG, fg=TXT_GRAU,
            selectcolor=BG_PANEL,
            activebackground=BG,
            font=FONT_KLEIN,
        ).pack(side="left")

    def _baue_songliste(self):
        """Hauptbereich: Treeview mit Scrollbar."""
        rahmen = tk.Frame(self.root, bg=BG)
        rahmen.pack(fill="both", expand=True, padx=12, pady=(4, 0))

        # Scrollbar
        scrollbar = ttk.Scrollbar(rahmen, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        # Treeview
        spalten_ids = [s[0] for s in SPALTEN]
        self.tree = ttk.Treeview(
            rahmen,
            columns=spalten_ids,
            show="headings",           # keine Icon-Spalte
            yscrollcommand=scrollbar.set,
            selectmode="browse",       # immer genau eine Zeile ausgewaehlt
        )
        self.tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)

        # Spalten konfigurieren
        for spalten_id, anzeigetext, breite, ausrichtung in SPALTEN:
            self.tree.heading(
                spalten_id,
                text=anzeigetext,
                # Klick auf Spaltenheader sortiert nach dieser Spalte
                command=lambda s=spalten_id: self._spalte_sortieren(s),
            )
            self.tree.column(spalten_id, width=breite, anchor=ausrichtung, minwidth=40)

        # Doppelklick zeigt Details
        self.tree.bind("<Double-1>", self._zeige_details)

        # Abwechselnde Zeilenfarben fuer bessere Lesbarkeit
        self.tree.tag_configure("gerade",   background=BG_PANEL)
        self.tree.tag_configure("ungerade", background="#1e1e30")

    def _baue_statusleiste(self):
        """Unterste Leiste mit Anzahl Songs und Statusmeldungen."""
        status_rahmen = tk.Frame(self.root, bg=BG_PANEL, height=28)
        status_rahmen.pack(fill="x", side="bottom")
        status_rahmen.pack_propagate(False)

        self._status_var = tk.StringVar(value="Bereit")
        tk.Label(status_rahmen, textvariable=self._status_var,
                 bg=BG_PANEL, fg=TXT_GRAU, font=FONT_KLEIN,
                 anchor="w", padx=10).pack(side="left", fill="y")

        self._anzahl_var = tk.StringVar(value="0 Songs")
        tk.Label(status_rahmen, textvariable=self._anzahl_var,
                 bg=BG_PANEL, fg=TXT_GRAU, font=FONT_KLEIN,
                 anchor="e", padx=10).pack(side="right", fill="y")

    # -------------------------------------------------------------------------
    # Aktionen
    # -------------------------------------------------------------------------

    def _scan_starten(self):
        """
        Oeffnet einen Ordner-Auswahldialog und startet den Scan in einem
        eigenen Thread. Die GUI bleibt waehrend des Scans bedienbar.
        """
        verzeichnis = filedialog.askdirectory(
            title="MP3-Verzeichnis auswaehlen",
            mustexist=True,
        )
        if not verzeichnis:
            return   # Nutzer hat abgebrochen

        # Fortschrittsfenster oeffnen
        dialog = ScanDialog(self.root)

        def scan_thread():
            """Laeuft in einem eigenen Thread -- kein tkinter-Zugriff direkt."""

            def fortschritt(aktuell, gesamt, dateiname):
                # after() delegiert den UI-Update in den Haupt-Thread
                self.root.after(0, dialog.aktualisieren, aktuell, gesamt, dateiname)

            try:
                songs, fehler = scanne_verzeichnis(verzeichnis, fortschritt)

                # Ergebnis in den Haupt-Thread uebergeben
                self.root.after(0, self._scan_abgeschlossen, songs, fehler, dialog)

            except Exception as e:
                self.root.after(0, self._scan_fehler, str(e), dialog)

        # Thread starten (daemon=True: wird beendet wenn Hauptfenster schliesst)
        threading.Thread(target=scan_thread, daemon=True).start()

    def _scan_abgeschlossen(self, songs: list[Song], fehler: list[str], dialog: ScanDialog):
        """Wird im Haupt-Thread aufgerufen wenn der Scan fertig ist."""
        dialog.destroy()

        self.bibliothek.leeren()
        self.bibliothek.alle_hinzufuegen(songs)
        self._liste_aktualisieren()

        meldung = f"{len(songs)} Songs gefunden."
        if fehler:
            meldung += f"\n{len(fehler)} Datei(en) konnten nicht gelesen werden."

        self._status_setzen(meldung, TXT_GRUEN if not fehler else TXT_ROT)

        if fehler and messagebox.askyesno("Scan-Fehler", f"{len(fehler)} Fehler aufgetreten. Details anzeigen?"):
            messagebox.showinfo("Fehler beim Scan", "\n".join(fehler[:20]))

    def _scan_fehler(self, fehler: str, dialog: ScanDialog):
        """Wird im Haupt-Thread aufgerufen wenn der Scan mit Ausnahme abbricht."""
        dialog.destroy()
        messagebox.showerror("Scan fehlgeschlagen", fehler)

    def _laden(self):
        """Laedt eine gespeicherte Bibliothek aus einer JSON-Datei."""
        pfad = filedialog.askopenfilename(
            title="Bibliothek laden",
            filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")],
            initialfile=str(BIBLIOTHEK_DATEI),
        )
        if not pfad:
            return

        try:
            anzahl = self.bibliothek.laden(pfad)
            self._liste_aktualisieren()
            self._status_setzen(f"{anzahl} Songs geladen aus {Path(pfad).name}", TXT_GRUEN)
        except FileNotFoundError:
            messagebox.showerror("Fehler", f"Datei nicht gefunden:\n{pfad}")
        except Exception as e:
            messagebox.showerror("Fehler beim Laden", str(e))

    def _speichern(self):
        """Speichert die aktuelle Bibliothek als JSON."""
        if self.bibliothek.anzahl == 0:
            messagebox.showwarning("Nichts zu speichern", "Die Bibliothek ist leer.")
            return

        pfad = filedialog.asksaveasfilename(
            title="Bibliothek speichern",
            defaultextension=".json",
            filetypes=[("JSON-Dateien", "*.json")],
            initialfile=str(BIBLIOTHEK_DATEI),
        )
        if not pfad:
            return

        try:
            self.bibliothek.speichern(pfad)
            self._status_setzen(f"Gespeichert: {Path(pfad).name}", TXT_GRUEN)
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", str(e))

    def _lade_beim_start(self):
        """
        Versucht beim Programmstart die zuletzt gespeicherte Bibliothek zu laden.
        Wenn keine Datei existiert oder ein Fehler auftritt, wird still weitergemacht.
        """
        if BIBLIOTHEK_DATEI.exists():
            try:
                anzahl = self.bibliothek.laden(BIBLIOTHEK_DATEI)
                self._liste_aktualisieren()
                self._status_setzen(f"{anzahl} Songs aus gespeicherter Bibliothek geladen.")
            except Exception:
                pass   # fehlerhafte Datei ignorieren

    def _exportieren_csv(self):
        """Exportiert die Bibliothek als CSV-Datei."""
        if self.bibliothek.anzahl == 0:
            messagebox.showwarning("Nichts zu exportieren", "Die Bibliothek ist leer.")
            return

        pfad = filedialog.asksaveasfilename(
            title="Als CSV exportieren",
            defaultextension=".csv",
            filetypes=[("CSV-Dateien", "*.csv")],
            initialfile="bibliothek.csv",
        )
        if not pfad:
            return

        try:
            self.bibliothek.exportieren_csv(pfad)
            self._status_setzen(f"Exportiert: {Path(pfad).name}", TXT_GRUEN)
        except Exception as e:
            messagebox.showerror("Export fehlgeschlagen", str(e))

    def _fehlende_entfernen(self):
        """Entfernt Eintraege fuer Dateien die nicht mehr existieren."""
        fehlende = self.bibliothek.entferne_fehlende()
        if not fehlende:
            messagebox.showinfo("Alles aktuell", "Keine fehlenden Dateien gefunden.")
        else:
            self._liste_aktualisieren()
            messagebox.showinfo(
                "Eintraege entfernt",
                f"{len(fehlende)} Eintraege entfernt (Dateien nicht mehr vorhanden)."
            )

    def _zeige_statistiken(self):
        """Oeffnet das Statistik-Fenster."""
        if self.bibliothek.anzahl == 0:
            messagebox.showinfo("Statistiken", "Die Bibliothek ist leer.")
            return
        StatistikFenster(self.root, self.bibliothek)

    def _zeige_details(self, event):
        """Zeigt Details zum angeklickten Song in einem Popup."""
        ausgewaehlt = self.tree.selection()
        if not ausgewaehlt:
            return

        # Der iid des Treeview-Eintrags ist der Pfad des Songs
        pfad = self.tree.item(ausgewaehlt[0], "values")
        if not pfad:
            return

        # Song aus der Bibliothek suchen
        alle = self.bibliothek.alle()
        # Die Werte aus dem Treeview: (titel, interpret, album, jahr, dauer)
        # Wir identifizieren den Song anhand der Position in der angezeigten Liste
        index = self.tree.index(ausgewaehlt[0])
        suchbegriff = self._such_var.get()
        sortiert = self.bibliothek.sortieren(
            nach=self._sort_var.get(),
            absteigend=self._absteigend_var.get()
        )
        if suchbegriff:
            sortiert = [s for s in sortiert if s.enthaelt(suchbegriff)]

        if index >= len(sortiert):
            return
        song = sortiert[index]

        detail = (
            f"Titel:     {song.titel_anzeige}\n"
            f"Interpret: {song.interpret_anzeige}\n"
            f"Album:     {song.album_anzeige}\n"
            f"Jahr:      {song.jahr_anzeige}\n"
            f"Dauer:     {song.dauer_anzeige}\n"
            f"\nDatei:\n{song.pfad}"
        )
        messagebox.showinfo("Song-Details", detail)

    # -------------------------------------------------------------------------
    # Anzeige-Updates
    # -------------------------------------------------------------------------

    def _liste_aktualisieren(self):
        """
        Fuellt den Treeview mit den aktuellen Daten aus der Bibliothek.
        Beruecksichtigt den aktuellen Suchbegriff und die Sortierung.
        """
        # Alle alten Eintraege loeschen
        self.tree.delete(*self.tree.get_children())

        suchbegriff = self._such_var.get() if hasattr(self, "_such_var") else ""
        sortfeld    = self._sort_var.get() if hasattr(self, "_sort_var") else "interpret"
        absteigend  = self._absteigend_var.get() if hasattr(self, "_absteigend_var") else False

        songs = self.bibliothek.sortieren(nach=sortfeld, absteigend=absteigend)
        if suchbegriff:
            songs = [s for s in songs if s.enthaelt(suchbegriff)]

        for i, song in enumerate(songs):
            # Abwechselnde Zeilenfarben
            tag = "gerade" if i % 2 == 0 else "ungerade"
            self.tree.insert(
                "", "end",
                values=(
                    song.titel_anzeige,
                    song.interpret_anzeige,
                    song.album_anzeige,
                    song.jahr_anzeige,
                    song.dauer_anzeige,
                ),
                tags=(tag,),
            )

        # Anzahl aktualisieren
        if hasattr(self, "_anzahl_var"):
            gesamt = self.bibliothek.anzahl
            angezeigt = len(songs)
            if suchbegriff and angezeigt != gesamt:
                self._anzahl_var.set(f"{angezeigt} von {gesamt} Songs")
            else:
                self._anzahl_var.set(f"{gesamt} Songs")

    def _suche_aktualisieren(self):
        """Wird bei jeder Aenderung im Suchfeld aufgerufen."""
        self._liste_aktualisieren()

    def _spalte_sortieren(self, spalte: str):
        """
        Sortiert nach der geklickten Spalte.
        Zweiter Klick auf dieselbe Spalte kehrt die Reihenfolge um.
        """
        if self._sort_var.get() == spalte:
            # Schon nach dieser Spalte sortiert -- Richtung umkehren
            self._absteigend_var.set(not self._absteigend_var.get())
        else:
            self._sort_var.set(spalte)
            self._absteigend_var.set(False)
        self._liste_aktualisieren()

    def _status_setzen(self, text: str, farbe: str = TXT_GRAU):
        """Setzt den Statustext und seine Farbe."""
        self._status_var.set(text)
        # Label direkt ansprechen -- etwas umstaendlich aber ohne separate Referenz
        # aktualisieren wir nur den Text, die Farbe wird beim naechsten Bauen gesetzt
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and child.cget("textvariable") == str(self._status_var):
                        child.config(fg=farbe)


# =============================================================================
# 5. Einstiegspunkt
# =============================================================================

def main():
    root = tk.Tk()
    app  = MP3App(root)

    # Fenster zentrieren
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth()  // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"900x580+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()
