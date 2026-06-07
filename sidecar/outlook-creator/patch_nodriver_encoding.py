"""
Corrige l'encodage de nodriver/cdp/network.py (requis pour Python 3.14+).

Voir https://github.com/ultrafunkamsterdam/nodriver/issues/35
"""
from __future__ import annotations

import pathlib
import site
import sys

MAX_SAFE_LINE_LENGTH: int = 8000


def candidate_site_packages() -> list[str]:
    """
    Liste les dossiers site-packages possibles (global + user-site).
    @returns Liste de chemins uniques.
    """
    paths: list[str] = []

    for value in site.getsitepackages():
        if value not in paths:
            paths.append(value)

    user_site: str = site.getusersitepackages()
    if user_site and user_site not in paths:
        paths.append(user_site)

    return paths


def patch_network_file(network_py: pathlib.Path) -> None:
    """
    Corrige l'encodage et force une recompilation propre du module nodriver.cdp.network.
    @param network_py - Fichier network.py de nodriver.
    @returns None.
    """
    raw: bytes = network_py.read_bytes()

    try:
        text: str = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = remove_parser_overflow_lines(text)
    network_py.write_text(text, encoding="utf-8", newline="\n")

    pycache_dir: pathlib.Path = network_py.parent / "__pycache__"
    if pycache_dir.is_dir():
        for compiled in pycache_dir.glob("network*.pyc"):
            try:
                compiled.unlink()
            except OSError:
                pass


def remove_parser_overflow_lines(text: str) -> str:
    """
    Supprime les commentaires generes trop longs qui cassent le parser Python 3.14.
    @param text - Contenu source de nodriver.cdp.network.
    @returns Source patché.
    """
    output: list[str] = []
    removed_count: int = 0

    for line in text.split("\n"):
        if len(line) > MAX_SAFE_LINE_LENGTH and line.lstrip().startswith("#"):
            indent: str = line[: len(line) - len(line.lstrip())]
            output.append(f"{indent}#: Long generated CDP comment removed by Alyvo patch.")
            removed_count += 1
            continue

        output.append(line)

    if removed_count:
        print(f"Removed {removed_count} oversized generated comment line(s).", file=sys.stderr)

    return "\n".join(output)


def main() -> int:
    for base in candidate_site_packages():
        network_py = pathlib.Path(base) / "nodriver" / "cdp" / "network.py"

        if not network_py.is_file():
            continue

        patch_network_file(network_py)
        print(f"Patched nodriver encoding: {network_py}", file=sys.stderr)
        return 0

    print("nodriver/cdp/network.py not found — is nodriver installed?", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
