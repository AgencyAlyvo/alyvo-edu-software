"""
Sidecar Alyvo Edu — creation de compte Outlook via nodriver.

Runtime cible : Python 3.14.5 (interpreteur embarque dans le binaire PyInstaller au build).
Sortie : une ligne JSON sur stdout. Logs de progression sur stderr.
Chrome ou Chromium doit etre installe sur la machine de l'utilisateur.
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import os
import platform
import subprocess
import sys
from collections.abc import Callable
from typing import Any

from email_builder import build_outlook_email
from nodriver_window_layout import apply_nodriver_window_layout
from outlook_password import generate_outlook_password, validate_outlook_password
from outlook_signup_flow import SignupCredentials, run_outlook_signup
from us_names import parse_used_name_pairs, random_us_full_name

SIGNUP_STEP_TIMEOUT_SECONDS: float = 300
MANUAL_INTERVENTION_DELAY_SECONDS: float = 15.0
BROWSER_STOP_POLL_INTERVAL_SECONDS: float = 0.25
BROWSER_STOP_MAX_POLL_ATTEMPTS: int = 40
BROWSER_POST_CLOSE_PAUSE_SECONDS: float = 1.5


def configure_stdio_utf8() -> None:
    """Force stderr/stdout UTF-8 pour Tauri (lecture pipe en raw + decode cote app)."""
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding="utf-8",
            errors="replace",
            line_buffering=True,
        )
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer,
            encoding="utf-8",
            errors="replace",
            line_buffering=True,
        )


configure_stdio_utf8()


def emit(result: dict[str, Any]) -> None:
    print(json.dumps(result), flush=True)


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


async def close_browser_safely(
    browser: Any,
    tab: Any,
    log_fn: Callable[[str], None],
    *,
    pause_before_close_seconds: float = 0.0,
) -> None:
    """
    Ferme Chrome proprement avant la fin du sidecar.

    browser.stop() de nodriver planifie aclose() sans attendre ; si asyncio.run() se termine
    trop tot, Chrome reste ouvert et le compte suivant echoue au relancement.
    """
    if browser is None:
        return

    if tab is not None and pause_before_close_seconds > 0:
        try:
            await tab.sleep(pause_before_close_seconds)
        except Exception:  # noqa: BLE001
            pass

    log_fn("Fermeture de Chrome (nodriver)...")
    try:
        await browser.aclose()
    except Exception as error:  # noqa: BLE001
        log_fn(f"  aclose() : {error}")
        try:
            browser.stop()
        except Exception as stop_error:  # noqa: BLE001
            log_fn(f"  stop() : {stop_error}")

    for _ in range(BROWSER_STOP_MAX_POLL_ATTEMPTS):
        if getattr(browser, "stopped", True):
            break
        await asyncio.sleep(BROWSER_STOP_POLL_INTERVAL_SECONDS)
    else:
        log_fn("  Chrome encore actif — l'app fermera les processus avant le compte suivant.")

    await asyncio.sleep(BROWSER_POST_CLOSE_PAUSE_SECONDS)


def flush_dns_if_windows(log_fn: Callable[[str], None]) -> None:
    """Vide le cache DNS sur Windows avant le lancement de Chrome (sans droits admin)."""
    if platform.system() != "Windows":
        return

    log_fn("Flush DNS Windows (ipconfig /flushdns)...")
    try:
        completed: subprocess.CompletedProcess[str] = subprocess.run(
            ["ipconfig", "/flushdns"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if completed.returncode == 0:
            log_fn("  Cache DNS vide.")
            return

        detail: str = (completed.stderr or completed.stdout or "").strip()
        log_fn(f"  ipconfig /flushdns code {completed.returncode}: {detail or 'erreur inconnue'}")
    except Exception as error:  # noqa: BLE001
        log_fn(f"  Flush DNS ignore : {error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Alyvo Edu — creation compte Outlook")
    parser.add_argument(
        "--password",
        required=False,
        default=None,
        help="Mot de passe du compte (optionnel : genere automatiquement si absent)",
    )
    parser.add_argument("--birthday", required=True, help="Date de naissance (YYYY-MM-DD)")
    parser.add_argument(
        "--used-names",
        default="[]",
        help='Paires prenom/nom deja utilisees : JSON [["First","Last"], ...]',
    )
    parser.add_argument(
        "--skip-dns-flush",
        action="store_true",
        help="Ne pas executer ipconfig /flushdns (deja fait par l'app desktop avant Chrome).",
    )
    parser.add_argument(
        "--first-name",
        default=None,
        help="Prenom impose (creation parallele) ; sinon tire au sort.",
    )
    parser.add_argument(
        "--last-name",
        default=None,
        help="Nom impose (creation parallele) ; sinon tire au sort.",
    )
    parser.add_argument(
        "--window-slot",
        type=int,
        default=None,
        help="Index fenetre dans la vague parallele (0-based).",
    )
    parser.add_argument(
        "--window-slots",
        type=int,
        default=None,
        help="Nombre d'instances Chrome simultanees pour le placement fenetre.",
    )
    return parser.parse_args()


def resolve_password(password_arg: str | None) -> str:
    if password_arg is not None and password_arg.strip():
        return password_arg.strip()
    return generate_outlook_password()


async def create_outlook_nodriver(
    password: str,
    birthday: str,
    used_name_pairs: set[tuple[str, str]],
    *,
    skip_dns_flush: bool = False,
    fixed_first_name: str | None = None,
    fixed_last_name: str | None = None,
    window_slot: int | None = None,
    window_slots: int | None = None,
) -> dict[str, Any]:
    try:
        import nodriver as uc
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "error": f"nodriver not available: {error}"}

    if used_name_pairs:
        log(f"Exclusion de {len(used_name_pairs)} combinaison(s) prenom/nom deja utilisee(s).")

    first_name: str | None = fixed_first_name.strip() if fixed_first_name else None
    last_name: str | None = fixed_last_name.strip() if fixed_last_name else None

    if first_name and last_name:
        pair: tuple[str, str] = (first_name, last_name)
        if pair in used_name_pairs:
            return {"ok": False, "error": f"Combinaison prenom/nom deja utilisee : {first_name} {last_name}"}
    else:
        try:
            first_name, last_name = random_us_full_name(used_name_pairs)
        except RuntimeError as error:
            return {"ok": False, "error": str(error)}

    browser = None
    tab = None
    pause_before_close_seconds: float = 0.0

    try:
        planned_email: str = build_outlook_email(first_name, last_name)
        log(f"Prenom : {first_name}")
        log(f"Nom : {last_name}")
        log(f"Email prevu : {planned_email}")
        log(f"Date de naissance : {birthday}")
        log(f"Mot de passe : {password}")
        log("Demarrage de Chrome/Chromium via nodriver...")
        if skip_dns_flush:
            log("  Flush DNS omis (deja effectue avant Chrome par l'app).")
        else:
            flush_dns_if_windows(log)
        browser = await uc.start(headless=False)
        tab = await browser.get("about:blank")

        if window_slot is not None and window_slots is not None:
            await apply_nodriver_window_layout(
                tab,
                slot=window_slot,
                slots=window_slots,
                log_fn=log,
            )

        credentials: SignupCredentials = await asyncio.wait_for(
            run_outlook_signup(
                tab,
                password=password,
                birthday_iso=birthday,
                first_name=first_name,
                last_name=last_name,
                log=log,
            ),
            timeout=SIGNUP_STEP_TIMEOUT_SECONDS,
        )

        log(f"Inscription terminee : {credentials.email}")

        return {
            "ok": True,
            "email": credentials.email,
            "password": credentials.password,
            "firstName": credentials.first_name,
            "lastName": credentials.last_name,
            "birthday": credentials.birthday,
        }
    except asyncio.TimeoutError:
        pause_before_close_seconds = MANUAL_INTERVENTION_DELAY_SECONDS
        return {
            "ok": False,
            "error": f"Inscription Outlook interrompue apres {int(SIGNUP_STEP_TIMEOUT_SECONDS)}s (CAPTCHA ou etape bloquee).",
        }
    except Exception as error:  # noqa: BLE001
        pause_before_close_seconds = MANUAL_INTERVENTION_DELAY_SECONDS
        return {"ok": False, "error": str(error)}
    finally:
        await close_browser_safely(
            browser,
            tab,
            log,
            pause_before_close_seconds=pause_before_close_seconds,
        )


async def main() -> int:
    try:
        args = parse_args()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        emit({"ok": False, "error": f"Invalid arguments: {error}"})
        return 1

    try:
        password: str = resolve_password(args.password)
    except RuntimeError as error:
        emit({"ok": False, "error": str(error)})
        return 1

    if args.password is not None and args.password.strip():
        password_error: str | None = validate_outlook_password(password)
        if password_error is not None:
            emit({"ok": False, "error": password_error})
            return 1
    else:
        log("Mot de passe genere automatiquement pour ce compte.")

    used_name_pairs: set[tuple[str, str]] = parse_used_name_pairs(args.used_names)
    result = await create_outlook_nodriver(
        password,
        args.birthday,
        used_name_pairs,
        skip_dns_flush=args.skip_dns_flush,
        fixed_first_name=args.first_name,
        fixed_last_name=args.last_name,
        window_slot=args.window_slot,
        window_slots=args.window_slots,
    )
    emit(result)
    return 0 if result.get("ok") else 1


def run() -> int:
    try:
        return asyncio.run(main())
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        emit({"ok": False, "error": str(error)})
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
