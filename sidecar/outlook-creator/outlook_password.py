"""Validation et generation de mots de passe Outlook."""
from __future__ import annotations

import re
import secrets

OUTLOOK_PASSWORD_REQUIREMENTS_MESSAGE: str = (
    "Les mots de passe doivent contenir au moins 8 caracteres et inclure une combinaison "
    "de majuscules, de minuscules, de chiffres et de symboles."
)

_UPPERCASE: str = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_LOWERCASE: str = "abcdefghjkmnpqrstuvwxyz"
_DIGITS: str = "23456789"
_SYMBOLS: str = "!@#$%&*-_+=?"
_ALL_CHARS: str = _UPPERCASE + _LOWERCASE + _DIGITS + _SYMBOLS

_MIN_LENGTH: int = 14
_MAX_LENGTH: int = 18
_RECENT_MIN_LEVENSHTEIN: int = 6
_MAX_GENERATION_ATTEMPTS: int = 64


def validate_outlook_password(password: str) -> str | None:
    if len(password) < 8:
        return OUTLOOK_PASSWORD_REQUIREMENTS_MESSAGE
    if re.search(r"[A-Z]", password) is None:
        return OUTLOOK_PASSWORD_REQUIREMENTS_MESSAGE
    if re.search(r"[a-z]", password) is None:
        return OUTLOOK_PASSWORD_REQUIREMENTS_MESSAGE
    if re.search(r"[0-9]", password) is None:
        return OUTLOOK_PASSWORD_REQUIREMENTS_MESSAGE
    if re.search(r"[^A-Za-z0-9]", password) is None:
        return OUTLOOK_PASSWORD_REQUIREMENTS_MESSAGE
    return None


def generate_outlook_password(recent_passwords: tuple[str, ...] = ()) -> str:
    """Genere un mot de passe aleatoire conforme Outlook."""
    recent: list[str] = list(recent_passwords)

    for _ in range(_MAX_GENERATION_ATTEMPTS):
        password: str = _build_random_password()

        if validate_outlook_password(password) is not None or password.startswith("-"):
            continue

        if password in recent:
            continue

        if any(_levenshtein_distance(password, previous) < _RECENT_MIN_LEVENSHTEIN for previous in recent):
            continue

        return password

    raise RuntimeError("Impossible de generer un mot de passe Outlook unique.")


def _build_random_password() -> str:
    length: int = _MIN_LENGTH + secrets.randbelow(_MAX_LENGTH - _MIN_LENGTH + 1)
    chars: list[str] = [
        _pick_char(_UPPERCASE),
        _pick_char(_LOWERCASE),
        _pick_char(_DIGITS),
        _pick_char(_SYMBOLS),
    ]

    while len(chars) < length:
        chars.append(_pick_char(_ALL_CHARS))

    return "".join(_shuffle(chars))


def _pick_char(pool: str) -> str:
    return secrets.choice(pool)


def _shuffle(values: list[str]) -> list[str]:
    copy: list[str] = values[:]
    for index in range(len(copy) - 1, 0, -1):
        swap_index: int = secrets.randbelow(index + 1)
        copy[index], copy[swap_index] = copy[swap_index], copy[index]
    return copy


def _levenshtein_distance(left: str, right: str) -> int:
    rows: int = len(left) + 1
    cols: int = len(right) + 1
    matrix: list[list[int]] = [[0] * cols for _ in range(rows)]

    for row in range(rows):
        matrix[row][0] = row
    for col in range(cols):
        matrix[0][col] = col

    for row in range(1, rows):
        for col in range(1, cols):
            cost: int = 0 if left[row - 1] == right[col - 1] else 1
            matrix[row][col] = min(
                matrix[row - 1][col] + 1,
                matrix[row][col - 1] + 1,
                matrix[row - 1][col - 1] + cost,
            )

    return matrix[len(left)][len(right)]
