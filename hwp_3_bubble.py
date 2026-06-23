#!/usr/bin/env python3
"""
Auto-Eintipper fuer die BUBBLESORT-Tabelle in OPAL.

Tippt die 50 Zeilen (Adressen / Mnemonik / HEX / Kommentar) menschlich-zoegerlich
ein. Zwischen Spalten UND am Zeilenende wird per TAB navigiert -- nach dem
Kommentar-Feld landet der Fokus also automatisch im Adressen-Feld der naechsten
Zeile.

Bedienung
---------
  1. Abhaengigkeit installieren:   pip install pynput
  2. Skript starten:               python3 opal_autotype.py
  3. Waehrend des Countdowns ins ERSTE Eingabefeld klicken
     (Spalte "Adressen", Zeile 0).
  4. Haende weg -- der Rest laeuft von allein.

Jederzeit abbrechen:  ESC druecken.

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
# Daten: (Adressen, Mnemonik, HEX, Kommentar)  -- genau 50 Zeilen (0x00..0x31)
# Leere Mnemonik = Operand-Byte eines 2-Byte-Befehls.
# ---------------------------------------------------------------------------
ROWS = [
    ("0x00", "LDA 0x80",   "3A", "A <- n (Anzahl der Elemente laden)"),
    ("0x01", "",           "80", "Operand: Adresse 0x80"),
    ("0x02", "CPI 0x02",   "FE", "n mit 2 vergleichen"),
    ("0x03", "",           "02", "Operand: Konstante 2"),
    ("0x04", "JC 0x31",    "DA", "n < 2 -> Sprung zu HLT"),
    ("0x05", "",           "31", "Operand: Sprungziel 0x31"),
    ("0x06", "DCR A",      "3D", "A <- n-1"),
    ("0x07", "STA 0x42",   "32", "OUTER <- n-1"),
    ("0x08", "",           "42", "Operand: Adresse 0x42 (OUTER)"),
    ("0x09", "STA 0x41",   "32", "CNT <- n-1"),
    ("0x0A", "",           "41", "Operand: Adresse 0x41 (CNT)"),
    ("0x0B", "MVI L,0x81", "2E", "L <- Adresse A[0]"),
    ("0x0C", "",           "81", "Operand: Konstante 0x81"),
    ("0x0D", "MOV A,M",    "7E", "inner: A <- A[k]"),
    ("0x0E", "INR L",      "2C", "L <- k+1"),
    ("0x0F", "CMP M",      "BE", "A[k] - A[k+1] (setzt nur Flags)"),
    ("0x10", "JC 0x1D",    "DA", "A[k] < A[k+1] -> kein Tausch"),
    ("0x11", "",           "1D", "Operand: Sprungziel 0x1D"),
    ("0x12", "JZ 0x1D",    "CA", "gleich -> kein Tausch (stabil)"),
    ("0x13", "",           "1D", "Operand: Sprungziel 0x1D"),
    ("0x14", "STA 0x40",   "32", "TMP <- A[k]"),
    ("0x15", "",           "40", "Operand: Adresse 0x40 (TMP)"),
    ("0x16", "MOV A,M",    "7E", "A <- A[k+1]"),
    ("0x17", "DCR L",      "2D", "L <- k"),
    ("0x18", "MOV M,A",    "77", "A[k] <- A[k+1]"),
    ("0x19", "INR L",      "2C", "L <- k+1"),
    ("0x1A", "LDA 0x40",   "3A", "A <- altes A[k]"),
    ("0x1B", "",           "40", "Operand: Adresse 0x40 (TMP)"),
    ("0x1C", "MOV M,A",    "77", "A[k+1] <- altes A[k]"),
    ("0x1D", "LDA 0x41",   "3A", "noswap: A <- CNT"),
    ("0x1E", "",           "41", "Operand: Adresse 0x41 (CNT)"),
    ("0x1F", "DCR A",      "3D", "CNT - 1"),
    ("0x20", "STA 0x41",   "32", "CNT speichern"),
    ("0x21", "",           "41", "Operand: Adresse 0x41 (CNT)"),
    ("0x22", "JNZ 0x0D",   "C2", "noch Paare uebrig -> inner"),
    ("0x23", "",           "0D", "Operand: Sprungziel 0x0D"),
    ("0x24", "LDA 0x42",   "3A", "A <- OUTER"),
    ("0x25", "",           "42", "Operand: Adresse 0x42 (OUTER)"),
    ("0x26", "DCR A",      "3D", "OUTER - 1"),
    ("0x27", "STA 0x42",   "32", "OUTER speichern"),
    ("0x28", "",           "42", "Operand: Adresse 0x42 (OUTER)"),
    ("0x29", "JZ 0x31",    "CA", "OUTER = 0 -> sortiert"),
    ("0x2A", "",           "31", "Operand: Sprungziel 0x31"),
    ("0x2B", "STA 0x41",   "32", "CNT <- OUTER"),
    ("0x2C", "",           "41", "Operand: Adresse 0x41 (CNT)"),
    ("0x2D", "MVI L,0x81", "2E", "L <- Adresse A[0]"),
    ("0x2E", "",           "81", "Operand: Konstante 0x81"),
    ("0x2F", "JMP 0x0D",   "C3", "naechster Durchlauf -> inner"),
    ("0x30", "",           "0D", "Operand: Sprungziel 0x0D"),
    ("0x31", "HLT",        "76", "done: Halt"),
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