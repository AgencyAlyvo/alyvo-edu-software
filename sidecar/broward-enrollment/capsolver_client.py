"""
Client HTTP minimal pour CapSolver (reCAPTCHA v2).
"""
from __future__ import annotations

import time
from typing import Any

import httpx

CAPSOLVER_CREATE_TASK_URL: str = "https://api.capsolver.com/createTask"
CAPSOLVER_GET_RESULT_URL: str = "https://api.capsolver.com/getTaskResult"
POLL_INTERVAL_SECONDS: float = 2.0
MAX_POLL_ATTEMPTS: int = 60


class CapSolverError(Exception):
    """Erreur API CapSolver."""


class CapSolverProxyBannedError(CapSolverError):
    """Proxy CapSolver banni par le service cible — retry navigateur recommande."""


_PROXY_BANNED_NEEDLE: str = "proxy ip banned"


def capsolver_error_from_api(message: str | None, fallback: str) -> CapSolverError:
    """
    Construit l'exception CapSolver appropriee (proxy banni vs erreur generique).
    @param message - Message API CapSolver.
    @param fallback - Texte si message vide.
    @returns Exception a lever.
    """
    text: str = (message or fallback).strip()
    if _PROXY_BANNED_NEEDLE in text.lower():
        return CapSolverProxyBannedError(text)
    return CapSolverError(text)


def solve_recaptcha_v2(
    api_key: str,
    website_url: str,
    website_key: str,
    *,
    log: Any | None = None,
) -> str:
    """
    Resout un reCAPTCHA v2 via CapSolver (ReCaptchaV2TaskProxyLess).
    @param api_key - Cle API CapSolver.
    @param website_url - URL de la page contenant le widget.
    @param website_key - Site key reCAPTCHA.
    @param log - Fonction de log optionnelle.
    @returns Token g-recaptcha-response.
    """
    key: str = api_key.strip()
    if not key:
        raise CapSolverError("CAPSOLVER_API_KEY manquante.")

    if log:
        log("CapSolver : creation de la tache reCAPTCHA v2...")

    create_payload: dict[str, Any] = {
        "clientKey": key,
        "task": {
            "type": "ReCaptchaV2TaskProxyLess",
            "websiteURL": website_url,
            "websiteKey": website_key,
        },
    }

    with httpx.Client(timeout=60.0) as client:
        create_response: httpx.Response = client.post(CAPSOLVER_CREATE_TASK_URL, json=create_payload)
        create_response.raise_for_status()
        create_data: dict[str, Any] = create_response.json()

        if create_data.get("errorId", 0) != 0:
            raise capsolver_error_from_api(
                create_data.get("errorDescription") or create_data.get("errorCode"),
                "createTask a echoue",
            )

        task_id: str | None = create_data.get("taskId")
        if not task_id:
            raise CapSolverError("CapSolver : taskId absent dans la reponse.")

        if log:
            log(f"CapSolver : tache {task_id} — attente du token...")

        for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
            time.sleep(POLL_INTERVAL_SECONDS)
            result_response: httpx.Response = client.post(
                CAPSOLVER_GET_RESULT_URL,
                json={"clientKey": key, "taskId": task_id},
            )
            result_response.raise_for_status()
            result_data: dict[str, Any] = result_response.json()

            if result_data.get("errorId", 0) != 0:
                raise capsolver_error_from_api(
                    result_data.get("errorDescription") or result_data.get("errorCode"),
                    "getTaskResult a echoue",
                )

            status: str = str(result_data.get("status", ""))
            if status == "ready":
                solution: dict[str, Any] = result_data.get("solution") or {}
                token: str | None = solution.get("gRecaptchaResponse")
                if not token:
                    raise CapSolverError("CapSolver : gRecaptchaResponse absent.")
                if log:
                    log("CapSolver : token reCAPTCHA recu.")
                return str(token)

            if status == "failed":
                raise capsolver_error_from_api(
                    result_data.get("errorDescription") or result_data.get("errorCode"),
                    "CapSolver : resolution echouee (status failed).",
                )

            if log and attempt % 5 == 0:
                log(f"CapSolver : en attente ({attempt}/{MAX_POLL_ATTEMPTS})...")

    raise CapSolverError("CapSolver : delai depasse en attente du token.")
