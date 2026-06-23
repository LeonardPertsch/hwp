#!/usr/bin/env python3
"""
Auto-Eintipper fuer die FIBONACCI-Tabelle in OPAL.

Tippt die 50 Zeilen (Adressen / Mnemonik / HEX / Kommentar) menschlich-zoegerlich
ein. Zwischen Spalten UND am Zeilenende wird per TAB navigiert.

Bedienung
---------
  1. Abhaengigkeit installieren:   pip install pynput
  2. Skript starten:               python3 opal_fibonacci_autotype.py
  3. Waehrend des Countdowns ins ERSTE Eingabefeld klicken
     (Spalte "Adressen", Zeile 0).
  4. Haende weg -- der Rest laeuft von allein.

Jederzeit abbrechen: ESC druecken.
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
# Daten: (Adressen, Mnemonik, HEX, Kommentar) -- genau 50 Zeilen
# Leere Mnemonik = Operand-Byte eines 2-Byte-Befehls.
# ---------------------------------------------------------------------------
ROWS = [
    ("0x00", "LXI SP,0xFF", "31", "Stackpointer initialisieren"),
    ("0x01", "",            "FF", "Operand: Stackstart 0xFF"),

    ("0x02", "LDA 0x80",    "3A", "A <- n laden"),
    ("0x03", "",            "80", "Operand: Adresse 0x80"),

    ("0x04", "CALL 0x07",   "CD", "FIB(n) aufrufen"),
    ("0x05", "",            "07", "Operand: Adresse FIB"),

    ("0x06", "HLT",         "76", "Ende: Ergebnis liegt in A"),

    ("0x07", "CPI 0x02",    "FE", "FIB: n mit 2 vergleichen"),
    ("0x08", "",            "02", "Operand: Konstante 2"),

    ("0x09", "JC 0x18",     "DA", "wenn n < 2 -> direkt RET"),
    ("0x0A", "",            "18", "Operand: Sprungziel 0x18"),

    ("0x0B", "PUSH A",      "F5", "n sichern"),
    ("0x0C", "DCR A",       "3D", "A <- n-1"),

    ("0x0D", "CALL 0x07",   "CD", "FIB(n-1) berechnen"),
    ("0x0E", "",            "07", "Operand: Adresse FIB"),

    ("0x0F", "POP L",       "E1", "urspruengliches n nach L holen"),
    ("0x10", "PUSH A",      "F5", "FIB(n-1) sichern"),

    ("0x11", "MOV A,L",     "7D", "A <- urspruengliches n"),
    ("0x12", "DCR A",       "3D", "A <- n-1"),
    ("0x13", "DCR A",       "3D", "A <- n-2"),

    ("0x14", "CALL 0x07",   "CD", "FIB(n-2) berechnen"),
    ("0x15", "",            "07", "Operand: Adresse FIB"),

    ("0x16", "POP L",       "E1", "FIB(n-1) nach L holen"),
    ("0x17", "ADD L",       "85", "A <- FIB(n-2) + FIB(n-1)"),

    ("0x18", "RET",         "C9", "Rueckkehr aus FIB"),

    ("0x19", "NOP",         "00", "frei"),
    ("0x1A", "NOP",         "00", "frei"),
    ("0x1B", "NOP",         "00", "frei"),
    ("0x1C", "NOP",         "00", "frei"),
    ("0x1D", "NOP",         "00", "frei"),
    ("0x1E", "NOP",         "00", "frei"),
    ("0x1F", "NOP",         "00", "frei"),
    ("0x20", "NOP",         "00", "frei"),
    ("0x21", "NOP",         "00", "frei"),
    ("0x22", "NOP",         "00", "frei"),
    ("0x23", "NOP",         "00", "frei"),
    ("0x24", "NOP",         "00", "frei"),
    ("0x25", "NOP",         "00", "frei"),
    ("0x26", "NOP",         "00", "frei"),
    ("0x27", "NOP",         "00", "frei"),
    ("0x28", "NOP",         "00", "frei"),
    ("0x29", "NOP",         "00", "frei"),
    ("0x2A", "NOP",         "00", "frei"),
    ("0x2B", "NOP",         "00", "frei"),
    ("0x2C", "NOP",         "00", "frei"),
    ("0x2D", "NOP",         "00", "frei"),
    ("0x2E", "NOP",         "00", "frei"),
    ("0x2F", "NOP",         "00", "frei"),
    ("0x30", "NOP",         "00", "frei"),
    ("0x31", "NOP",         "00", "frei"),
]


# ---------------------------------------------------------------------------
# Timing -- hier die "Menschlichkeit" einstellen
# ---------------------------------------------------------------------------
CHAR_DELAY   = (0.0125, 0.08)
TAB_DELAY    = (0.075, 0.15)
ROW_DELAY    = (0.10, 0.30)
THINK_CHANCE = 0.02
THINK_DELAY  = (0.05, 0.25)
COUNTDOWN    = 6
FINAL_TAB    = False

kb = Controller()
abort = threading.Event()


def on_press(key):
    if key == Key.esc:
        abort.set()
        return False


def rnd(rng):
    return random.uniform(*rng)


def sleep_abortable(seconds):
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