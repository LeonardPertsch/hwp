#!/usr/bin/env python3
"""
Auto-Eintipper fuer die MULTIPLY-Tabelle in OPAL.

Diese Version ist fuer den Fall gedacht, dass Zeile 0 in OPAL bereits vorgegeben ist:
  0x00, 0x01 | JMP 0x40 | 0xC3 0x40 | Springe zum Beginn von MULTIPLY

Start daher im ERSTEN Feld von Zeile 1.

Bedienung
---------
  1. Abhaengigkeit installieren:   pip install pynput
  2. Skript starten:               python3 hwp_3_mul.py
  3. Waehrend des Countdowns ins ERSTE Eingabefeld von Zeile 1 klicken
     (Spalte "Adressen", Zeile 1).
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
# Daten: (Adressen, Mnemonik, HEX, Kommentar)
# Zeile 0 ist in OPAL bereits vorgegeben und wird hier NICHT getippt.
# ---------------------------------------------------------------------------
ROWS = [
    ("0x40, 0x41", "MVI A,0x00", "0x3E 0x00", "A <- 0"),
    ("0x42, 0x43", "STA 0xB0",   "0x32 0xB0", "HIGH <- 0"),
    ("0x44, 0x45", "STA 0xB1",   "0x32 0xB1", "LOW <- 0"),

    ("0x46, 0x47", "LDA 0xA1",   "0x3A 0xA1", "A <- b"),
    ("0x48, 0x49", "STA 0xA2",   "0x32 0xA2", "CNT <- b"),

    ("0x4A, 0x4B", "CPI 0x00",   "0xFE 0x00", "b mit 0 vergleichen"),
    ("0x4C, 0x4D", "JZ 0x63",    "0xCA 0x63", "wenn b = 0 -> Ende"),

    ("0x4E, 0x4F", "LDA 0xB1",   "0x3A 0xB1", "LOW laden"),
    ("0x50, 0x51", "MVI L,0xA0", "0x2E 0xA0", "L <- Adresse von a"),
    ("0x52",       "ADD M",      "0x86",       "LOW <- LOW + a"),

    ("0x53, 0x54", "STA 0xB1",   "0x32 0xB1", "LOW speichern"),
    ("0x55, 0x56", "JNC 0x5C",   "0xD2 0x5C", "kein Uebertrag -> HIGH bleibt"),

    ("0x57, 0x58", "LDA 0xB0",   "0x3A 0xB0", "HIGH laden"),
    ("0x59",       "INR A",      "0x3C",       "HIGH <- HIGH + 1"),
    ("0x5A, 0x5B", "STA 0xB0",   "0x32 0xB0", "HIGH speichern"),

    ("0x5C, 0x5D", "LDA 0xA2",   "0x3A 0xA2", "CNT laden"),
    ("0x5E",       "DCR A",      "0x3D",       "CNT <- CNT - 1"),
    ("0x5F, 0x60", "STA 0xA2",   "0x32 0xA2", "CNT speichern"),

    ("0x61, 0x62", "JNZ 0x4E",   "0xC2 0x4E", "solange CNT != 0 -> weiter"),
    ("0x63",       "HLT",        "0x76",       "Ende"),
]


# ---------------------------------------------------------------------------
# Timing
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

    print(f"Klicke jetzt ins erste Feld von Zeile 1 (Adressen). Start in {COUNTDOWN}s ...")
    for s in range(COUNTDOWN, 0, -1):
        if abort.is_set():
            sys.exit(0)
        print(f"  {s} ...", end="\r", flush=True)
        time.sleep(1)

    print("Los!  (ESC zum Abbrechen)            ")

    total = len(ROWS)
    for i, row in enumerate(ROWS, start=1):
        for j, field in enumerate(row):
            human_type(field)
            is_last_field = (i == total) and (j == len(row) - 1)
            if is_last_field and not FINAL_TAB:
                continue
            press_tab()

        sleep_abortable(rnd(ROW_DELAY))
        print(f"Zeile {i:2d} fertig          ", end="\r", flush=True)

    print("\nFertig. Bitte in OPAL kontrollieren und dann speichern/abgeben.")


if __name__ == "__main__":
    main()
