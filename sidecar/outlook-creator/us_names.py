"""Prenoms et noms de famille courants aux Etats-Unis (generation aleatoire)."""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_MIN_NAMES = 5000
_FIRST_NAMES_FILE = "us_first_names.txt"
_LAST_NAMES_FILE = "us_last_names.txt"


def _data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "data"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent / "data"


def _load_name_list(filename: str) -> tuple[str, ...]:
    path = _data_dir() / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing name list: {path} (expected under sidecar/outlook-creator/data/)."
        )
    names = tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
    if len(names) < _MIN_NAMES:
        raise ValueError(
            f"{filename} has {len(names)} names; at least {_MIN_NAMES} required."
        )
    return names


US_FIRST_NAMES: tuple[str, ...] = _load_name_list(_FIRST_NAMES_FILE)
US_LAST_NAMES: tuple[str, ...] = _load_name_list(_LAST_NAMES_FILE)


def random_us_first_name() -> str:
    return random.choice(US_FIRST_NAMES)


def random_us_last_name() -> str:
    return random.choice(US_LAST_NAMES)


def normalize_name_part(value: str) -> str:
    return value.strip().casefold()


def parse_used_name_pairs(json_payload: str) -> set[tuple[str, str]]:
    """Parse JSON `[["First","Last"], ...]` en ensemble de paires normalisees."""
    if not json_payload or not json_payload.strip():
        return set()

    try:
        raw: object = json.loads(json_payload)
    except json.JSONDecodeError:
        return set()

    if not isinstance(raw, list):
        return set()

    used: set[tuple[str, str]] = set()
    for item in raw:
        first: str | None = None
        last: str | None = None

        if isinstance(item, (list, tuple)) and len(item) >= 2:
            first = str(item[0])
            last = str(item[1])
        elif isinstance(item, dict):
            first = str(item.get("firstName") or item.get("first_name") or "")
            last = str(item.get("lastName") or item.get("last_name") or "")

        if not first or not last:
            continue

        used.add((normalize_name_part(first), normalize_name_part(last)))

    return used


def random_us_full_name(used_pairs: set[tuple[str, str]] | None = None) -> tuple[str, str]:
    """Tire un prenom et un nom, en evitant les paires deja utilisees si fournies."""
    excluded: set[tuple[str, str]] = used_pairs or set()
    max_attempts: int = 2000

    for _ in range(max_attempts):
        first_name: str = random_us_first_name()
        last_name: str = random_us_last_name()
        key: tuple[str, str] = (normalize_name_part(first_name), normalize_name_part(last_name))

        if key not in excluded:
            return first_name, last_name

    raise RuntimeError(
        "Impossible de tirer un prenom et un nom non deja utilises "
        f"({len(excluded)} combinaisons exclues)."
    )
