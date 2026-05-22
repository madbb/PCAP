# =============================================================================
# mastermind/test.py
#
# Tests fuer die Kernlogik -- ausfuehren mit: python test.py
# Kein pytest noetig, laeuft mit der eingebauten unittest-Bibliothek.
# =============================================================================

import unittest
from logik import bewerte, erzeuge_code, normalisiere_eingabe, Spiel, FARBEN


class TestBewertung(unittest.TestCase):
    """
    Testet die bewerte()-Funktion gruendlich.
    Besonders die Randfaelle mit Wiederholungen -- das ist die fehleranfaelligste Stelle.
    """

    def test_alles_richtig(self):
        # Perfekter Versuch: 4 schwarz, 0 weiss
        self.assertEqual(bewerte(["r","b","g","y"], ["r","b","g","y"]), (4, 0))

    def test_alles_falsch(self):
        # Keine Uebereinstimmung
        self.assertEqual(bewerte(["r","r","r","r"], ["b","b","b","b"]), (0, 0))

    def test_richtige_farben_falsche_positionen(self):
        # Alle Farben enthalten aber alle verschoben
        self.assertEqual(bewerte(["r","b","g","y"], ["b","g","y","r"]), (0, 4))

    def test_gemischt(self):
        # Code: r b r g | Versuch: r r b y
        # Schwarz-Phase:
        #   Pos 0: r == r -> schwarz, verbraucht
        #   Pos 1, 2, 3: keine weiteren exakten Treffer
        # Weiss-Phase (code_rest = [None, b, r, g], versuch_rest = [None, r, b, y]):
        #   r -> code_rest enthaelt noch r (Pos 2) -> weiss, Pos 2 verbraucht
        #   b -> code_rest enthaelt noch b (Pos 1) -> weiss, Pos 1 verbraucht
        #   y -> nicht im restlichen Code
        # Ergebnis: schwarz=1, weiss=2
        # (Der Code hat zweimal r -- deshalb zaehlt das r im Versuch an Pos 1 als weiss)
        self.assertEqual(bewerte(["r","b","r","g"], ["r","r","b","y"]), (1, 2))

    def test_wiederholungen_im_code(self):
        # Code hat 2x r, Versuch hat 4x r -- nur 2 zaehlen
        self.assertEqual(bewerte(["r","r","b","g"], ["r","r","r","r"]), (2, 0))

    def test_wiederholungen_im_versuch(self):
        # Code hat 1x r, Versuch hat 4x r -- nur 1 zaehlt
        self.assertEqual(bewerte(["r","b","g","y"], ["r","r","r","r"]), (1, 0))

    def test_weiss_nicht_doppelt(self):
        # Wichtig: schwarz darf nicht nochmal als weiss zaehlen
        # Code: r b g y | Versuch: r y g b
        # Position 0: r == r -> schwarz
        # Position 2: g == g -> schwarz
        # Position 1: y != b, aber y in restlichem Code -> weiss
        # Position 3: b != y, aber b in restlichem Code -> weiss
        self.assertEqual(bewerte(["r","b","g","y"], ["r","y","g","b"]), (2, 2))

    def test_laenge_zwei(self):
        # Funktioniert auch mit anderen Laengen
        self.assertEqual(bewerte(["r","b"], ["b","r"]), (0, 2))
        self.assertEqual(bewerte(["r","b"], ["r","b"]), (2, 0))

    def test_nur_weiss(self):
        self.assertEqual(bewerte(["r","b","g","y"], ["y","r","b","g"]), (0, 4))


class TestErzeugeCode(unittest.TestCase):

    def test_laenge(self):
        code = erzeuge_code(laenge=4)
        self.assertEqual(len(code), 4)

    def test_nur_gueltige_farben(self):
        code = erzeuge_code()
        for farbe in code:
            self.assertIn(farbe, FARBEN)

    def test_reproduzierbar_mit_seed(self):
        code_a = erzeuge_code(seed=42)
        code_b = erzeuge_code(seed=42)
        self.assertEqual(code_a, code_b)

    def test_verschiedene_seeds_unterschiedlich(self):
        code_a = erzeuge_code(seed=1)
        code_b = erzeuge_code(seed=2)
        # Mit sehr hoher Wahrscheinlichkeit unterschiedlich
        # (Restwahrscheinlichkeit von Gleichheit ist 1/6^4 = 1/1296)
        self.assertNotEqual(code_a, code_b)


class TestNormalisiere(unittest.TestCase):

    def test_vollstaendige_namen(self):
        self.assertEqual(
            normalisiere_eingabe("rot blau gruen gelb"),
            ["rot", "blau", "gruen", "gelb"]
        )

    def test_abkuerzungen(self):
        self.assertEqual(
            normalisiere_eingabe("r b g ge"),
            ["rot", "blau", "gruen", "gelb"]
        )

    def test_grosskleinschreibung(self):
        self.assertEqual(
            normalisiere_eingabe("ROT BLAU GRUEN GELB"),
            ["rot", "blau", "gruen", "gelb"]
        )

    def test_zu_wenige_farben(self):
        with self.assertRaises(ValueError):
            normalisiere_eingabe("rot blau")

    def test_zu_viele_farben(self):
        with self.assertRaises(ValueError):
            normalisiere_eingabe("rot blau gruen gelb orange")

    def test_ungueltige_farbe(self):
        with self.assertRaises(ValueError):
            normalisiere_eingabe("rot blau gruen pink")


class TestSpiel(unittest.TestCase):

    def setUp(self):
        # Fixer Seed damit der Test deterministisch ist
        self.spiel = Spiel(seed=42)

    def test_start_zustand(self):
        self.assertEqual(self.spiel.anzahl_versuche, 0)
        self.assertFalse(self.spiel.ist_beendet)
        self.assertFalse(self.spiel.gewonnen)

    def test_versuch_wird_gespeichert(self):
        versuch = ["rot", "blau", "gruen", "gelb"]
        self.spiel.versuch_ausfuehren(versuch)
        self.assertEqual(self.spiel.anzahl_versuche, 1)
        self.assertEqual(self.spiel.versuche[0], versuch)

    def test_gewinn_bei_korrektem_versuch(self):
        # Geheimcode direkt einsetzen fuer deterministischen Test
        self.spiel.geheimcode = ["rot", "blau", "gruen", "gelb"]
        self.spiel.versuch_ausfuehren(["rot", "blau", "gruen", "gelb"])
        self.assertTrue(self.spiel.gewonnen)
        self.assertTrue(self.spiel.ist_beendet)

    def test_spiel_endet_nach_max_versuchen(self):
        falscher_versuch = ["orange", "orange", "orange", "orange"]
        # Sicherstellen dass der Code nicht zufaellig so ist
        self.spiel.geheimcode = ["rot", "blau", "gruen", "gelb"]
        for _ in range(self.spiel.max_versuche):
            self.spiel.versuch_ausfuehren(falscher_versuch)
        self.assertTrue(self.spiel.ist_beendet)
        self.assertFalse(self.spiel.gewonnen)

    def test_kein_versuch_nach_spielende(self):
        self.spiel.geheimcode = ["rot", "blau", "gruen", "gelb"]
        self.spiel.versuch_ausfuehren(["rot", "blau", "gruen", "gelb"])
        with self.assertRaises(RuntimeError):
            self.spiel.versuch_ausfuehren(["rot", "blau", "gruen", "gelb"])

    def test_verlauf_struktur(self):
        versuch = ["rot", "blau", "gruen", "gelb"]
        self.spiel.versuch_ausfuehren(versuch)
        verlauf = self.spiel.verlauf()
        self.assertEqual(len(verlauf), 1)
        eintrag = verlauf[0]
        self.assertIn("nr",      eintrag)
        self.assertIn("versuch", eintrag)
        self.assertIn("schwarz", eintrag)
        self.assertIn("weiss",   eintrag)


if __name__ == "__main__":
    # Ausfuehren mit: python test.py
    # Gibt detaillierte Ausgabe mit -v: python test.py -v
    unittest.main(verbosity=2)
