#!/usr/bin/env python3
"""
Schnell-Loescher fuer eine OPAL-Tabelle.

Tabbt durch die Felder und leert jedes Feld (Strg/Cmd+A -> Entf) -- so schnell
wie moeglich. Kein Inhalt wird getippt, es wird nur navigiert und geloescht.

Bedienung
---------
  1. Abhaengigkeit installieren:   pip install pynput
  2. Skript starten:               python3 hwp_3_clear.py [ANZAHL_FELDER]
                                   (ohne Angabe: 675 Felder = 45 Zeilen x 15 Spalten)
  3. Waehrend des Countdowns ins ERSTE Eingabefeld klicken
     (Spalte "Adressen", Zeile 0).
  4. Haende weg -- der Rest laeuft von allein.

Jederzeit abbrechen: ESC druecken.
"""

import sys
import time
import threading

try:
    from pynput.keyboard import Controller, Key, Listener
except ImportError:
    sys.exit("pynput fehlt. Installiere es mit:  pip install pynput")


# ---------------------------------------------------------------------------
# Einstellungen
# ---------------------------------------------------------------------------
DEFAULT_CELLS = 45 * 15   # 45 Zeilen x 15 Spalten (wie hwp_3_table.py)
STEP_DELAY    = 0.004     # Pause zwischen Feldern (Sekunden) -- ganz schnell
KEY_DELAY     = 0.002     # Pause zwischen einzelnen Tastendruecken
COUNTDOWN     = 6

# Auf macOS ist die "Alles auswaehlen"-Taste Cmd, sonst Strg.
SELECT_MOD = Key.cmd if sys.platform == "darwin" else Key.ctrl

kb = Controller()
abort = threading.Event()


def on_press(key):
    if key == Key.esc:
        abort.set()
        return False


def check_abort():
    if abort.is_set():
        print("\nAbgebrochen.")
        sys.exit(0)


def tap(key):
    check_abort()
    kb.press(key)
    kb.release(key)
    time.sleep(KEY_DELAY)


def clear_field():
    # Alles im Feld markieren ...
    check_abort()
    kb.press(SELECT_MOD)
    kb.press('a')
    kb.release('a')
    kb.release(SELECT_MOD)
    time.sleep(KEY_DELAY)
    # ... und loeschen.
    tap(Key.delete)


def main():
    try:
        cells = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CELLS
    except ValueError:
        sys.exit("Ungueltige Anzahl. Beispiel:  python3 hwp_3_clear.py 675")

    Listener(on_press=on_press).start()

    print(f"Klicke jetzt ins erste Feld (Adressen, Zeile 0). Start in {COUNTDOWN}s ...")
    for s in range(COUNTDOWN, 0, -1):
        if abort.is_set():
            sys.exit(0)
        print(f"  {s} ...", end="\r", flush=True)
        time.sleep(1)

    print(f"Los!  Loesche {cells} Felder ...  (ESC zum Abbrechen)        ")

    for i in range(1, cells + 1):
        clear_field()
        if i < cells:                 # nach dem letzten Feld kein Tab mehr
            tap(Key.tab)
        time.sleep(STEP_DELAY)
        if i % 15 == 0:
            print(f"  {i}/{cells} geleert        ", end="\r", flush=True)

    print("\nFertig. Tabelle geleert.")


if __name__ == "__main__":
    main()
