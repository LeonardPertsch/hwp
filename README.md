# OPAL Auto-Typer

Eine Sammlung kleiner Python-Skripte, die ein 8085-/OPAL-Programm **automatisch in die OPAL-Tabelle eintippen** – Feld für Feld, per simulierter Tastatur. Statt 50 Zeilen × 4 Spalten von Hand abzutippen, klickst du ins erste Feld, wartest den Countdown ab und lässt das Skript den Rest machen.

> **Wichtig:** Die Skripte steuern deine echte Tastatur. Damit das funktioniert, muss dein Betriebssystem dem Python-Programm erlauben, Tastendrücke zu senden. Genau hier hakt es meistens bei anderen – siehe [Für dein OS freischalten](#für-dein-os-freischalten).

## Demo

![Auto-Typer in Aktion](ezgif-85f6aa29aac39de2.gif)

Der Typer füllt die OPAL-Tabelle Feld für Feld – während du nichts machst.

---

## Projektstruktur

```
typer/
├── typer_for_opal/        # Die eigentlichen Auto-Typer (das, was du startest)
│   ├── hwp_3_fib.py            # Fibonacci, ausführlich (jedes Byte eine Zeile)
│   ├── hwp_3_fib_compact.py    # Fibonacci, kompakt (1 Befehl = 1 Zeile)
│   ├── hwp_3_bubble.py         # Bubblesort, ausführlich
│   ├── hwp_3_bubble_compact.py # Bubblesort, kompakt
│   ├── hwp_3_mul.py            # Multiplikation (Start in Zeile 1, Zeile 0 vorgegeben)
│   ├── hwp_3_table.py          # weitere Tabellen-Variante
│   └── hwp_3_clear.py          # Leert eine OPAL-Tabelle (tabbt durch & löscht)
│
├── tabellen/              # Referenz-Material & Decoder
│   ├── decode.py              # Wandelt einen HEX-Dump in eine lesbare Befehlstabelle
│   ├── *.txt                  # Fertig dekodierte Tabellen (Adresse/HEX/Binär/Mnemonik)
│   └── Befehlssatz.pdf        # 8085-Befehlssatz als Referenz
│
└── scripts_for_editor/    # Roh-HEX-Dumps (256 Byte) als CSV, Eingabe für decode.py
    └── *.csv
```

Kurz gesagt:
- **`typer_for_opal/`** – startest du, um automatisch zu tippen.
- **`tabellen/` + `scripts_for_editor/`** – Hilfsmaterial: HEX-Dumps und ein Decoder, um nachzuvollziehen, *was* getippt wird.

---

## Wie die Typer funktionieren

Alle Typer folgen demselben Prinzip (am Beispiel `hwp_3_fib.py`):

1. **Daten** stehen oben im Skript als Liste `ROWS`, eine Zeile pro Tabellenzeile:
   ```python
   ("0x00", "LXI SP,0xFF", "31", "Stackpointer initialisieren"),
   ```
   Das sind die vier OPAL-Spalten: **Adresse, Mnemonik, HEX, Kommentar**.

2. **Tastatur-Simulation** über die Bibliothek [`pynput`](https://pypi.org/project/pynput/). Das Skript erzeugt einen `Controller`, der echte Tastendrücke ans aktive Fenster sendet – genau so, als würdest du tippen.

3. **Ablauf beim Start:**
   - Countdown (Standard 6 s) läuft – in dieser Zeit **klickst du ins erste Eingabefeld** in OPAL (Spalte *Adresse*, Zeile 0).
   - Danach tippt das Skript Feld für Feld:
     - `human_type()` tippt Zeichen für Zeichen mit kleinen, zufälligen Verzögerungen, damit es **menschlich/zögerlich** wirkt (nicht wie ein Bot-Schwall).
     - Nach jedem Feld wird **TAB** gedrückt, um ins nächste Feld zu springen. Nach der letzten Spalte landet der Fokus automatisch in der nächsten Zeile.
   - Am Ende meldet es „Fertig“. Du kontrollierst in OPAL und speicherst.

4. **Jederzeit abbrechen:** **ESC** drücken. Ein Hintergrund-`Listener` fängt die Taste ab und beendet das Skript sofort.

Das Timing lässt sich oben im Skript einstellen:
```python
CHAR_DELAY   = (0.0125, 0.08)   # Pause zwischen einzelnen Zeichen
TAB_DELAY    = (0.075, 0.15)    # Pause nach einem TAB
ROW_DELAY    = (0.10, 0.30)     # Pause am Zeilenende
COUNTDOWN    = 6                # Sekunden bis zum Start
```

**Sonderfälle:**
- `hwp_3_clear.py` – tippt nichts, sondern **leert** die Tabelle: tabbt durch alle Felder und löscht jedes mit „Alles markieren + Entf“. Es erkennt automatisch das OS (`Cmd+A` auf macOS, sonst `Strg+A`). Optional kann die Feldanzahl als Argument übergeben werden: `python3 hwp_3_clear.py 675`.
- `hwp_3_mul.py` – setzt voraus, dass **Zeile 0 in OPAL bereits vorgegeben** ist, und startet daher im ersten Feld von **Zeile 1**.
- `*_compact.py` – ein Befehl pro Zeile (bei 2-Byte-Befehlen werden beide Bytes zusammengefasst, z. B. `31, FF`), dadurch weniger Zeilen.

---

## Voraussetzungen

- **Python 3** (getestet mit 3.x)
- Das Paket **`pynput`**:
  ```bash
  pip install pynput
  ```
  Falls `pip` fehlt, ggf. `pip3` benutzen. Auf manchen Systemen empfiehlt sich eine virtuelle Umgebung:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate     # Windows: .venv\Scripts\activate
  pip install pynput
  ```

---

## Für dein OS freischalten

Das ist der entscheidende Schritt – und der häufigste Grund, warum es „bei den Freunden nicht geht“. `pynput` darf eine Tastatur nur simulieren, wenn das Betriebssystem es **explizit erlaubt**. Sonst passiert oft: das Skript läuft scheinbar durch, aber **es wird nichts getippt** (oder es kommt ein Permission-Fehler).

### 🍎 macOS

macOS blockiert das Senden von Tastendrücken standardmäßig. Du musst **dem Programm, das Python startet** (Terminal, iTerm, VS Code, PyCharm …), zwei Rechte geben:

1. **Systemeinstellungen → Datenschutz & Sicherheit → Bedienungshilfen** (Accessibility)
   → dein Terminal/IDE hinzufügen und Haken setzen.
2. **Systemeinstellungen → Datenschutz & Sicherheit → Eingabeüberwachung** (Input Monitoring)
   → ebenfalls dein Terminal/IDE hinzufügen (wird für das ESC-Abbrechen / den Listener gebraucht).

> Nach dem Setzen der Haken das Terminal/die IDE **komplett neu starten**. Wichtig: Den Haken bei *genau dem Programm* setzen, von dem aus du `python3 …` aufrufst – nicht bei „Python“ selbst.

Wenn nichts getippt wird, fehlt fast immer der **Bedienungshilfen**-Haken.

### 🐧 Linux

`pynput` setzt unter Linux auf **X11**.

- **X11-Sitzung:** Funktioniert direkt. Ggf. fehlt das X-Backend:
  ```bash
  pip install python-xlib
  ```
- **Wayland (Standard bei Ubuntu 22.04+, Fedora, …):** Hier kann `pynput` Tastendrücke oft **nicht** zuverlässig einspeisen – das ist die häufigste Linux-Fehlerquelle.
  - Prüfen, was läuft:
    ```bash
    echo $XDG_SESSION_TYPE      # "x11" oder "wayland"
    ```
  - Lösung: Beim Login-Bildschirm unten aufs Zahnrad → **„GNOME on Xorg“ / X11-Sitzung** wählen, dann erneut anmelden und das Skript starten.
- Manche Distributionen verlangen, dass dein Benutzer in der Gruppe `input` ist:
  ```bash
  sudo usermod -aG input $USER   # danach neu einloggen
  ```

### 🪟 Windows

Meist läuft es **ohne Extra-Berechtigung**:
```bash
pip install pynput
python hwp_3_fib.py
```
Falls nicht getippt wird:
- **Als Administrator ausführen**, falls das OPAL-Fenster mit erhöhten Rechten läuft (ein normaler Prozess darf keine Tasten an ein Admin-Fenster senden).
- Virenscanner/„Controlled Folder Access“ können Tastatur-Simulation blockieren → kurz testweise erlauben.

---

## Tastaturlayout beachten (alle OS)

Die Typer senden Zeichen wie `0x3A`, `,`, `LXI SP`. `pynput` tippt diese über das **aktuell aktive Tastaturlayout**. Wenn bei dir/deinen Freunden ein anderes Layout aktiv ist (z. B. US statt DE), können Sonderzeichen falsch ankommen. Im Zweifel vor dem Lauf auf dasselbe Layout umstellen, mit dem die Skripte erstellt wurden (**Deutsch**).

---

## Schnellstart

```bash
# 1. Abhängigkeit installieren
pip install pynput

# 2. OS freischalten (siehe oben – v. a. macOS/Linux!)

# 3. Skript starten
cd typer_for_opal
python3 hwp_3_fib.py

# 4. Während des Countdowns ins erste OPAL-Feld klicken (Adresse, Zeile 0)
# 5. Hände weg. Abbrechen jederzeit mit ESC.
```

---

## Tabellen dekodieren (optional)

Um nachzusehen, was ein HEX-Dump bedeutet:

```bash
python3 tabellen/decode.py scripts_for_editor/fibonacci_emulator.csv
```

Gibt eine Tabelle mit **Adresse, HEX, Binär, Schalterstellung (A7..A0 / D7..D0), Mnemonik und Kommentar** aus – nützlich, um die Typer-Daten mit dem tatsächlichen Programm abzugleichen.
