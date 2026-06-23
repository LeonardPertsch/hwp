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


ROWS = [
    ("Befehlsanfang", "", "0x02", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "0x03", "", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("LXI SP, 0x00", "", "", "1", "1", "", "0x02", "0x31", "", "", "", "", "", "", ""),
    ("(0x31 0x00)", "", "", "0", "0", "", "", "", "0x31", "", "", "", "", "", ""),
    ("Adresse: 0x02, 0x03", "", "0x03", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "0x04", "", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "", "", "1", "1", "", "0x03", "0x00", "", "", "", "", "", "", ""),
    ("", "", "", "0", "0", "", "", "", "0x00", "", "", "", "", "", ""),
    ("Befehlsende", "", "", "", "", "", "", "", "", "", "0x00", "", "", "", ""),
    ("Befehlsanfang", "", "0x04", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "0x05", "", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("MVI A, 0x76", "", "", "1", "1", "", "0x04", "0x3E", "", "", "", "", "", "", ""),
    ("(0x3E 0x76)", "", "", "0", "0", "", "", "", "0x3E", "", "", "", "", "", ""),
    ("Adresse: 0x04, 0x05", "", "0x05", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "0x06", "", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "", "", "1", "1", "", "0x05", "0x76", "", "", "", "", "", "", ""),
    ("", "", "", "0", "0", "", "", "", "0x76", "", "", "", "", "", ""),
    ("Befehlsende", "", "", "", "", "", "", "", "", "", "", "0x76", "", "", ""),
    ("Befehlsanfang", "", "0x06", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "0x07", "", "", "", "", "", "", "", "", "", "", "", "", ""),

    ("PUSH A", "", "", "1", "1", "", "0x06", "0xF5", "", "", "", "", "", "", ""),
    ("(0xF5)", "", "", "0", "0", "", "", "", "0xF5", "", "", "", "", "", ""),
    ("Adresse: 0x06", "", "", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "", "", "", "", "", "", "", "", "", "0xFF", "", "", "", ""),
    ("", "", "0xFF", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "", "", "", "", "", "", "", "0x76", "", "", "", "", "", ""),
    ("Befehlsende", "", "", "1", "", "1", "0xFF", "0x76", "", "", "", "", "", "", ""),
    ("Befehlsanfang", "", "0x07", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "0x08", "", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("JUMP @P(0x06)", "", "", "1", "1", "", "0x07", "0xC3", "", "", "", "", "", "", ""),
    ("(0xC3 0x06)", "", "", "0", "0", "", "", "", "0xC3", "", "", "", "", "", ""),
    ("Adresse: 0x07, 0x08", "", "0x08", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "0x09", "", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "", "", "1", "1", "", "0x08", "0x06", "", "", "", "", "", "", ""),
    ("", "", "", "0", "0", "", "", "", "0x06", "", "", "", "", "", ""),
    ("Befehlsende", "0x06", "", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("Befehlsanfang", "", "0x06", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "0x07", "", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("PUSH A", "", "", "1", "1", "", "0x06", "0xF5", "", "", "", "", "", "", ""),
    ("(0xF5)", "", "", "0", "0", "", "", "", "0xF5", "", "", "", "", "", ""),
    ("Adresse: 0x06", "", "", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "", "", "", "", "", "", "", "", "", "0xFE", "", "", "", ""),
    ("", "", "0xFE", "", "", "", "", "", "", "", "", "", "", "", ""),
    ("", "", "", "", "", "", "", "", "0x76", "", "", "", "", "", ""),
    ("Befehlsende", "", "", "1", "", "1", "0xFE", "0x76", "", "", "", "", "", "", ""),
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