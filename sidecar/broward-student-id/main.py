"""
Sidecar Alyvo Edu — recuperation Student ID / email ecole Broward via Outlook.

Sortie : une ligne JSON sur stdout. Logs sur stderr.
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import os
import sys
from pathlib import Path
from collections.abc import Callable
from typing import Any

from nodriver_window_layout import apply_nodriver_window_layout
from student_id_flow import (
    StudentIdAccountInput,
    StudentIdMailNotFoundError,
    run_student_id_flow,
)

FLOW_TIMEOUT_SECONDS: float = 1200
BROWSER_STOP_POLL_INTERVAL_SECONDS: float = 0.25
BROWSER_STOP_MAX_POLL_ATTEMPTS: int = 40
BROWSER_POST_CLOSE_PAUSE_SECONDS: float = 1.5


def configure_stdio_utf8() -> None:
    """Force stderr/stdout UTF-8 pour Tauri."""
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
) -> None:
    """Ferme Chrome proprement."""
    if browser is None:
        return

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

    await asyncio.sleep(BROWSER_POST_CLOSE_PAUSE_SECONDS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Alyvo Edu — Student ID Broward")
    parser.add_argument(
        "--account-json",
        required=True,
        help="JSON compte : accountId, email, password, birthday",
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


def parse_account_json(raw: str) -> StudentIdAccountInput:
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"account-json invalide : {error}") from error

    account_id: Any = data.get("accountId")
    email: str = str(data.get("email", "")).strip().lower()
    password: str = str(data.get("password", "")).strip()
    birthday: str = str(data.get("birthday", "")).strip()[:10]

    if account_id is None or not email or not password or not birthday:
        raise ValueError("account-json incomplet (accountId, email, password, birthday).")

    return StudentIdAccountInput(
        account_id=int(account_id),
        email=email,
        password=password,
        birthday=birthday,
    )


async def activate_student_id(
    account: StudentIdAccountInput,
    *,
    window_slot: int | None = None,
    window_slots: int | None = None,
) -> dict[str, Any]:
    try:
        import nodriver as uc
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "accountId": account.account_id, "error": f"nodriver unavailable: {error}"}

    log(f"Email Outlook : {account.email}")
    log(f"Date de naissance : {account.birthday}")

    browser = None
    tab = None

    try:
        log("Demarrage de Chrome/Chromium via nodriver...")
        browser = await uc.start(headless=False)
        tab = await browser.get("about:blank")

        if window_slot is not None and window_slots is not None:
            await apply_nodriver_window_layout(
                tab,
                slot=window_slot,
                slots=window_slots,
                log_fn=log,
            )

        result = await asyncio.wait_for(
            run_student_id_flow(tab, account, log),
            timeout=FLOW_TIMEOUT_SECONDS,
        )

        payload: dict[str, Any] = {
            "ok": True,
            "accountId": result.account_id,
            "schoolEmail": result.school_email,
            "studentId": result.student_id,
            "schoolEmailPassword": result.school_email_password or None,
        }

        if result.mybc_screenshots is not None:
            student_home_path: str = result.mybc_screenshots.student_home
            prospect_menu_path: str = result.mybc_screenshots.prospect_menu
            registration_status_path: str = result.mybc_screenshots.registration_status
            paths_ok: bool = (
                Path(student_home_path).is_file()
                and Path(prospect_menu_path).is_file()
                and Path(registration_status_path).is_file()
            )
            if paths_ok:
                payload["mybcScreenshotPaths"] = {
                    "studentHome": student_home_path,
                    "prospectMenu": prospect_menu_path,
                    "registrationStatus": registration_status_path,
                }
                log(f"Captures myBC pretes pour upload : {student_home_path}")
            else:
                log("Attention : fichiers capture myBC introuvables sur disque.")

        return payload
    except StudentIdMailNotFoundError as error:
        log(str(error))
        return {
            "ok": False,
            "skipped": True,
            "reason": "MAIL_NOT_FOUND",
            "accountId": account.account_id,
            "error": str(error),
        }
    except asyncio.TimeoutError:
        return {
            "ok": False,
            "accountId": account.account_id,
            "error": f"Student ID Broward interrompu apres {int(FLOW_TIMEOUT_SECONDS)}s.",
        }
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "accountId": account.account_id, "error": str(error)}
    finally:
        if browser is not None:
            await close_browser_safely(browser, tab, log)


async def main() -> int:
    try:
        args = parse_args()
        account = parse_account_json(args.account_json)
    except (SystemExit, ValueError) as error:
        emit({"ok": False, "error": str(error)})
        return 1

    result = await activate_student_id(
        account,
        window_slot=args.window_slot,
        window_slots=args.window_slots,
    )
    emit(result)

    if result.get("skipped"):
        return 0

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
