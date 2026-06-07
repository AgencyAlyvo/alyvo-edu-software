"""Generation d'adresses email Outlook a partir du prenom et nom US."""
from __future__ import annotations

import random
import re
import string


def build_outlook_local_part(first_name: str, last_name: str, digit_count: int = 12) -> str:
    """
    Construit une partie locale du type prenomnom15152441122.
    @param first_name
    @param last_name
    @param digit_count
    """
    base: str = re.sub(r"[^a-z0-9]", "", f"{first_name}{last_name}".lower())

    if len(base) < 2:
        base = "user"

    digits: str = "".join(random.choices(string.digits, k=digit_count))
    return f"{base}{digits}"


def build_outlook_email(first_name: str, last_name: str) -> str:
    """Retourne une adresse @outlook.com complete."""
    return f"{build_outlook_local_part(first_name, last_name)}@outlook.com"
