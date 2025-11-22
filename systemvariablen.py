#!/usr/bin/env python3
"""Umgebungsvariablen sichern und wiederherstellen."""

import argparse
import json
import os
from pathlib import Path

DEFAULT_SNAPSHOT = Path("env_snapshot.json")

def dump_env(path: Path = DEFAULT_SNAPSHOT):
    snapshot = dict(os.environ)
    path.write_text(json.dumps(snapshot, indent=2))
    print(f"Gespeichert: {len(snapshot)} Variablen in {path}")

def load_env(path: Path = DEFAULT_SNAPSHOT):
    if not path.exists():
        raise FileNotFoundError(f"Snapshot {path} nicht gefunden. Bitte zuerst dump ausführen.")
    data = json.loads(path.read_text())
    for key, value in data.items():
        os.environ[key] = value
    print(f"Geladen: {len(data)} Variablen aus {path}")

def main():
    parser = argparse.ArgumentParser(description="Umgebungsvariablen lesen und setzen")
    parser.add_argument("action", choices=("dump", "load"), help="dump=sichern, load=aus Snapshot laden")
    parser.add_argument("--file", default=str(DEFAULT_SNAPSHOT), help="Pfad zur JSON-Datei")
    args = parser.parse_args()

    target = Path(args.file)

    if args.action == "dump":
        dump_env(target)
    else:
        load_env(target)

if __name__ == "__main__":
    main()
