#!/usr/bin/env python3
"""
Auto-Eintipper fuer die FIBONACCI-Tabelle in OPAL.

Tippt die 43 Zeilen (Adressen / Mnemonik / HEX / Kommentar) menschlich-
zoegerlich ein. Jeder Befehl steht in EINER Zeile -- bei 2-Byte-Befehlen
werden beide Adressen bzw. beide HEX-Bytes kombiniert (z.B. "0x00, 0x01" /
"31, FF"). Die 25 NOP-Fueller (0x19..0x31) sind 1-Byte-Befehle und bleiben
einzeilig. Zwischen Spalten UND am Zeilenende wird per TAB navigiert -- nach
dem Kommentar-Feld landet der Fokus also automatisch im Adressen-Feld der
naechsten Zeile.

Bedienung
---------
  1. Abhaengigkeit installieren:   pip install pynput
  2. Skript starten:               python3 opal_autotype_fib.py
  3. Waehrend des Countdowns ins ERSTE Eingabefeld klicken
     (Spalte "Adressen", Zeile 0).
  4. Haende weg -- der Rest laeuft von allein.

Jederzeit abbrechen:  ESC druecken.

Hinweis zur Trennzeichen-Konvention
-----------------------------------
Adressen und HEX-Bytes sind hier mit ", " (Komma + Leerzeichen) getrennt,
passend zur kombinierten Darstellung aus Aufgabe 2a). Wenn dein Formular
ein anderes Trennzeichen erwartet (z.B. nur Leerzeichen "31 FF"), passe
einfach die Felder unten an.

macOS-Hinweis
-------------
Dein Terminal (bzw. die Python-App) braucht die Rechte unter
  Systemeinstellungen > Datenschutz & Sicherheit > Bedienungshilfen
und ggf. zusaetzlich > Eingabeueberwachung.
Sonst passiert beim Tippen nichts.
"""

import sys
import time
import random
import threading

try:
    from pynput.keyboard import Controller, Key, Listener
except ImportError:
    sys.exit("pynput fehlt. Installiere es mit:  pip install pynput")

# ---------------------------------------------------------------------------
# Daten: (Adressen, Mnemonik, HEX, Kommentar)
# 43 Zeilen = 50 Bytes (0x00..0x31).
# 2-Byte-Befehle stehen in EINER Zeile, Adressen/HEX mit ", " getrennt.
# ---------------------------------------------------------------------------
ROWS = [
    ("0x00, 0x01", "LXI SP,0xFF", "31, FF", "Stackpointer initialisieren"),
    ("0x02, 0x03", "LDA 0x80",    "3A, 80", "A <- n laden"),
    ("0x04, 0x05", "CALL 0x07",   "CD, 07", "FIB(n) aufrufen"),
    ("0x06",       "HLT",         "76",     "Ende: Ergebnis liegt in A"),
    ("0x07, 0x08", "CPI 0x02",    "FE, 02", "FIB: n mit 2 vergleichen"),
    ("0x09, 0x0A", "JC 0x18",     "DA, 18", "wenn n < 2 -> direkt RET"),
    ("0x0B",       "PUSH A",      "F5",     "n sichern"),
    ("0x0C",       "DCR A",       "3D",     "A <- n-1"),
    ("0x0D, 0x0E", "CALL 0x07",   "CD, 07", "FIB(n-1) berechnen"),
    ("0x0F",       "POP L",       "E1",     "urspruengliches n nach L holen"),
    ("0x10",       "PUSH A",      "F5",     "FIB(n-1) sichern"),
    ("0x11",       "MOV A,L",     "7D",     "A <- urspruengliches n"),
    ("0x12",       "DCR A",       "3D",     "A <- n-1"),
    ("0x13",       "DCR A",       "3D",     "A <- n-2"),
    ("0x14, 0x15", "CALL 0x07",   "CD, 07", "FIB(n-2) berechnen"),
    ("0x16",       "POP L",       "E1",     "FIB(n-1) nach L holen"),
    ("0x17",       "ADD L",       "85",     "A <- FIB(n-2) + FIB(n-1)"),
    ("0x18",       "RET",         "C9",     "Rueckkehr aus FIB"),
    ("0x19",       "NOP",         "00",     "frei"),
    ("0x1A",       "NOP",         "00",     "frei"),
    ("0x1B",       "NOP",         "00",     "frei"),
    ("0x1C",       "NOP",         "00",     "frei"),
    ("0x1D",       "NOP",         "00",     "frei"),
    ("0x1E",       "NOP",         "00",     "frei"),
    ("0x1F",       "NOP",         "00",     "frei"),
    ("0x20",       "NOP",         "00",     "frei"),
    ("0x21",       "NOP",         "00",     "frei"),
    ("0x22",       "NOP",         "00",     "frei"),
    ("0x23",       "NOP",         "00",     "frei"),
    ("0x24",       "NOP",         "00",     "frei"),
    ("0x25",       "NOP",         "00",     "frei"),
    ("0x26",       "NOP",         "00",     "frei"),
    ("0x27",       "NOP",         "00",     "frei"),
    ("0x28",       "NOP",         "00",     "frei"),
    ("0x29",       "NOP",         "00",     "frei"),
    ("0x2A",       "NOP",         "00",     "frei"),
    ("0x2B",       "NOP",         "00",     "frei"),
    ("0x2C",       "NOP",         "00",     "frei"),
    ("0x2D",       "NOP",         "00",     "frei"),
    ("0x2E",       "NOP",         "00",     "frei"),
    ("0x2F",       "NOP",         "00",     "frei"),
    ("0x30",       "NOP",         "00",     "frei"),
    ("0x31",       "NOP",         "00",     "frei"),
]

# ---------------------------------------------------------------------------
# Timing -- hier die "Menschlichkeit" einstellen (alle Werte in Sekunden)
# ---------------------------------------------------------------------------
CHAR_DELAY   = (0.0125, 0.08)  # Pause pro getipptem Zeichen
TAB_DELAY    = (0.075, 0.15)   # Pause nach einem TAB (Spalten-/Zeilenwechsel)
ROW_DELAY    = (0.10, 0.30)    # zusaetzliche Pause am Zeilenende
THINK_CHANCE = 0.02            # Wahrscheinlichkeit fuer kurzes "Nachdenken"
THINK_DELAY  = (0.05, 0.25)    # Dauer eines solchen Nachdenkens
COUNTDOWN    = 6               # Sekunden, um ins erste Feld zu klicken
FINAL_TAB    = False           # nach dem allerletzten Feld noch TAB druecken?

kb = Controller()
abort = threading.Event()


def on_press(key):
    if key == Key.esc:
        abort.set()
        return False  # Listener beenden


def rnd(rng):
    return random.uniform(*rng)


def sleep_abortable(seconds):
    """Schlaeft in kleinen Haeppchen, damit ESC schnell greift."""
    end = time.time() + seconds
    while time.time() < end:
        if abort.is_set():
            print("\nAbgebrochen.")
            sys.exit(0)
        time.sleep(max(0.0, min(0.01, end - time.time())))


def human_type(text):
    for ch in text:
        if abort.is_set():
            print("\nAbgebrochen.")
            sys.exit(0)
        kb.type(ch)
        sleep_abortable(rnd(CHAR_DELAY))
        if random.random() < THINK_CHANCE:
            sleep_abortable(rnd(THINK_DELAY))


def press_tab():
    if abort.is_set():
        print("\nAbgebrochen.")
        sys.exit(0)
    kb.press(Key.tab)
    kb.release(Key.tab)
    sleep_abortable(rnd(TAB_DELAY))


def main():
    Listener(on_press=on_press).start()

    print(f"Klicke jetzt ins erste Feld (Adressen, Zeile 0). Start in {COUNTDOWN}s ...")
    for s in range(COUNTDOWN, 0, -1):
        if abort.is_set():
            sys.exit(0)
        print(f"  {s} ...", end="\r", flush=True)
        time.sleep(1)
    print("Los!  (ESC zum Abbrechen)            ")

    total = len(ROWS)
    for i, row in enumerate(ROWS):
        for j, field in enumerate(row):
            human_type(field)
            is_last_field = (i == total - 1) and (j == len(row) - 1)
            if is_last_field and not FINAL_TAB:
                continue
            press_tab()
        sleep_abortable(rnd(ROW_DELAY))
        print(f"Zeile {i:2d}/{total - 1} fertig          ", end="\r", flush=True)

    print("\nFertig. Bitte in OPAL kontrollieren und dann speichern/abgeben.")


if __name__ == "__main__":
    main()