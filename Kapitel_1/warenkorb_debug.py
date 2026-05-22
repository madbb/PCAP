# warenkorb.py

def berechne_zwischensumme(artikel):
    """Summiert die Preise aller Artikel."""
    gesamt = 0
    for name, preis, menge in artikel:
        gesamt += preis * menge
    return gesamt


def berechne_rabatt(zwischensumme, rabatt_prozent):
    """Berechnet den Rabattbetrag."""
    # BUG: Hier steckt der Fehler
    return zwischensumme / 100 * rabatt_prozent


def berechne_steuer(betrag, steuersatz=19):
    """Berechnet die Mehrwertsteuer."""
    return betrag / 100 * steuersatz


def berechne_gesamtpreis(artikel, rabatt_prozent=0):
    """Berechnet den Gesamtpreis inkl. Rabatt und MwSt."""
    zwischensumme = berechne_zwischensumme(artikel)
    rabatt        = berechne_rabatt(zwischensumme, rabatt_prozent)
    netto         = zwischensumme - rabatt
    steuer        = berechne_steuer(netto)
    gesamt        = netto + steuer
    return round(gesamt, 2)


if __name__ == '__main__':
    bestellung = [
        ('Python Buch',    29.99,  2),
        ('USB-Hub',        19.90,  1),
        ('Tastatur',       89.00,  1),
    ]

    # 10% Rabatt weil Stammkunde
    preis = berechne_gesamtpreis(bestellung, rabatt_prozent=10)
    print(f'Gesamtpreis: {preis} EUR')

    # Erwartetes Ergebnis:
    # Zwischensumme: 29.99*2 + 19.90 + 89.00 = 168.87
    # Rabatt 10%:    168.87 * 0.10 = 16.887
    # Netto:         168.87 - 16.887 = 151.983
    # MwSt 19%:      151.983 * 0.19 = 28.877
    # Gesamt:        151.983 + 28.877 = 180.86
    print(f'Erwartet:    180.87 EUR')