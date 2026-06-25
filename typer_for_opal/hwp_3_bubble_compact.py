#!/usr/bin/env python3
"""
Auto-Eintipper fuer die BUBBLESORT-Tabelle in OPAL.

Tippt die 31 Befehlszeilen (Adressen / Mnemonik / HEX / Kommentar)
menschlich-zoegerlich ein. Jeder Befehl steht in EINER Zeile -- bei
2-Byte-Befehlen werden beide Adressen bzw. beide HEX-Bytes kombiniert
(z.B. "0x00, 0x01" / "3A, 80"). Zwischen Spalten UND am Zeilenende wird
per TAB navigiert -- nach dem Kommentar-Feld landet der Fokus also
automatisch im Adressen-Feld der naechsten Zeile.

Bedienung
---------
  1. Abhaengigkeit installieren:   pip install pynput
  2. Skript starten:               python3 opal_autotype.py
  3. Waehrend des Countdowns ins ERSTE Eingabefeld klicken
     (Spalte "Adressen", Zeile 0).
  4. Haende weg -- der Rest laeuft von allein.

Jederzeit abbrechen:  ESC druecken.

Hinweis zur Trennzeichen-Konvention
-----------------------------------
Adressen und HEX-Bytes sind hier mit ", " (Komma + Leerzeichen) getrennt,
passend zur kombinierten Darstellung aus Aufgabe 2a). Wenn dein Formular
ein anderes Trennzeichen erwartet (z.B. nur Leerzeichen "3A 80"), passe
einfach SEP unten an.

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
# 31 Befehlszeilen = 50 Bytes (0x00..0x31).
# 2-Byte-Befehle stehen in EINER Zeile, Adressen/HEX mit SEP getrennt.
# ---------------------------------------------------------------------------
ROWS = [
    ("0x00, 0x01", "LDA 0x80",   "3A, 80", "A <- n (Anzahl der Elemente laden)"),
    ("0x02, 0x03", "CPI 0x02",   "FE, 02", "n mit 2 vergleichen"),
    ("0x04, 0x05", "JC 0x31",    "DA, 31", "n < 2 -> Sprung zu HLT"),
    ("0x06",       "DCR A",      "3D",     "A <- n-1"),
    ("0x07, 0x08", "STA 0x42",   "32, 42", "OUTER <- n-1"),
    ("0x09, 0x0A", "STA 0x41",   "32, 41", "CNT <- n-1"),
    ("0x0B, 0x0C", "MVI L,0x81", "2E, 81", "L <- Adresse A[0]"),
    ("0x0D",       "MOV A,M",    "7E",     "inner: A <- A[k]"),
    ("0x0E",       "INR L",      "2C",     "L <- k+1"),
    ("0x0F",       "CMP M",      "BE",     "A[k] - A[k+1] (setzt nur Flags)"),
    ("0x10, 0x11", "JC 0x1D",    "DA, 1D", "A[k] < A[k+1] -> kein Tausch"),
    ("0x12, 0x13", "JZ 0x1D",    "CA, 1D", "gleich -> kein Tausch (stabil)"),
    ("0x14, 0x15", "STA 0x40",   "32, 40", "TMP <- A[k]"),
    ("0x16",       "MOV A,M",    "7E",     "A <- A[k+1]"),
    ("0x17",       "DCR L",      "2D",     "L <- k"),
    ("0x18",       "MOV M,A",    "77",     "A[k] <- A[k+1]"),
    ("0x19",       "INR L",      "2C",     "L <- k+1"),
    ("0x1A, 0x1B", "LDA 0x40",   "3A, 40", "A <- altes A[k]"),
    ("0x1C",       "MOV M,A",    "77",     "A[k+1] <- altes A[k]"),
    ("0x1D, 0x1E", "LDA 0x41",   "3A, 41", "noswap: A <- CNT"),
    ("0x1F",       "DCR A",      "3D",     "CNT - 1"),
    ("0x20, 0x21", "STA 0x41",   "32, 41", "CNT speichern"),
    ("0x22, 0x23", "JNZ 0x0D",   "C2, 0D", "noch Paare uebrig -> inner"),
    ("0x24, 0x25", "LDA 0x42",   "3A, 42", "A <- OUTER"),
    ("0x26",       "DCR A",      "3D",     "OUTER - 1"),
    ("0x27, 0x28", "STA 0x42",   "32, 42", "OUTER speichern"),
    ("0x29, 0x2A", "JZ 0x31",    "CA, 31", "OUTER = 0 -> sortiert"),
    ("0x2B, 0x2C", "STA 0x41",   "32, 41", "CNT <- OUTER"),
    ("0x2D, 0x2E", "MVI L,0x81", "2E, 81", "L <- Adresse A[0]"),
    ("0x2F, 0x30", "JMP 0x0D",   "C3, 0D", "naechster Durchlauf -> inner"),
    ("0x31",       "HLT",        "76",     "done: Halt"),
]

# Trennzeichen zwischen den beiden Bytes eines 2-Byte-Befehls.
# Falls dein Formular nur Leerzeichen erwartet: SEP = " "
SEP = ", "

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