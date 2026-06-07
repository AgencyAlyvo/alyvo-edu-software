"""
Sidecar Alyvo Edu — inscription Broward College via nodriver + CapSolver.

Sortie : une ligne JSON sur stdout. Logs sur stderr.
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import os
import sys
from collections.abc import Callable
from typing import Any

from broward_signup_flow import (
    BrowardAccountInput,
    derive_broward_ssn,
    normalize_broward_email,
    run_broward_signup,
)
from capsolver_client import CapSolverProxyBannedError

SIGNUP_TIMEOUT_SECONDS: float = 900
BROWSER_STOP_POLL_INTERVAL_SECONDS: float = 0.25
BROWSER_STOP_MAX_POLL_ATTEMPTS: int = 40
BROWSER_POST_CLOSE_PAUSE_SECONDS: float = 1.5
CAPSOLVER_PROXY_BANNED_MAX_ATTEMPTS: int = 2
CAPSOLVER_PROXY_BANNED_RETRY_PAUSE_S: float = 3.0


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
    parser = argparse.ArgumentParser(description="Alyvo Edu — inscription Broward")
    parser.add_argument(
        "--account-json",
        required=True,
        help="JSON compte : accountId, firstName, lastName, birthday, email, password",
    )
    return parser.parse_args()


def parse_account_json(raw: str) -> BrowardAccountInput:
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"account-json invalide : {error}") from error

    account_id: Any = data.get("accountId")
    first_name: str = str(data.get("firstName", "")).strip()
    last_name: str = str(data.get("lastName", "")).strip()
    birthday: str = str(data.get("birthday", "")).strip()
    email: str = normalize_broward_email(str(data.get("email", "")))
    password: str = str(data.get("password", "")).strip()
    born_in_us: str = str(data.get("bornInUs", "Yes")).strip() or "Yes"
    application_term: str = str(data.get("applicationTerm", "Summer")).strip() or "Summer"
    street: str = str(data.get("street", data.get("addressStreet", "3020 Lake Spier Dr"))).strip() or "3020 Lake Spier Dr"
    city: str = str(data.get("city", data.get("addressCity", "El Paso"))).strip() or "El Paso"
    state: str = str(data.get("state", data.get("addressState", "Texas"))).strip() or "Texas"
    postal_code: str = str(data.get("postalCode", data.get("zip", "79936"))).strip() or "79936"
    mobile_phone: str = "".join(
        char for char in str(data.get("mobilePhone", "9155550184")) if char.isdigit()
    )[:10] or "9155550184"
    home_phone_raw: Any = data.get("homePhone", "")
    home_phone: str = (
        "".join(char for char in str(home_phone_raw) if char.isdigit())[:10]
        if home_phone_raw is not None and str(home_phone_raw).strip()
        else ""
    )
    emergency_first_name: str = str(data.get("emergencyFirstName", "Maria")).strip() or "Maria"
    emergency_last_name: str = str(data.get("emergencyLastName", "Johnson")).strip() or "Johnson"
    emergency_relationship: str = str(data.get("emergencyRelationship", "Other")).strip() or "Other"
    emergency_mobile_phone: str = "".join(
        char for char in str(data.get("emergencyMobilePhone", "9155550186")) if char.isdigit()
    )[:10] or "9155550186"
    gender: str = str(data.get("gender", "Female")).strip() or "Female"
    race: str = str(data.get("race", "White")).strip() or "White"
    primary_language: str = str(data.get("primaryLanguage", "English")).strip() or "English"
    high_school_degree: str = (
        str(data.get("highSchoolDegree", "Standard High School Diploma")).strip()
        or "Standard High School Diploma"
    )
    high_school_graduation_date: str = (
        str(data.get("highSchoolGraduationDate", "2030-05-05")).strip()
        or "2030-05-05"
    )
    high_school_state: str = str(data.get("highSchoolState", "Texas")).strip() or "Texas"
    high_school_name: str = (
        str(data.get("highSchoolName", "El Paso High School")).strip()
        or "El Paso High School"
    )

    if account_id is None or not first_name or not last_name or not birthday or not email or not password:
        raise ValueError("account-json incomplet (accountId, firstName, lastName, birthday, email, password).")

    parsed_account_id: int = int(account_id)
    ssn_raw: Any = data.get("ssn")
    if ssn_raw is not None and str(ssn_raw).strip():
        ssn: str = "".join(char for char in str(ssn_raw) if char.isdigit())[:9]
        if len(ssn) != 9:
            raise ValueError("ssn invalide : 9 chiffres requis.")
    else:
        ssn = derive_broward_ssn(parsed_account_id)

    return BrowardAccountInput(
        account_id=parsed_account_id,
        first_name=first_name,
        last_name=last_name,
        birthday=birthday[:10],
        email=email,
        password=password,
        born_in_us_territory=born_in_us,
        application_term=application_term,
        street=street,
        city=city,
        state=state,
        postal_code=postal_code,
        mobile_phone=mobile_phone,
        home_phone=home_phone,
        ssn=ssn,
        emergency_first_name=emergency_first_name,
        emergency_last_name=emergency_last_name,
        emergency_relationship=emergency_relationship,
        emergency_mobile_phone=emergency_mobile_phone,
        gender=gender,
        race=race,
        primary_language=primary_language,
        high_school_degree=high_school_degree,
        high_school_graduation_date=high_school_graduation_date[:10],
        high_school_state=high_school_state,
        high_school_name=high_school_name,
    )


async def enroll_broward(account: BrowardAccountInput) -> dict[str, Any]:
    api_key: str = os.environ.get("CAPSOLVER_API_KEY", "").strip()
    if not api_key:
        return {
            "ok": False,
            "accountId": account.account_id,
            "error": "CAPSOLVER_API_KEY manquante. Configurez CapSolver dans Parametres.",
        }

    try:
        import nodriver as uc
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "accountId": account.account_id, "error": f"nodriver unavailable: {error}"}

    log(f"Prenom : {account.first_name}")
    log(f"Nom : {account.last_name}")
    log(f"Email prevu : {account.email}")
    log(f"Date de naissance : {account.birthday}")

    for attempt in range(1, CAPSOLVER_PROXY_BANNED_MAX_ATTEMPTS + 1):
        browser = None
        tab = None

        try:
            if attempt > 1:
                log(
                    f"Nouvelle tentative complete pour ce compte "
                    f"({attempt}/{CAPSOLVER_PROXY_BANNED_MAX_ATTEMPTS})...",
                )
            else:
                log("Demarrage de Chrome/Chromium via nodriver...")

            browser = await uc.start(headless=False)
            tab = await browser.get("about:blank")

            await asyncio.wait_for(
                run_broward_signup(tab, account, api_key, log),
                timeout=SIGNUP_TIMEOUT_SECONDS,
            )

            return {
                "ok": True,
                "accountId": account.account_id,
                "email": account.email,
            }
        except CapSolverProxyBannedError as error:
            log(f"CapSolver : {error}")
            if attempt >= CAPSOLVER_PROXY_BANNED_MAX_ATTEMPTS:
                return {
                    "ok": False,
                    "accountId": account.account_id,
                    "error": (
                        f"{error} — {CAPSOLVER_PROXY_BANNED_MAX_ATTEMPTS} tentative(s) "
                        "avec redemarrage Chrome."
                    ),
                }
            log(
                "Proxy CapSolver banni : fermeture de Chrome et nouvel essai "
                "complet sur ce compte...",
            )
            await close_browser_safely(browser, tab, log)
            browser = None
            tab = None
            await asyncio.sleep(CAPSOLVER_PROXY_BANNED_RETRY_PAUSE_S)
            continue
        except asyncio.TimeoutError:
            await close_browser_safely(browser, tab, log)
            return {
                "ok": False,
                "accountId": account.account_id,
                "error": f"Inscription Broward interrompue apres {int(SIGNUP_TIMEOUT_SECONDS)}s.",
            }
        except Exception as error:  # noqa: BLE001
            await close_browser_safely(browser, tab, log)
            return {"ok": False, "accountId": account.account_id, "error": str(error)}
        finally:
            if browser is not None:
                await close_browser_safely(browser, tab, log)

    return {
        "ok": False,
        "accountId": account.account_id,
        "error": "Inscription Broward : echec apres tentatives CapSolver proxy banni.",
    }


async def main() -> int:
    try:
        args = parse_args()
        account = parse_account_json(args.account_json)
        log(
            f"Profil Broward (compte #{account.account_id}) "
            f": SSN derive={account.ssn}, {account.city}, {account.state}.",
        )
    except (SystemExit, ValueError) as error:
        emit({"ok": False, "error": str(error)})
        return 1

    result = await enroll_broward(account)
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
