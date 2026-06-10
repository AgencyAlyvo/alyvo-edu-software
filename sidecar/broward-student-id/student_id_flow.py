"""
Recuperation Student ID / email ecole Broward depuis Outlook + BC One Access.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

_BROWARD_DIR: Path = Path(__file__).resolve().parent.parent / "broward-enrollment"
if str(_BROWARD_DIR) not in sys.path:
    sys.path.insert(0, str(_BROWARD_DIR))

from broward_signup_flow import (  # noqa: E402
    BrowardAccountInput,
    click_microsoft_primary,
    fill_microsoft_login_field,
    fill_microsoft_login_if_needed,
    fill_microsoft_visible_input,
    get_microsoft_login_state,
    js_eval_bool,
    js_eval_json,
    open_outlook_sign_in_from_microsoft_page,
    wait_for_outlook_inbox,
)

STUDENT_ID_SUBJECT: str = "Your student ID has arrived"
OUTLOOK_MAIL_TIMEOUT_S: float = 120.0
ONELOGIN_TIMEOUT_S: float = 90.0
MFA_SETUP_TIMEOUT_S: float = 90.0
MANUAL_MFA_TIMEOUT_S: float = 600.0
CHANGE_PASSWORD_TIMEOUT_S: float = 90.0
MYBC_SESSION_TIMEOUT_S: float = 120.0
MYBC_POLICY_TIMEOUT_S: float = 60.0
POST_LOGIN_ROUTE_TIMEOUT_S: float = 45.0
MYBC_TOTAL_STEPS: int = 26

# Phases de reprise apres connexion BC One Access (comptes partiellement actives).
PHASE_MYBC_POST_LOGON: str = "mybc_post_logon"
PHASE_MYBC_STUDENT_HOME: str = "mybc_student_home"
PHASE_PORTAL: str = "portal"
PHASE_MYBC_OTHER: str = "mybc_other"
PHASE_CHANGE_PASSWORD: str = "change_password"
PHASE_CONVERGED_TFA: str = "converged_tfa"
PHASE_MYSIGNINS: str = "mysignins"
PHASE_PROOF_UP: str = "proof_up"
PHASE_MS_LOGIN: str = "ms_login"
PHASE_MS_ERROR: str = "ms_error"
PHASE_ONELOGIN_USERNAME: str = "onelogin_username"
PHASE_SECURITY_QUESTION: str = "security_question"
PHASE_UNKNOWN: str = "unknown"

MYBC_RESUME_PHASES: frozenset[str] = frozenset(
    {PHASE_MYBC_POST_LOGON, PHASE_MYBC_STUDENT_HOME, PHASE_PORTAL, PHASE_MYBC_OTHER},
)
PHASE_PRIORITY: dict[str, int] = {
    PHASE_SECURITY_QUESTION: 105,
    PHASE_MYBC_POST_LOGON: 100,
    PHASE_MYBC_STUDENT_HOME: 95,
    PHASE_PORTAL: 90,
    PHASE_MYBC_OTHER: 80,
    PHASE_CHANGE_PASSWORD: 70,
    PHASE_CONVERGED_TFA: 60,
    PHASE_MYSIGNINS: 50,
    PHASE_PROOF_UP: 40,
    PHASE_MS_ERROR: 35,
    PHASE_MS_LOGIN: 30,
    PHASE_ONELOGIN_USERNAME: 20,
    PHASE_UNKNOWN: 0,
}

MYBC_BASE: str = "https://mybc.broward.edu"
MYBC_POST_LOGON_URL: str = f"{MYBC_BASE}/FCCSC/security/studentpostlogon.jsp"
MYBC_STUDENT_HOME_URL: str = f"{MYBC_BASE}/FCCSC/student/ias900n1.jsp"
MYBC_HOME_SERVLET_PATH: str = "/FCCSC/servlet/security.IAU090N0s"
MYBC_PROSPECT_MENU_URL: str = f"{MYBC_BASE}/FCCSC/prospects/prospectmenu.jsp"
MYBC_MY_DETAILS_SERVLET_PATH: str = "/FCCSC/servlet/prospects.IAS065N0s"
MYBC_REGISTRATION_DATES_PATH: str = "/FCCSC/servlet/registration.IAS021N0s"
MYBC_REGISTRATION_STATUS_SERVLET_PATH: str = "/FCCSC/servlet/registration.IAS016N1s"
MYBC_PRIMARY_OBJECTIVE_DISPLAY: str = "2150 - Applied Artificial Intelligence"
MYBC_SCREENSHOT_LOAD_TIMEOUT_S: float = 60.0
MYBC_SCREENSHOT_POST_DOM_WAIT_S: float = 0.6
MYBC_SCREENSHOT_MAX_WIDTH: int = 1920
MYBC_SECURITY_QUESTION_CODE: str = "04"  # The Name Of Your Favorite Pet
MYBC_SECURITY_QUESTION_ANSWER: str = "Buddy"
ONELOGIN_PORTAL_URL: str = "https://broward.onelogin.com/"
ONELOGIN_USER_PORTAL_URL: str = "https://broward.onelogin.com/portal"

SCHOOL_EMAIL_RE: re.Pattern[str] = re.compile(r"[\w.+-]+@mail\.broward\.edu", re.IGNORECASE)
STUDENT_ID_RE: re.Pattern[str] = re.compile(r"Your Student ID is:\s*([A-Z0-9]+)", re.IGNORECASE)

LogFn = Callable[[str], None]


class StudentIdMailNotFoundError(Exception):
    """Email « Your student ID has arrived » absent de la boite Outlook."""


@dataclass(frozen=True)
class StudentIdAccountInput:
    account_id: int
    email: str
    password: str
    birthday: str


@dataclass(frozen=True)
class MybcScreenshotPaths:
    student_home: str
    prospect_menu: str
    registration_status: str


@dataclass(frozen=True)
class StudentIdFlowResult:
    account_id: int
    school_email: str
    student_id: str
    school_email_password: str
    mybc_screenshots: MybcScreenshotPaths | None = None


def bc_proud_temp_password(birthday: str) -> str:
    """
    Mot de passe temporaire BC One Access : MMYYYY@BCProud!
    @param birthday - Date ISO YYYY-MM-DD.
    @returns Mot de passe temporaire.
    """
    normalized: str = birthday.strip()[:10]
    if len(normalized) < 10 or normalized[4] != "-":
        return ""
    mm: str = normalized[5:7]
    yyyy: str = normalized[0:4]
    return f"{mm}{yyyy}@BCProud!"


def to_broward_account(account: StudentIdAccountInput) -> BrowardAccountInput:
    """Adapte le compte minimal pour les helpers Outlook de broward_signup_flow."""
    return BrowardAccountInput(
        account_id=account.account_id,
        first_name="Student",
        last_name="Id",
        birthday=account.birthday[:10],
        email=account.email,
        password=account.password,
    )


def _student_id_outlook_mail_js() -> str:
    subject_json: str = json.dumps(STUDENT_ID_SUBJECT.lower())
    return f"""
            const subjectNeedle = {subject_json};
            const isStudentIdRow = (el) => {{
                if (!el) return false;
                const aria = (el.getAttribute('aria-label') || '').toLowerCase();
                if (aria.includes(subjectNeedle) || aria.includes('student id has arrived')) {{
                    return true;
                }}
                const subject = el.querySelector('span.TtcXM, span.JdFsz');
                const subjectText = ((subject && subject.textContent) || '').trim().toLowerCase();
                if (subjectText.includes(subjectNeedle)) {{
                    return true;
                }}
                const preview = (el.textContent || '').toLowerCase();
                return preview.includes(subjectNeedle);
            }};
            const findStudentIdRow = () => {{
                const listRows = Array.from(
                    document.querySelectorAll('#MailList [role="option"], [role="listbox"] [role="option"]'),
                );
                let row = listRows.find(isStudentIdRow);
                if (row) return row;

                const subjects = Array.from(document.querySelectorAll('span.TtcXM, span.JdFsz'));
                const subject = subjects.find((el) =>
                    ((el.textContent || '').trim().toLowerCase()).includes(subjectNeedle),
                );
                if (!subject) return null;
                return (
                    subject.closest('[role="option"]')
                    || subject.closest('[data-convid]')
                    || subject.closest('.jGG6V')
                );
            }};
    """


async def click_student_id_email(tab: Any, log: LogFn) -> bool:
    """Clique la ligne du mail Student ID dans OWA."""
    click_data: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        {_student_id_outlook_mail_js()}
            const row = findStudentIdRow();
            if (!row) {{
                return {{ clicked: false }};
            }}
            row.scrollIntoView({{ block: 'center' }});
            row.click();
            return {{ clicked: true, aria: (row.getAttribute('aria-label') || '').slice(0, 120) }};
        """,
    )
    if click_data.get("clicked"):
        aria: str = str(click_data.get("aria") or "").strip()
        if aria:
            log(f"  Clic email Student ID : {aria[:80]}...")
        else:
            log(f"  Clic email « {STUDENT_ID_SUBJECT} ».")
        return True
    return False


def _outlook_mail_body_roots_js() -> str:
    """JS partage : racines du corps du message OWA (conteneurs + iframes)."""
    return """
            const getOutlookMailBodyRoots = () => {
                const roots = [];
                const pushIframes = (node) => {
                    if (!node || !node.querySelectorAll) return;
                    node.querySelectorAll('iframe').forEach((iframe) => {
                        try {
                            const doc = iframe.contentDocument || iframe.contentWindow?.document;
                            if (doc && doc.body) {
                                roots.push(doc);
                                pushIframes(doc.body);
                            }
                        } catch (_) {
                            /* cross-origin iframe */
                        }
                    });
                };
                const containers = [
                    document.querySelector('[data-test-id="mailMessageBodyContainer"]'),
                    document.querySelector('#UniqueMessageBody'),
                    document.querySelector('[role="document"]'),
                    document.querySelector('.wide-content-host'),
                ].filter(Boolean);
                if (containers.length) {
                    for (const container of containers) {
                        roots.push(container);
                        pushIframes(container);
                    }
                } else {
                    roots.push(document);
                    pushIframes(document.body);
                }
                return roots;
            };
            const normalizeMailLinkHref = (el) => (
                (el.href || el.getAttribute('href') || el.getAttribute('title') || '')
                    .replace(/&amp;/g, '&')
                    .trim()
            );
            const isBcOneAccessLink = (el) => {
                const text = (el.textContent || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                const href = normalizeMailLinkHref(el).toLowerCase();
                const title = (el.getAttribute('title') || '').toLowerCase();
                const mentionsBcOneAccess =
                    text === 'bc one access' || text.includes('bc one access');
                const isOneLoginTarget =
                    href.includes('broward.onelogin.com/login2')
                    || title.includes('broward.onelogin.com/login2')
                    || href.includes('onelogin.com/login2')
                    || title.includes('onelogin.com/login2');
                return mentionsBcOneAccess && isOneLoginTarget;
            };
            const findBcOneAccessLinks = () => {
                const seen = new Set();
                const matches = [];
                for (const root of getOutlookMailBodyRoots()) {
                    const scope = root.querySelectorAll ? root : root.documentElement;
                    if (!scope || !scope.querySelectorAll) continue;
                    Array.from(scope.querySelectorAll('a[href]')).forEach((el) => {
                        if (seen.has(el)) return;
                        seen.add(el);
                        if (isBcOneAccessLink(el)) {
                            matches.push(el);
                        }
                    });
                }
                return matches;
            };
    """


async def read_student_id_mail_body(tab: Any) -> str:
    """Lit le corps du message ouvert dans Outlook."""
    body_data: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        {_outlook_mail_body_roots_js()}
            for (const root of getOutlookMailBodyRoots()) {{
                const scope = root.querySelectorAll ? root : root.documentElement;
                if (!scope) continue;
                const text = (scope.innerText || scope.textContent || '').trim();
                if (text.length > 40) {{
                    return {{ body: text.slice(0, 12000) }};
                }}
            }}
            const bodyText = (document.body?.innerText || '').trim();
            return {{ body: bodyText.slice(0, 12000) }};
        """,
    )
    return str(body_data.get("body") or "")


def parse_student_id_mail(body: str) -> tuple[str, str]:
    """
    Extrait email ecole et student ID depuis le corps du mail.
    @returns (school_email, student_id)
    """
    email_match: re.Match[str] | None = SCHOOL_EMAIL_RE.search(body)
    id_match: re.Match[str] | None = STUDENT_ID_RE.search(body)

    school_email: str = email_match.group(0).strip().lower() if email_match else ""
    student_id: str = id_match.group(1).strip().upper() if id_match else ""

    if not school_email:
        raise RuntimeError("Email @mail.broward.edu introuvable dans le corps du message.")
    if not student_id:
        raise RuntimeError("Student ID introuvable dans le corps du message.")

    return school_email, student_id


async def extract_bc_one_access_href(tab: Any) -> str:
    """Extrait le lien BC One Access depuis le corps du mail ouvert (OWA + iframes)."""
    href_data: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        {_outlook_mail_body_roots_js()}
            const links = findBcOneAccessLinks();
            if (!links.length) {{
                return {{ href: '', count: 0 }};
            }}
            const href = normalizeMailLinkHref(links[0]);
            return {{ href, count: links.length }};
        """,
    )
    return str(href_data.get("href") or "").strip()


async def _read_tab_url(tab: Any) -> str:
    """Lit l'URL courante d'un onglet nodriver."""
    url_data: dict[str, Any] = await js_eval_json(
        tab,
        """
            return { url: (location.href || '').trim() };
        """,
    )
    return str(url_data.get("url") or "").strip()


async def _close_stray_onelogin_tabs(keep_tab: Any, log: LogFn) -> None:
    """Ferme les onglets OneLogin en double (ex. target=_blank du lien mail)."""
    browser: Any | None = getattr(keep_tab, "browser", None)
    if browser is None:
        return

    await browser.update_targets()
    for candidate in list(getattr(browser, "tabs", []) or []):
        if candidate is keep_tab:
            continue
        try:
            candidate_url: str = await _read_tab_url(candidate)
        except Exception:  # noqa: BLE001
            continue
        if "onelogin.com" not in candidate_url.lower():
            continue
        log(f"  Fermeture onglet OneLogin en double : {candidate_url[:80]}...")
        try:
            await candidate.close()
        except Exception:  # noqa: BLE001
            pass


async def open_bc_one_access_from_mail(tab: Any, log: LogFn) -> Any:
    """
    Ouvre BC One Access depuis le mail Student ID dans le meme onglet qu'Outlook.
    On n'utilise pas link.click() : le lien a souvent target=_blank et ouvre un 2e onglet inutile.
    """
    href_data: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        {_outlook_mail_body_roots_js()}
            const links = findBcOneAccessLinks();
            if (!links.length) {{
                return {{ href: '', count: 0 }};
            }}
            const href = normalizeMailLinkHref(links[0]);
            return {{ href, count: links.length }};
        """,
    )

    href: str = str(href_data.get("href") or "").strip()
    link_count: int = int(href_data.get("count") or 0)

    if not href:
        href = await extract_bc_one_access_href(tab)

    if not href or "onelogin.com/login2" not in href.lower():
        raise RuntimeError("Lien « BC One Access » (broward.onelogin.com/login2) introuvable dans le mail Student ID.")

    if link_count > 1:
        log(f"  {link_count} lien(s) « BC One Access » trouve(s) — navigation vers le premier (meme onglet).")
    else:
        log("  Navigation vers BC One Access dans le meme onglet (sans clic sur le lien du mail).")

    log(f"  URL : {href[:100]}...")
    await tab.get(href)
    await tab.sleep(2.5)
    await _close_stray_onelogin_tabs(tab, log)
    return tab


async def dismiss_onetrust_if_present(tab: Any) -> None:
    """Ferme la banniere cookies OneTrust si visible."""
    await js_eval_bool(
        tab,
        """
        () => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const accept = buttons.find((btn) => {
                const text = (btn.textContent || '').trim().toLowerCase();
                return text.includes('accept') || text.includes('accepter') || text.includes('agree');
            });
            if (accept) {
                accept.click();
                return true;
            }
            return false;
        }
        """,
    )


async def submit_bc_one_access_username(tab: Any, school_email: str, log: LogFn) -> None:
    """Remplit l'email ecole sur OneLogin et clique Continue."""
    await dismiss_onetrust_if_present(tab)
    await tab.sleep(1.0)

    email_json: str = json.dumps(school_email)
    attempts: int = max(1, int(ONELOGIN_TIMEOUT_S / 1.0))

    for i in range(attempts):
        state: dict[str, Any] = await js_eval_json(
            tab,
            f"""
            const username = document.querySelector('#username, input[data-testid="username"]');
            const visible = (el) => {{
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 4 && rect.height > 4;
            }};
            const submit = document.querySelector(
                'button[type="submit"], button[data-testid="auth-username-screen"] button[type="submit"]',
            );
            const continueBtn = Array.from(document.querySelectorAll('button[type="submit"]')).find((btn) => {{
                const text = (btn.textContent || '').trim().toLowerCase();
                return text === 'continue' || text === 'continuer';
            }});
            return {{
                hasUsername: !!(username && visible(username)),
                hasContinue: !!(continueBtn || submit),
                url: (location.href || '').slice(0, 120),
            }};
            """,
        )

        if state.get("hasUsername"):
            filled: bool = await js_eval_bool(
                tab,
                f"""
                () => {{
                    const input = document.querySelector('#username, input[data-testid="username"]');
                    if (!input) return false;
                    input.focus();
                    const nativeSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype,
                        'value',
                    )?.set;
                    const value = {email_json};
                    if (nativeSetter) {{
                        nativeSetter.call(input, value);
                    }} else {{
                        input.value = value;
                    }}
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return (input.value || '').trim().toLowerCase() === value.toLowerCase();
                }}
                """,
            )
            if not filled:
                raise RuntimeError("Impossible de remplir le champ username OneLogin.")

            clicked: bool = await js_eval_bool(
                tab,
                """
                () => {
                    const buttons = Array.from(document.querySelectorAll('button[type="submit"]'));
                    const btn = buttons.find((el) => {
                        const text = (el.textContent || '').trim().toLowerCase();
                        return text === 'continue' || text === 'continuer';
                    }) || buttons[0];
                    if (!btn) return false;
                    btn.scrollIntoView({ block: 'center' });
                    btn.click();
                    return true;
                }
                """,
            )
            if not clicked:
                raise RuntimeError("Bouton Continue OneLogin introuvable.")

            log(f"  BC One Access : email {school_email} saisi, Continue clique.")
            await tab.sleep(2.0)
            return

        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente page OneLogin ({i}/{attempts}) — url={state.get('url', '')!r}...")

    raise RuntimeError("Page OneLogin BC One Access introuvable ou champ username absent.")


async def _iter_browser_tabs(tab: Any) -> list[Any]:
    """Liste les onglets Chrome ouverts (nodriver)."""
    browser: Any | None = getattr(tab, "browser", None)
    if browser is None:
        return [tab]

    await browser.update_targets()
    tabs: list[Any] = list(getattr(browser, "tabs", []) or [])
    return tabs if tabs else [tab]


async def _read_change_password_state(tab: Any) -> dict[str, Any]:
    """Detecte la page Microsoft ConvergedChangePassword."""
    return await js_eval_json(
        tab,
        """
            const pageId = document.querySelector('meta[name="PageID"]');
            const pgid = ((pageId && pageId.getAttribute('content')) || '').trim();
            const currentPassword = document.querySelector('#currentPassword, input[name="currentpasswd"]');
            const newPassword = document.querySelector('#newPassword, input[name="newpasswd"]');
            const confirmPassword = document.querySelector('#confirmNewPassword, input[name="confirmnewpasswd"]');
            const visible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 4 && rect.height > 4;
            };
            const hasCurrent = !!(currentPassword && visible(currentPassword));
            const hasNew = !!(newPassword && visible(newPassword));
            const hasConfirm = !!(confirmPassword && visible(confirmPassword));
            return {
                isChangePassword:
                    pgid === 'ConvergedChangePassword'
                    || (hasCurrent && hasNew && hasConfirm),
                hasCurrent,
                hasNew,
                hasConfirm,
                pgid,
                url: (location.href || '').slice(0, 120),
                host: location.hostname || '',
            };
        """,
    )


async def _find_tab_with_change_password(tab: Any) -> tuple[Any | None, dict[str, Any]]:
    """Retourne le premier onglet affichant le formulaire de changement de mot de passe."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            state: dict[str, Any] = await _read_change_password_state(candidate)
        except Exception:  # noqa: BLE001
            continue
        if state.get("isChangePassword") and state.get("hasCurrent"):
            return candidate, state
    return None, {}


async def _find_microsoft_login_tab(tab: Any) -> tuple[Any | None, dict[str, Any]]:
    """Retourne l'onglet ConvergedSignIn Microsoft (username ou password)."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            url: str = await _read_tab_url(candidate)
        except Exception:  # noqa: BLE001
            continue
        if "login.microsoftonline.com" not in url.lower() and "login.microsoft.com" not in url.lower():
            continue
        try:
            state: dict[str, Any] = await get_microsoft_login_state(candidate)
        except Exception:  # noqa: BLE001
            continue
        if str(state.get("step") or "") in ("username", "password"):
            return candidate, state
    return None, {}


async def _classify_tab_phase(tab: Any) -> tuple[str, dict[str, Any]]:
    """Classifie l'etape courante d'un onglet pour reprise du flux Student ID."""
    try:
        url: str = (await _read_tab_url(tab)).lower()
    except Exception:  # noqa: BLE001
        return PHASE_UNKNOWN, {}

    if "mybc.broward.edu" in url:
        try:
            security_q_state: dict[str, Any] = await _read_mybc_security_question_state(tab)
        except Exception:  # noqa: BLE001
            security_q_state = {}
        if security_q_state.get("isSecurityQuestion"):
            return PHASE_SECURITY_QUESTION, security_q_state

        try:
            post_state: dict[str, Any] = await _read_mybc_post_logon_state(tab)
        except Exception:  # noqa: BLE001
            post_state = {}
        if post_state.get("isPostLogon"):
            return PHASE_MYBC_POST_LOGON, post_state

        try:
            home_state: dict[str, Any] = await _read_mybc_student_home_state(tab)
        except Exception:  # noqa: BLE001
            home_state = {}
        if home_state.get("isStudentHome"):
            return PHASE_MYBC_STUDENT_HOME, home_state

        return PHASE_MYBC_OTHER, {"url": url[:140]}

    if "onelogin.com" in url:
        if "/portal" in url:
            try:
                portal_state: dict[str, Any] = await _read_onelogin_portal_state(tab)
            except Exception:  # noqa: BLE001
                portal_state = {"isPortal": True}
            if portal_state.get("isPortal"):
                return PHASE_PORTAL, portal_state
        try:
            username_state: dict[str, Any] = await _read_onelogin_username_screen(tab)
        except Exception:  # noqa: BLE001
            username_state = {}
        if username_state.get("hasUsername"):
            return PHASE_ONELOGIN_USERNAME, username_state
        return PHASE_UNKNOWN, {"url": url[:140]}

    if "login.microsoftonline.com" in url or "login.microsoft.com" in url:
        try:
            change_state: dict[str, Any] = await _read_change_password_state(tab)
        except Exception:  # noqa: BLE001
            change_state = {}
        if change_state.get("isChangePassword") and change_state.get("hasCurrent"):
            return PHASE_CHANGE_PASSWORD, change_state

        try:
            tfa_state: dict[str, Any] = await _read_converged_tfa_state(tab)
        except Exception:  # noqa: BLE001
            tfa_state = {}
        if tfa_state.get("isConvergedTFA"):
            return PHASE_CONVERGED_TFA, tfa_state

        try:
            proof_state: dict[str, Any] = await _read_proof_up_redirect_state(tab)
        except Exception:  # noqa: BLE001
            proof_state = {}
        if proof_state.get("isProofUpRedirect"):
            return PHASE_PROOF_UP, proof_state

        try:
            error_state: dict[str, Any] = await _read_converged_error_state(tab)
        except Exception:  # noqa: BLE001
            error_state = {}
        if error_state.get("isConvergedError"):
            return PHASE_MS_ERROR, error_state

        try:
            ms_state: dict[str, Any] = await get_microsoft_login_state(tab)
        except Exception:  # noqa: BLE001
            ms_state = {}
        if str(ms_state.get("step") or "") in ("username", "password"):
            return PHASE_MS_LOGIN, ms_state

    if "mysignins.microsoft.com" in url:
        try:
            mysignins_state: dict[str, Any] = await _read_mysignins_register_state(tab)
        except Exception:  # noqa: BLE001
            mysignins_state = {}
        return PHASE_MYSIGNINS, mysignins_state

    return PHASE_UNKNOWN, {}


async def _detect_flow_resume_phase(tab: Any) -> tuple[Any | None, str, dict[str, Any]]:
    """Detecte la phase la plus avancee parmi tous les onglets ouverts."""
    best_tab: Any | None = None
    best_phase: str = PHASE_UNKNOWN
    best_state: dict[str, Any] = {}
    best_priority: int = -1

    for candidate in await _iter_browser_tabs(tab):
        try:
            phase, state = await _classify_tab_phase(candidate)
        except Exception:  # noqa: BLE001
            continue
        priority: int = PHASE_PRIORITY.get(phase, 0)
        if priority > best_priority:
            best_tab = candidate
            best_phase = phase
            best_state = state
            best_priority = priority

    return best_tab, best_phase, best_state


async def _try_resume_mybc_entry(tab: Any, log: LogFn) -> Any | None:
    """
    Si le compte est deja sur portail OneLogin ou myBC, retourne l'onglet pour reprendre
    directement les politiques (sans refaire MFA / changement MDP).
    """
    resume_tab, phase, _state = await _detect_flow_resume_phase(tab)
    if phase not in MYBC_RESUME_PHASES:
        return None

    labels: dict[str, str] = {
        PHASE_MYBC_POST_LOGON: "Student Post-Logon myBC (politiques a accepter)",
        PHASE_MYBC_STUDENT_HOME: "myBC Student Home (politiques deja acceptees)",
        PHASE_PORTAL: "portail OneLogin (/portal)",
        PHASE_MYBC_OTHER: "myBC (redirection Student Post-Logon)",
    }
    log(f"  Reprise compte partiellement active — {labels.get(phase, phase)} detecte.")
    log("  Etapes MFA / changement MDP ignorees — suite vers myBC.")
    if resume_tab is not None:
        await resume_tab.activate()
        return resume_tab
    return tab


async def submit_microsoft_school_login(
    tab: Any,
    school_email: str,
    temp_password: str,
    log: LogFn,
    *,
    fallback_password: str = "",
) -> tuple[Any, bool]:
    """
    Apres OneLogin username : redirection Microsoft ConvergedSignIn.
    Saisit l'email @mail.broward.edu puis le mot de passe temporaire MMYYYY@BCProud!.
    Essaie le mot de passe ecole actuel en repli si le temporaire est refuse.
    """
    if not temp_password and not fallback_password:
        raise RuntimeError("Mot de passe temporaire MMYYYY@BCProud! introuvable (date de naissance invalide).")

    password_candidates: list[str] = []
    if temp_password:
        password_candidates.append(temp_password)
    if fallback_password and fallback_password not in password_candidates:
        password_candidates.append(fallback_password)

    attempts: int = max(1, int(ONELOGIN_TIMEOUT_S / 1.0))
    active_tab: Any = tab
    password_attempt_index: int = 0
    used_bcproud_password: bool = False

    for i in range(attempts):
        resume_tab: Any | None = await _try_resume_mybc_entry(active_tab, log)
        if resume_tab is not None:
            return resume_tab, False

        ms_tab, state = await _find_microsoft_login_tab(active_tab)
        if ms_tab is None:
            await active_tab.sleep(1.0)
            if i > 0 and i % 15 == 0:
                log(f"  Attente page Microsoft ConvergedSignIn ({i}/{attempts})...")
            continue

        await ms_tab.activate()
        active_tab = ms_tab
        step: str = str(state.get("step") or "other")

        if step == "username":
            log(f"  Microsoft : saisie email ecole {school_email}...")
            if not await fill_microsoft_login_field(ms_tab, "username", school_email):
                raise RuntimeError("Impossible de remplir l'email ecole sur Microsoft (#i0116).")
            if not await click_microsoft_primary(ms_tab):
                raise RuntimeError("Bouton Suivant Microsoft introuvable (#idSIButton9).")
            log("  Microsoft : Suivant clique.")
            await ms_tab.sleep(2.5)
            continue

        if step == "password":
            current_password: str = password_candidates[min(password_attempt_index, len(password_candidates) - 1)]
            if password_attempt_index == 0 and current_password == temp_password and temp_password:
                log(
                    "  Microsoft : saisie mot de passe temporaire (MMYYYY@BCProud!) "
                    "— compte jamais active.",
                )
            elif password_attempt_index == 0:
                log("  Microsoft : saisie mot de passe ecole (compte deja active)...")
            else:
                log(
                    "  Microsoft : mot de passe temporaire refuse — "
                    "essai mot de passe Outlook (compte deja partiellement active)...",
                )
            if not await fill_microsoft_login_field(ms_tab, "password", current_password):
                raise RuntimeError("Impossible de remplir le mot de passe Microsoft (#i0118).")
            if not await click_microsoft_primary(ms_tab):
                raise RuntimeError("Bouton Se connecter Microsoft introuvable (#idSIButton9).")
            log("  Microsoft : mot de passe soumis.")
            await ms_tab.sleep(3.0)

            used_bcproud_password = (
                bool(temp_password)
                and current_password == temp_password
                and password_attempt_index == 0
            )

            resume_tab = await _try_resume_mybc_entry(ms_tab, log)
            if resume_tab is not None:
                return resume_tab, False

            ms_tab_after, state_after = await _find_microsoft_login_tab(ms_tab)
            if (
                ms_tab_after is not None
                and str(state_after.get("step") or "") == "password"
                and password_attempt_index + 1 < len(password_candidates)
            ):
                password_attempt_index += 1
                log("  Mot de passe refuse — nouvel essai...")
                continue

            return ms_tab, used_bcproud_password

        await active_tab.sleep(1.0)

    raise RuntimeError(
        "Connexion Microsoft BC One Access non terminee (email ecole / mot de passe temporaire).",
    )


async def _read_proof_up_redirect_state(tab: Any) -> dict[str, Any]:
    """Detecte la page Microsoft ConvergedProofUpRedirect (« Securisons votre compte »)."""
    return await js_eval_json(
        tab,
        """
            const pageId = document.querySelector('meta[name="PageID"]');
            const pgid = ((pageId && pageId.getAttribute('content')) || '').trim();
            const heading = document.querySelector('#heading');
            const headingText = ((heading && heading.textContent) || '').trim().toLowerCase();
            const btn = document.querySelector('#idSubmit_ProofUp_Redirect');
            const visible = (el) => {
                if (!el) return false;
                if (el.disabled || el.getAttribute('aria-disabled') === 'true') return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 4 && rect.height > 4;
            };
            const isProofUpRedirect =
                pgid === 'ConvergedProofUpRedirect'
                || headingText.includes('sécurisons votre compte')
                || headingText.includes('securisons votre compte')
                || headingText.includes('secure your account');
            return {
                isProofUpRedirect,
                hasNext: !!(btn && visible(btn)),
                pgid,
                heading: headingText.slice(0, 80),
                url: (location.href || '').slice(0, 120),
                host: location.hostname || '',
            };
        """,
    )


async def _find_tab_with_proof_up_redirect(
    tab: Any,
    *,
    require_button: bool = True,
) -> tuple[Any | None, dict[str, Any]]:
    """Retourne l'onglet ConvergedProofUpRedirect (optionnellement avec bouton Suivant visible)."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            state: dict[str, Any] = await _read_proof_up_redirect_state(candidate)
        except Exception:  # noqa: BLE001
            continue
        if not state.get("isProofUpRedirect"):
            continue
        if require_button and not state.get("hasNext"):
            continue
        return candidate, state
    return None, {}


async def _read_converged_error_state(tab: Any) -> dict[str, Any]:
    """Detecte la page Microsoft ConvergedError (ex. AADSTS90100)."""
    return await js_eval_json(
        tab,
        """
            const pageId = document.querySelector('meta[name="PageID"]');
            const pgid = ((pageId && pageId.getAttribute('content')) || '').trim();
            const errEl = document.querySelector('#exceptionMessageContainer');
            const errText = ((errEl && errEl.textContent) || '').trim();
            const config = window.$Config || window.ServerData || {};
            const serviceMsg = String(
                config.strServiceExceptionMessage || config.sErrTxt || errText || '',
            ).trim();
            const combined = (errText || serviceMsg).toLowerCase();
            const codeMatch = combined.match(/aadsts\\d+/i);
            return {
                isConvergedError: pgid === 'ConvergedError' || combined.includes('aadsts'),
                pgid,
                errorMessage: (errText || serviceMsg).slice(0, 200),
                errorCode: codeMatch ? codeMatch[0].toUpperCase() : '',
                url: (location.href || '').slice(0, 120),
            };
        """,
    )


async def _find_tab_with_converged_error(tab: Any) -> tuple[Any | None, dict[str, Any]]:
    """Retourne l'onglet ConvergedError Microsoft si present."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            state: dict[str, Any] = await _read_converged_error_state(candidate)
        except Exception:  # noqa: BLE001
            continue
        if state.get("isConvergedError"):
            return candidate, state
    return None, {}


async def _click_proof_up_redirect_button(tab: Any) -> bool:
    """Clique Suivant sur ConvergedProofUpRedirect (Knockout — pas de form.submit())."""
    return await js_eval_bool(
        tab,
        """
        () => {
            const btn = document.querySelector('#idSubmit_ProofUp_Redirect');
            if (!btn || btn.disabled || btn.getAttribute('aria-disabled') === 'true') {
                return false;
            }
            btn.scrollIntoView({ block: 'center' });
            btn.focus();
            btn.click();
            return true;
        }
        """,
    )


async def _browser_back_to_onelogin(tab: Any, log: LogFn, *, max_steps: int = 12) -> Any:
    """Recule dans l'historique jusqu'a retrouver OneLogin / BC One Access."""
    active_tab: Any = tab

    for step in range(max_steps):
        try:
            url: str = (await _read_tab_url(active_tab)).lower()
        except Exception:  # noqa: BLE001
            url = ""

        if "onelogin.com" in url:
            log(f"  BC One Access (OneLogin) retrouve apres {step} retour(s) arriere.")
            return active_tab

        await js_eval_bool(
            active_tab,
            """
            () => {
                window.history.back();
                return true;
            }
            """,
        )
        await active_tab.sleep(2.5)

        for candidate in await _iter_browser_tabs(active_tab):
            try:
                candidate_url: str = (await _read_tab_url(candidate)).lower()
            except Exception:  # noqa: BLE001
                continue
            if "onelogin.com" in candidate_url:
                await candidate.activate()
                active_tab = candidate
                log(f"  BC One Access (OneLogin) retrouve apres {step + 1} retour(s) arriere.")
                return active_tab

    log("  OneLogin non retrouve par retour arriere — onglet courant conserve.")
    return active_tab


async def _recover_fresh_bcproud_via_onelogin_back(
    tab: Any,
    school_email: str,
    temp_password: str,
    fallback_password: str,
    log: LogFn,
) -> Any:
    """Reprend le flux compte neuf apres ConvergedError : retour BC One Access + reconnexion."""
    error_tab, error_state = await _find_tab_with_converged_error(tab)
    error_code: str = str(error_state.get("errorCode") or "")
    error_message: str = str(error_state.get("errorMessage") or "")
    log(
        f"  Erreur Microsoft {error_code or 'ConvergedError'} detectee"
        f"{f' : {error_message[:80]}' if error_message else ''}.",
    )
    log("  Retour BC One Access et nouvelle tentative (mot de passe BCProud)...")

    recovery_tab: Any = error_tab if error_tab is not None else tab
    recovery_tab = await _browser_back_to_onelogin(recovery_tab, log)

    username_state: dict[str, Any] = await _read_onelogin_username_screen(recovery_tab)
    if username_state.get("hasUsername"):
        await submit_bc_one_access_username(recovery_tab, school_email, log)

    ms_tab, _used_bcproud = await submit_microsoft_school_login(
        recovery_tab,
        school_email,
        temp_password,
        log,
        fallback_password=fallback_password,
    )
    return ms_tab


async def _wait_for_post_proof_up_navigation(tab: Any, log: LogFn) -> str:
    """
    Attend la redirection ProofUp -> My Sign-Ins apres le clic Suivant.
    Retourne la phase detectee (mysignins, ms_error, proof_up, other).
    """
    attempts: int = max(1, int(MFA_SETUP_TIMEOUT_S / 1.0))
    for i in range(attempts):
        _route_tab, phase, _state = await _detect_flow_resume_phase(tab)
        if phase == PHASE_MYSIGNINS:
            log("  Redirection My Sign-Ins detectee apres ProofUp.")
            return phase
        if phase == PHASE_MS_ERROR:
            log("  Erreur Microsoft detectee apres clic ProofUp.")
            return phase
        if phase not in (PHASE_PROOF_UP, PHASE_UNKNOWN):
            return phase
        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente redirection My Sign-Ins apres ProofUp ({i}/{attempts})...")
    return PHASE_UNKNOWN


async def submit_proof_up_redirect(tab: Any, log: LogFn) -> Any:
    """
    Apres le mot de passe temporaire : page ConvergedProofUpRedirect.
    Clique Suivant (#idSubmit_ProofUp_Redirect) pour lancer l'enregistrement MFA.
    """
    log("Etape 6/12 — Securisons votre compte (ConvergedProofUpRedirect)...")
    attempts: int = max(1, int(MFA_SETUP_TIMEOUT_S / 1.0))
    active_tab: Any = tab

    for i in range(attempts):
        resume_tab: Any | None = await _try_resume_mybc_entry(active_tab, log)
        if resume_tab is not None:
            return resume_tab

        proof_tab, state = await _find_tab_with_proof_up_redirect(active_tab, require_button=False)
        if proof_tab is None or not state.get("hasNext"):
            await active_tab.sleep(1.0)
            if i > 0 and i % 15 == 0:
                log(f"  Attente page ConvergedProofUpRedirect ({i}/{attempts})...")
            continue

        await proof_tab.activate()
        clicked: bool = await _click_proof_up_redirect_button(proof_tab)
        if not clicked:
            raise RuntimeError("Bouton Suivant ConvergedProofUpRedirect introuvable (#idSubmit_ProofUp_Redirect).")

        log("  ConvergedProofUpRedirect : Suivant clique.")
        await proof_tab.sleep(3.0)
        post_phase: str = await _wait_for_post_proof_up_navigation(proof_tab, log)
        if post_phase == PHASE_MS_ERROR:
            raise RuntimeError(
                "ConvergedError Microsoft apres ProofUp (AADSTS90100) — reprise BC One Access requise.",
            )
        return proof_tab

    raise RuntimeError("Page ConvergedProofUpRedirect introuvable apres soumission du mot de passe temporaire.")


async def _read_mysignins_register_state(tab: Any) -> dict[str, Any]:
    """Detecte l'etape courante du wizard My Sign-Ins Register (mysignins.microsoft.com)."""
    return await js_eval_json(
        tab,
        """
            const title = document.querySelector('[data-testid="reskin-step-title"]');
            const titleText = ((title && title.textContent) || '').trim().toLowerCase();
            const nextBtn = document.querySelector('[data-testid="reskin-step-next-button"]');
            const setupInstructions = document.querySelector('[data-testid="setup-instructions"]');
            const visible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 4 && rect.height > 4;
            };
            const downloadLinks = document.querySelector('[data-testid="authenticator-download-link"]');
            let step = 'other';
            if (
                titleText.includes('installer microsoft authenticator')
                || titleText.includes('install microsoft authenticator')
                || !!downloadLinks
            ) {
                step = 'install_app';
            } else if (
                titleText.includes('configurer votre compte')
                || titleText.includes('set up your account')
                || titleText.includes('configure your account')
                || !!setupInstructions
            ) {
                step = 'setup_account';
            } else if (
                titleText.includes('authenticator added')
                || titleText.includes('authenticator ajout')
                || titleText.includes('méthode de connexion par défaut')
                || titleText.includes('default sign-in method')
            ) {
                step = 'authenticator_added';
            }
            const automatedSteps = ['install_app', 'setup_account'];
            return {
                step,
                isAutomatedStep: automatedSteps.includes(step),
                hasNext: !!(nextBtn && visible(nextBtn)),
                title: titleText.slice(0, 120),
                url: (location.href || '').slice(0, 120),
                host: (location.hostname || '').toLowerCase(),
            };
        """,
    )


async def _find_tab_with_mysignins_step(
    tab: Any,
    step_id: str,
    *,
    require_next: bool = True,
) -> tuple[Any | None, dict[str, Any]]:
    """Retourne l'onglet mysignins sur une etape donnee du wizard Register."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            url: str = await _read_tab_url(candidate)
        except Exception:  # noqa: BLE001
            continue
        if "mysignins.microsoft.com" not in url.lower():
            continue
        try:
            state: dict[str, Any] = await _read_mysignins_register_state(candidate)
        except Exception:  # noqa: BLE001
            continue
        if str(state.get("step") or "") != step_id:
            continue
        if require_next and not state.get("hasNext"):
            continue
        return candidate, state
    return None, {}


async def _find_tab_with_mysignins_automated_step(tab: Any) -> tuple[Any | None, dict[str, Any]]:
    """Retourne l'onglet mysignins sur une etape automatisable (install / setup)."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            url: str = await _read_tab_url(candidate)
        except Exception:  # noqa: BLE001
            continue
        if "mysignins.microsoft.com" not in url.lower():
            continue
        try:
            state: dict[str, Any] = await _read_mysignins_register_state(candidate)
        except Exception:  # noqa: BLE001
            continue
        if state.get("isAutomatedStep") and state.get("hasNext"):
            return candidate, state
    return None, {}


async def _read_converged_tfa_state(tab: Any) -> dict[str, Any]:
    """Detecte la page Microsoft ConvergedTFA (approbation Authenticator)."""
    return await js_eval_json(
        tab,
        """
            const pageId = document.querySelector('meta[name="PageID"]');
            const pgid = ((pageId && pageId.getAttribute('content')) || '').trim();
            const title = document.querySelector('#idDiv_SAOTCAS_Title');
            const visible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 4 && rect.height > 4;
            };
            const hasTitle = !!(title && visible(title));
            return {
                isConvergedTFA: pgid === 'ConvergedTFA' || hasTitle,
                pgid,
                title: ((title && title.textContent) || '').trim().slice(0, 120),
                url: (location.href || '').slice(0, 120),
                host: location.hostname || '',
            };
        """,
    )


async def _find_tab_with_converged_tfa(tab: Any) -> tuple[Any | None, dict[str, Any]]:
    """Retourne l'onglet ConvergedTFA (approbation push Authenticator)."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            url: str = await _read_tab_url(candidate)
        except Exception:  # noqa: BLE001
            continue
        if "login.microsoftonline.com" not in url.lower():
            continue
        try:
            state: dict[str, Any] = await _read_converged_tfa_state(candidate)
        except Exception:  # noqa: BLE001
            continue
        if state.get("isConvergedTFA"):
            return candidate, state
    return None, {}


async def _click_mysignins_next_button(tab: Any) -> bool:
    """Clique Suivant sur une page My Sign-Ins Register."""
    return await js_eval_bool(
        tab,
        """
        () => {
            const btn = document.querySelector('[data-testid="reskin-step-next-button"]');
            if (!btn || btn.disabled || btn.getAttribute('aria-disabled') === 'true') {
                return false;
            }
            btn.scrollIntoView({ block: 'center' });
            btn.focus();
            btn.click();
            const label = btn.querySelector('.ms-Button-label, [id^="id__"]');
            if (label) {
                label.click();
            }
            return true;
        }
        """,
    )


async def advance_mysignins_register_steps(tab: Any, log: LogFn) -> Any:
    """
    Enchaine les etapes automatiques My Sign-Ins Register apres ConvergedProofUpRedirect :
    - Installer Microsoft Authenticator
    - Configurer votre compte dans l'application
    Puis laisse l'etape QR au manuel.
    """
    step_labels: dict[str, tuple[int, str]] = {
        "install_app": (7, "Installer Microsoft Authenticator"),
        "setup_account": (8, "Configurer votre compte dans l'application"),
    }
    completed_steps: set[str] = set()
    active_tab: Any = tab
    attempts_per_step: int = max(1, int(MFA_SETUP_TIMEOUT_S / 1.0))

    wait_attempts: int = 0
    max_wait_attempts: int = attempts_per_step * len(step_labels)

    while len(completed_steps) < len(step_labels):
        resume_tab: Any | None = await _try_resume_mybc_entry(active_tab, log)
        if resume_tab is not None:
            return resume_tab

        ms_tab, state = await _find_tab_with_mysignins_automated_step(active_tab)
        current_step: str = str(state.get("step") or "")

        if ms_tab is None or current_step not in step_labels or current_step in completed_steps:
            wait_attempts += 1
            if wait_attempts > max_wait_attempts:
                pending: str = ", ".join(
                    step_labels[step_id][1]
                    for step_id in step_labels
                    if step_id not in completed_steps
                )
                raise RuntimeError(
                    f"Etapes My Sign-Ins automatiques introuvables ({pending}).",
                )
            await active_tab.sleep(1.0)
            if wait_attempts > 0 and wait_attempts % 15 == 0:
                log(f"  Attente etapes My Sign-Ins auto ({wait_attempts}/{max_wait_attempts})...")
            continue

        wait_attempts = 0
        step_num, step_label = step_labels[current_step]
        log(f"Etape {step_num}/12 — {step_label} (My Sign-Ins)...")

        clicked: bool = False
        for i in range(attempts_per_step):
            resume_tab = await _try_resume_mybc_entry(active_tab, log)
            if resume_tab is not None:
                return resume_tab

            ms_tab, state = await _find_tab_with_mysignins_automated_step(active_tab)
            current_step = str(state.get("step") or "")
            if ms_tab is None or current_step not in step_labels or current_step in completed_steps:
                await active_tab.sleep(1.0)
                if i > 0 and i % 15 == 0:
                    log(f"  Attente page « {step_label} » ({i}/{attempts_per_step})...")
                continue

            await ms_tab.activate()
            if not await _click_mysignins_next_button(ms_tab):
                raise RuntimeError(
                    f"Bouton Suivant introuvable sur « {step_label} » "
                    "(data-testid=reskin-step-next-button).",
                )

            log(f"  My Sign-Ins : Suivant clique (« {step_label} »).")
            await ms_tab.sleep(3.0)
            active_tab = ms_tab
            completed_steps.add(current_step)
            clicked = True
            break

        if not clicked:
            raise RuntimeError(
                f"Page « {step_label} » (mysignins.microsoft.com) introuvable "
                "dans le flux d'enregistrement MFA.",
            )

    return active_tab


async def complete_post_qr_mfa_flow(tab: Any, log: LogFn) -> Any:
    """
    Apres les etapes auto My Sign-Ins (install + setup) :
    1. Manuel : scan QR jusqu'a « Authenticator Added »
    2. Auto : clic Termine sur My Sign-Ins
    3. Manuel : approbation ConvergedTFA (push Authenticator)
    4. Reprise auto sur ConvergedChangePassword
    """
    log("Etape 9/12 — Scan QR Microsoft Authenticator : intervention MANUELLE.")
    log("  Scannez le QR code dans l'application jusqu'a « Authenticator Added ».")

    attempts: int = max(1, int(MANUAL_MFA_TIMEOUT_S / 2.0))
    active_tab: Any = tab
    done_clicked: bool = False
    tfa_phase_logged: bool = False

    for i in range(attempts):
        resume_tab: Any | None = await _try_resume_mybc_entry(active_tab, log)
        if resume_tab is not None:
            return resume_tab

        added_tab, _added_state = await _find_tab_with_mysignins_step(
            active_tab,
            "authenticator_added",
        )
        if added_tab is not None and not done_clicked:
            await added_tab.activate()
            if not await _click_mysignins_next_button(added_tab):
                raise RuntimeError(
                    "Bouton « Termine » introuvable sur « Authenticator Added » "
                    "(data-testid=reskin-step-next-button).",
                )
            log("Etape 10/12 — Authenticator Added : Termine clique (My Sign-Ins).")
            await added_tab.sleep(3.0)
            active_tab = added_tab
            done_clicked = True
            tfa_phase_logged = False
            continue

        change_tab, cp_state = await _find_tab_with_change_password(active_tab)
        if change_tab is not None:
            pgid: str = str(cp_state.get("pgid") or "ConvergedChangePassword")
            log(f"  Page changement de mot de passe detectee ({pgid}) — reprise automatique.")
            await change_tab.activate()
            return change_tab

        tfa_tab, tfa_state = await _find_tab_with_converged_tfa(active_tab)
        if tfa_tab is not None:
            if not tfa_phase_logged:
                title: str = str(tfa_state.get("title") or "Approuver la demande de connexion")
                log("Etape 11/12 — ConvergedTFA : intervention MANUELLE.")
                log(f"  {title} — approuvez la demande dans Microsoft Authenticator.")
                tfa_phase_logged = True
            await tfa_tab.activate()
            active_tab = tfa_tab

        await active_tab.sleep(2.0)
        if i > 0 and i % 15 == 0:
            elapsed_s: int = i * 2
            if not done_clicked:
                log(
                    f"  Attente scan QR / « Authenticator Added » "
                    f"({elapsed_s}s / {int(MANUAL_MFA_TIMEOUT_S)}s)...",
                )
            elif tfa_phase_logged:
                log(
                    f"  Attente approbation ConvergedTFA "
                    f"({elapsed_s}s / {int(MANUAL_MFA_TIMEOUT_S)}s)...",
                )
            else:
                log(
                    f"  Attente transition post-MFA "
                    f"({elapsed_s}s / {int(MANUAL_MFA_TIMEOUT_S)}s)...",
                )

    raise RuntimeError(
        f"Page changement de mot de passe Microsoft introuvable apres {int(MANUAL_MFA_TIMEOUT_S)}s "
        "(MFA / ConvergedTFA non termine ?).",
    )


async def submit_microsoft_change_password(
    tab: Any,
    temp_password: str,
    new_password: str,
    log: LogFn,
) -> Any:
    """Remplit ConvergedChangePassword et soumet le formulaire."""
    log("Etape 12/12 — Changement de mot de passe ecole...")
    attempts: int = max(1, int(CHANGE_PASSWORD_TIMEOUT_S / 1.0))

    for i in range(attempts):
        resume_tab: Any | None = await _try_resume_mybc_entry(tab, log)
        if resume_tab is not None:
            return resume_tab

        change_tab, state = await _find_tab_with_change_password(tab)
        active_tab: Any = change_tab if change_tab is not None else tab

        if state.get("isChangePassword") and state.get("hasCurrent"):
            if change_tab is not None:
                await change_tab.activate()

            if not await fill_microsoft_visible_input(
                active_tab,
                "#currentPassword, input[name='currentpasswd']",
                temp_password,
            ):
                raise RuntimeError("Champ « Mot de passe actuel » introuvable.")

            if not await fill_microsoft_visible_input(
                active_tab,
                "#newPassword, input[name='newpasswd']",
                new_password,
            ):
                raise RuntimeError("Champ « Nouveau mot de passe » introuvable.")

            if not await fill_microsoft_visible_input(
                active_tab,
                "#confirmNewPassword, input[name='confirmnewpasswd']",
                new_password,
            ):
                raise RuntimeError("Champ « Confirmer le mot de passe » introuvable.")

            clicked: bool = await click_microsoft_primary(active_tab)
            if not clicked:
                clicked = await js_eval_bool(
                    active_tab,
                    """
                    () => {
                        const btn = document.querySelector('#idSIButton9, input[type="submit"].win-button');
                        if (!btn) return false;
                        btn.scrollIntoView({ block: 'center' });
                        btn.click();
                        return true;
                    }
                    """,
                )
            if not clicked:
                raise RuntimeError("Bouton « Se connecter » (changement mot de passe) introuvable.")

            log("  Mot de passe ecole mis a jour (identique au mot de passe Outlook enregistre).")
            await active_tab.sleep(3.0)

            portal_wait_attempts: int = 15
            for _pw_wait in range(portal_wait_attempts):
                portal_tab: Any | None = await _find_onelogin_portal_tab(active_tab)
                if portal_tab is not None:
                    await portal_tab.activate()
                    return portal_tab
                try:
                    current_url: str = (await _read_tab_url(active_tab)).lower()
                except Exception:  # noqa: BLE001
                    current_url = ""
                if "onelogin.com/portal" in current_url:
                    return active_tab
                await active_tab.sleep(1.0)

            return active_tab

        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente formulaire changement de mot de passe ({i}/{attempts})...")

    raise RuntimeError("Formulaire changement de mot de passe Microsoft introuvable ou non soumis.")


async def _click_mybc_submit_by_value(tab: Any, value_patterns: list[str]) -> bool:
    """Clique un bouton/input submit ou button dont la valeur correspond aux motifs."""
    patterns_json: str = json.dumps([p.lower() for p in value_patterns])
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            const patterns = {patterns_json};
            const norm = (value) => (value || '').trim().toLowerCase();
            const matches = (value) => patterns.some((pattern) => {{
                const normalized = norm(value);
                return normalized.includes(pattern) || pattern.includes(normalized);
            }});
            const controls = Array.from(
                document.querySelectorAll('input[type="submit"], input[type="button"], button'),
            );
            for (const el of controls) {{
                const label = el.value || el.textContent || '';
                if (!matches(label)) continue;
                el.scrollIntoView({{ block: 'center' }});
                el.click();
                return true;
            }}
            return false;
        }}
        """,
    )


async def _read_mybc_post_logon_state(tab: Any) -> dict[str, Any]:
    """Detecte la page Student Post-Logon myBC."""
    return await js_eval_json(
        tab,
        """
            const url = (location.href || '').toLowerCase();
            const body = (document.body?.innerText || '').toLowerCase();
            const table = document.querySelector('table.fccsc-border');
            const pending = document.querySelectorAll('img[src*="check_no"]').length;
            const isPostLogon =
                url.includes('studentpostlogon')
                || !!table
                || body.includes('policy / request')
                || body.includes('politique / demande')
                || body.includes('require your review')
                || body.includes('necessitent votre examen');
            return {
                isPostLogon,
                pendingCount: pending,
                url: (location.href || '').slice(0, 140),
                host: location.hostname || '',
            };
        """,
    )


async def _is_mybc_post_logon_page(tab: Any) -> bool:
    """True si l'onglet affiche la liste des politiques post-logon."""
    state: dict[str, Any] = await _read_mybc_post_logon_state(tab)
    return bool(state.get("isPostLogon"))


async def _read_mybc_student_home_state(tab: Any) -> dict[str, Any]:
    """Detecte la page Student Home myBC (ias900n1.jsp — politiques deja validees)."""
    return await js_eval_json(
        tab,
        """
            const url = (location.href || '').toLowerCase();
            const body = (document.body?.innerText || '').toLowerCase();
            const title = (document.title || '').toLowerCase();
            const hasDetails = !!document.querySelector('#myDetailsBoxBox, #myQuickLinksBoxBox');
            const hasFinancialSummary = body.includes('my financial summary');
            const isStudentHome =
                url.includes('ias900n1.jsp')
                || url.includes('iau090n0s')
                || (
                    hasDetails
                    && hasFinancialSummary
                    && (title.includes('student home') || body.includes('quick links'))
                );
            return {
                isStudentHome,
                url: (location.href || '').slice(0, 140),
            };
        """,
    )


async def _is_mybc_student_home_page(tab: Any) -> bool:
    """True si l'onglet affiche myBC Student Home (CGU deja acceptees)."""
    state: dict[str, Any] = await _read_mybc_student_home_state(tab)
    return bool(state.get("isStudentHome"))


async def _wait_for_student_home_loaded(tab: Any, log: LogFn) -> None:
    """Attend que Student Home (ias900n1.jsp) soit entierement charge avant prep DOM."""
    attempts: int = max(1, int(MYBC_SCREENSHOT_LOAD_TIMEOUT_S / 1.0))
    for attempt in range(attempts):
        state: dict[str, Any] = await js_eval_json(
            tab,
            """
            () => {
                const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const url = (location.href || '').toLowerCase();
                const ready = document.readyState === 'complete';
                const hasPanels = !!(
                    document.querySelector('#myDetailsBoxBox')
                    && document.querySelector('#myQuickLinksBoxBox')
                );
                const bodyText = document.body?.innerText || '';
                const hasFinancial = bodyText.toLowerCase().includes('my financial summary');
                const hasDetails = bodyText.toLowerCase().includes('my details');

                let studentIdValue = '';
                let primaryObjectiveValue = '';
                let termRowReady = false;

                const detailsBox = document.querySelector('#myDetailsBoxBox');
                const finTable = detailsBox
                    ? Array.from(detailsBox.querySelectorAll(':scope > table')).find((table) =>
                        (table.textContent || '').includes('my Financial Summary'),
                    )
                    : null;
                if (finTable) {
                    const finText = normalize(finTable.textContent);
                    termRowReady = /Summer\\s+20\\d{2}/i.test(finText) || /Fall\\s+20\\d{2}/i.test(finText);
                }

                for (const row of Array.from(
                    detailsBox ? detailsBox.querySelectorAll('tr') : document.querySelectorAll('tr'),
                )) {
                    const cells = row.querySelectorAll('td');
                    if (cells.length < 2) continue;
                    const label = normalize(cells[0].textContent).toLowerCase();
                    const value = normalize(cells[1].textContent);
                    if (label.includes('student id') && value.length >= 4) {
                        studentIdValue = value;
                    }
                    if (label.includes('primary objective') && value.length >= 3) {
                        primaryObjectiveValue = value;
                    }
                }

                const quickLinksReady = Array.from(
                    document.querySelectorAll('#myQuickLinksBoxBox a, #myQuickLinksBoxBox .frontpage'),
                ).length >= 3;

                const bodyBroken = (
                    normalize(bodyText).toLowerCase() === 'null'
                    || bodyText.toLowerCase().includes('access denied')
                    || bodyText.toLowerCase().includes('not logged in')
                );
                const onStudentHomeView = (
                    url.includes('ias900n1.jsp')
                    || url.includes('iau090n0s')
                    || (hasPanels && hasFinancial && hasDetails)
                );
                const loaded = (
                    !bodyBroken
                    && onStudentHomeView
                    && ready
                    && hasPanels
                    && hasFinancial
                    && hasDetails
                    && !!studentIdValue
                    && !!primaryObjectiveValue
                    && termRowReady
                    && quickLinksReady
                );

                return {
                    loaded,
                    bodyBroken,
                    onStudentHomeView,
                    ready,
                    hasPanels,
                    studentIdValue: studentIdValue.slice(0, 24),
                    primaryObjectiveValue: primaryObjectiveValue.slice(0, 48),
                    termRowReady,
                    quickLinksReady,
                    url: url.slice(0, 120),
                };
            }
            """,
        )
        if state.get("loaded"):
            if attempt > 0:
                log(f"  Student Home charge apres {attempt + 1}s ({state.get('url', '')}).")
            return
        if attempt > 0 and attempt % 10 == 0:
            log(
                "  Attente Student Home..."
                f" broken={state.get('bodyBroken')},"
                f" panels={state.get('hasPanels')},"
                f" studentId={bool(state.get('studentIdValue'))}",
            )
        await tab.sleep(1.0)

    raise RuntimeError("Page myBC Student Home non entierement chargee (menu myBC Home requis).")


async def _prepare_mybc_student_home_dom_for_screenshot(tab: Any, log: LogFn) -> None:
    """
    Modifie uniquement les sous-tables directes de #myDetailsBoxBox.
    Ne jamais toucher au <td id=\"myDetailsBoxBox\"> ni a la table 740px parente.
    """
    objective_json: str = json.dumps(MYBC_PRIMARY_OBJECTIVE_DISPLAY)
    state: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        () => {{
            const objectiveText = {objective_json};
            const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();

            document.querySelectorAll('#alert-modal, #important-modal').forEach((el) => el.remove());
            document.querySelectorAll('.overlay').forEach((el) => {{
                if (el.id === 'alert-modal' || el.id === 'important-modal') el.remove();
            }});

            let removedOutstanding = 0;
            let replacedEnrollment = 0;
            let removedPayButton = 0;
            let removedImportantInfo = 0;
            let replacedObjective = 0;
            let removedBr = 0;

            const detailsBox = document.querySelector('#myDetailsBoxBox');
            if (!detailsBox) {{
                return {{
                    removedOutstanding,
                    replacedEnrollment,
                    removedPayButton,
                    removedImportantInfo,
                    replacedObjective,
                    removedBr,
                    quickLinksIntact: !!document.querySelector('#myQuickLinksBoxBox a'),
                    detailsIntact: false,
                }};
            }}

            const directTables = Array.from(detailsBox.children).filter(
                (el) => el.tagName === 'TABLE',
            );

            const finTable = directTables.find((table) =>
                normalize(table.textContent).includes('my Financial Summary'),
            );

            if (finTable) {{
                finTable.querySelectorAll('tr').forEach((row) => {{
                    const rowText = normalize(row.textContent);
                    if (rowText.includes('Total Outstanding')) {{
                        row.remove();
                        removedOutstanding += 1;
                        return;
                    }}
                    const cells = row.querySelectorAll('td');
                    if (cells.length < 2) return;
                    for (let index = 1; index < cells.length; index += 1) {{
                        const dueText = normalize(cells[index].textContent);
                        if (dueText.includes('Not Enrolled')) {{
                            cells[index].textContent = 'Enrolled';
                            replacedEnrollment += 1;
                        }}
                    }}
                }});

                let afterFin = false;
                for (const child of Array.from(detailsBox.childNodes)) {{
                    if (child === finTable) {{
                        afterFin = true;
                        continue;
                    }}
                    if (!afterFin) continue;
                    if (removedBr >= 2) break;
                    if (child.nodeType === Node.ELEMENT_NODE && child.nodeName === 'BR') {{
                        child.remove();
                        removedBr += 1;
                    }}
                }}
            }}

            directTables.forEach((table) => {{
                if (table === finTable) return;
                const tableText = normalize(table.textContent);
                const payButton = table.querySelector('button[onclick*="IAC061N0s"]');
                if (
                    payButton
                    || tableText.includes('Pay for Additional Items Now')
                ) {{
                    table.remove();
                    removedPayButton += 1;
                    return;
                }}
                if (tableText.includes('Important Information:')) {{
                    table.remove();
                    removedImportantInfo += 1;
                }}
            }});

            const myDetailsTable = Array.from(detailsBox.children)
                .filter((el) => el.tagName === 'TABLE')
                .find((table) => normalize(table.textContent).includes('My Details'));

            if (myDetailsTable) {{
                myDetailsTable.querySelectorAll('tr').forEach((row) => {{
                    const cells = row.querySelectorAll('td');
                    if (cells.length < 2) return;
                    const label = normalize(cells[0].textContent);
                    if (!label.includes('Primary Objective')) return;
                    cells[1].textContent = objectiveText;
                    replacedObjective += 1;
                }});
            }}

            const quickLinksIntact =
                document.querySelectorAll('#myQuickLinksBoxBox a, #myQuickLinksBoxBox .frontpage').length >= 3;
            const detailsIntact = normalize(detailsBox.textContent).includes('Student ID:');

            return {{
                removedOutstanding,
                replacedEnrollment,
                removedPayButton,
                removedImportantInfo,
                replacedObjective,
                removedBr,
                quickLinksIntact,
                detailsIntact,
            }};
        }}
        """,
    )
    log(
        "  DOM Student Home prepare :"
        f" outstanding={state.get('removedOutstanding', 0)},"
        f" enrolled={state.get('replacedEnrollment', 0)},"
        f" pay={state.get('removedPayButton', 0)},"
        f" info={state.get('removedImportantInfo', 0)},"
        f" objective={state.get('replacedObjective', 0)},"
        f" br={state.get('removedBr', 0)}",
    )

    if not state.get("quickLinksIntact"):
        raise RuntimeError("DOM Student Home : Quick Links endommages apres preparation.")
    if not state.get("detailsIntact"):
        raise RuntimeError("DOM Student Home : bloc My Details endommage apres preparation.")
    if int(state.get("replacedEnrollment") or 0) < 1:
        raise RuntimeError("DOM Student Home : statut « Not Enrolled » non remplace.")
    if int(state.get("replacedObjective") or 0) < 1:
        raise RuntimeError("DOM Student Home : Primary Objective non remplace.")


async def _navigate_to_mybc_home_via_menu(tab: Any, log: LogFn) -> None:
    """
    Ouvre Student Home via le menu myBC (myBC Home → IAU090N0s).
    La navigation directe vers ias900n1.jsp peut afficher un DOM vide (« null »).
    """
    log("  Menu myBC Home (IAU090N0s)...")
    clicked: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        () => {{
            const homePath = {json.dumps(MYBC_HOME_SERVLET_PATH)};
            const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();

            const homeLink = document.querySelector(
                '#student-menu li.first a[href*="security.IAU090N0s"],'
                + '#student-menu a[href*="IAU090N0s"]',
            ) || Array.from(document.querySelectorAll('#student-menu a')).find((anchor) => {{
                const href = anchor.getAttribute('href') || '';
                const label = normalize(anchor.textContent).toLowerCase();
                return href.includes('IAU090N0s') || label.includes('mybc home');
            }});

            if (!homeLink) {{
                return {{ ok: false, step: 'mybc-home-link-missing' }};
            }}

            homeLink.scrollIntoView({{ block: 'center' }});
            homeLink.click();
            return {{
                ok: true,
                href: (homeLink.getAttribute('href') || '').slice(0, 120),
                label: normalize(homeLink.textContent),
            }};
        }}
        """,
    )

    if not clicked.get("ok"):
        step: str = str(clicked.get("step") or "unknown")
        raise RuntimeError(f"Navigation menu myBC Home impossible ({step}).")

    log(f"  Lien myBC Home clique : {clicked.get('label') or 'myBC Home'}")
    await tab.sleep(2.5)


async def _navigate_to_prospect_my_details_via_menu(tab: Any, log: LogFn) -> None:
    """
    Ouvre My Details via le menu myBC (Information → My Details).
    La navigation directe vers prospectmenu.jsp ne charge pas les champs (AJAX).
    """
    log("  Menu Information → My Details (IAS065N0s)...")
    clicked: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        () => {{
            const detailsPath = {json.dumps(MYBC_MY_DETAILS_SERVLET_PATH)};
            const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();

            const informationLink = document.querySelector(
                '#student-menu a#information, a#information[href*="menuid=information"]',
            );
            if (!informationLink) {{
                return {{ ok: false, step: 'information-link-missing' }};
            }}

            informationLink.scrollIntoView({{ block: 'center' }});
            informationLink.dispatchEvent(new MouseEvent('mouseover', {{ bubbles: true }}));
            informationLink.dispatchEvent(new MouseEvent('mouseenter', {{ bubbles: true }}));
            informationLink.click();

            const informationItem = informationLink.closest('li');
            const submenu = informationItem?.querySelector(':scope > ul');
            if (submenu) {{
                submenu.style.display = 'block';
            }}

            const myDetailsLink = Array.from(
                document.querySelectorAll('#student-menu a, a[href*="prospects.IAS065N0s"]'),
            ).find((anchor) => {{
                const href = anchor.getAttribute('href') || '';
                return href.includes('prospects.IAS065N0s') || href.includes(detailsPath);
            }});

            if (!myDetailsLink) {{
                return {{ ok: false, step: 'my-details-link-missing' }};
            }}

            myDetailsLink.scrollIntoView({{ block: 'center' }});
            myDetailsLink.click();
            return {{
                ok: true,
                href: (myDetailsLink.getAttribute('href') || '').slice(0, 120),
                label: normalize(myDetailsLink.textContent),
            }};
        }}
        """,
    )

    if not clicked.get("ok"):
        step: str = str(clicked.get("step") or "unknown")
        raise RuntimeError(f"Navigation menu Information → My Details impossible ({step}).")

    log(f"  Lien My Details clique : {clicked.get('label') or 'My Details'}")
    await tab.sleep(2.0)


async def _wait_for_prospect_menu_loaded(tab: Any, log: LogFn) -> None:
    """Attend que My Details / Prospect menu affiche les informations etudiant."""
    attempts: int = max(1, int(MYBC_SCREENSHOT_LOAD_TIMEOUT_S / 1.0))
    for attempt in range(attempts):
        state: dict[str, Any] = await js_eval_json(
            tab,
            """
            () => {
                const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const url = (location.href || '').toLowerCase();
                const ready = document.readyState === 'complete';
                const bodyText = document.body?.innerText || '';
                const onProspectView = (
                    url.includes('prospectmenu.jsp')
                    || url.includes('ias065n0s')
                    || url.includes('prospects.ias065')
                );
                const hasWelcome = /Welcome/i.test(bodyText);

                if (!ready || !hasWelcome) {
                    return { loaded: false, url: url.slice(0, 120), onProspectView };
                }

                const values = {};
                for (const row of Array.from(document.querySelectorAll('tr'))) {
                    const cells = row.querySelectorAll('td');
                    if (cells.length < 2) continue;
                    const label = normalize(cells[0].textContent).toLowerCase();
                    const value = normalize(cells[1].textContent);
                    if (label.includes('name') && !label.includes('user')) values.name = value;
                    if (label.includes('birth date')) values.birthDate = value;
                    if (label.includes('street')) values.street = value;
                    if (label.includes('city')) values.city = value;
                }

                const loaded = (
                    (values.name || '').length >= 2
                    && (values.birthDate || '').length >= 4
                    && (values.street || '').length >= 3
                    && (values.city || '').length >= 2
                );
                return { loaded, onProspectView, url: url.slice(0, 120), ...values };
            }
            """,
        )
        if state.get("loaded"):
            if attempt > 0:
                log(f"  My Details charge apres {attempt + 1}s ({state.get('url', '')}).")
            else:
                log(f"  My Details charge ({state.get('url', '')}).")
            return
        await tab.sleep(1.0)

    raise RuntimeError("My Details (Information → IAS065N0s) non charge — champs vides.")


async def _navigate_to_registration_dates_via_menu(tab: Any, log: LogFn) -> None:
    """Ouvre Registration Dates via le menu myBC (Registration → Registration Dates)."""
    log("  Menu Registration → Registration Dates (IAS021N0s)...")
    clicked: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        () => {{
            const datesPath = {json.dumps(MYBC_REGISTRATION_DATES_PATH)};
            const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();

            const registrationLink = document.querySelector(
                '#student-menu a#registration, a#registration[href*="menuid=registration"]',
            );
            if (!registrationLink) {{
                return {{ ok: false, step: 'registration-link-missing' }};
            }}

            registrationLink.scrollIntoView({{ block: 'center' }});
            registrationLink.dispatchEvent(new MouseEvent('mouseover', {{ bubbles: true }}));
            registrationLink.dispatchEvent(new MouseEvent('mouseenter', {{ bubbles: true }}));
            registrationLink.click();

            const registrationItem = registrationLink.closest('li');
            const submenu = registrationItem?.querySelector(':scope > ul');
            if (submenu) {{
                submenu.style.display = 'block';
            }}

            const datesLink = Array.from(
                document.querySelectorAll('#student-menu a, a[href*="registration.IAS021N0s"]'),
            ).find((anchor) => {{
                const href = anchor.getAttribute('href') || '';
                return href.includes('registration.IAS021N0s') || href.includes(datesPath);
            }});

            if (!datesLink) {{
                return {{ ok: false, step: 'registration-dates-link-missing' }};
            }}

            datesLink.scrollIntoView({{ block: 'center' }});
            datesLink.click();
            return {{
                ok: true,
                href: (datesLink.getAttribute('href') || '').slice(0, 120),
                label: normalize(datesLink.textContent),
            }};
        }}
        """,
    )

    if not clicked.get("ok"):
        step: str = str(clicked.get("step") or "unknown")
        raise RuntimeError(f"Navigation menu Registration → Registration Dates impossible ({step}).")

    log(f"  Lien Registration Dates clique : {clicked.get('label') or 'Registration Dates'}")
    await tab.sleep(2.0)


async def _wait_for_registration_information_loaded(tab: Any, log: LogFn) -> None:
    """Attend la page Registration Information avec le bouton View Registration Details."""
    attempts: int = max(1, int(MYBC_SCREENSHOT_LOAD_TIMEOUT_S / 1.0))
    for attempt in range(attempts):
        state: dict[str, Any] = await js_eval_json(
            tab,
            """
            () => {
                const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const ready = document.readyState === 'complete';
                const bodyText = document.body?.innerText || '';
                const hasHeading = /Registration Information/i.test(bodyText);
                const hasWelcome = /Welcome/i.test(bodyText);
                const detailsForm = document.querySelector(
                    'form[action*="registration.IAS016N1s"]',
                );
                const submit = detailsForm?.querySelector(
                    'input[type="submit"].savebutton, input[type="submit"][value*="View Registration Details"]',
                ) || document.querySelector(
                    'input[type="submit"][value="View Registration Details"]',
                );
                const hasTermRow = Array.from(document.querySelectorAll('tr')).some((row) => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length < 4) return false;
                    const termText = normalize(cells[0].textContent);
                    return /summer|fall|spring|winter|\\d{4}/i.test(termText);
                });
                const loaded = ready && hasHeading && hasWelcome && !!submit && hasTermRow;
                return {
                    loaded,
                    hasHeading,
                    hasSubmit: !!submit,
                    hasTermRow,
                    hasForm: !!detailsForm,
                    url: (location.href || '').slice(0, 120),
                };
            }
            """,
        )
        if state.get("loaded"):
            if attempt > 0:
                log(f"  Registration Information charge apres {attempt + 1}s.")
            return
        if attempt > 0 and attempt % 10 == 0:
            log(
                "  Attente Registration Information..."
                f" heading={state.get('hasHeading')},"
                f" submit={state.get('hasSubmit')},"
                f" termRow={state.get('hasTermRow')}",
            )
        await tab.sleep(1.0)

    raise RuntimeError("Page Registration Information non chargee.")


async def _click_view_registration_details(tab: Any, log: LogFn) -> None:
    """Soumet le formulaire View Registration Details (POST IAS016N1s)."""
    result: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        () => {{
            const servletPath = {json.dumps(MYBC_REGISTRATION_STATUS_SERVLET_PATH)};
            const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();

            const form = document.querySelector(
                'form[action*="registration.IAS016N1s"], form[action*="IAS016N1s"]',
            );
            const submit = form?.querySelector(
                'input[type="submit"].savebutton, input[type="submit"][value*="View Registration Details"]',
            ) || Array.from(document.querySelectorAll('input[type="submit"]')).find((control) => {{
                const value = normalize(control.value || control.getAttribute('value') || '');
                return value.includes('View Registration Details');
            }});

            if (!form && !submit) {{
                return {{ ok: false, step: 'form-missing' }};
            }}

            const target = submit || form;
            target.scrollIntoView({{ block: 'center' }});

            if (submit) {{
                submit.dispatchEvent(new MouseEvent('mousedown', {{ bubbles: true }}));
                submit.dispatchEvent(new MouseEvent('mouseup', {{ bubbles: true }}));
                submit.click();
            }}

            if (form && typeof form.requestSubmit === 'function' && submit) {{
                form.requestSubmit(submit);
            }} else if (form) {{
                form.submit();
            }}

            return {{
                ok: true,
                method: submit ? 'click+submit' : 'form-submit',
                action: (form?.getAttribute('action') || '').slice(0, 120),
                term: form?.querySelector('input[name="term"]')?.value || '',
            }};
        }}
        """,
    )

    if not result.get("ok"):
        step: str = str(result.get("step") or "unknown")
        raise RuntimeError(f"Bouton « View Registration Details » introuvable ({step}).")

    log(
        "  Formulaire View Registration Details soumis"
        f" (term={result.get('term') or '?'}, {result.get('method')}).",
    )
    await tab.sleep(3.0)


async def _wait_for_registration_status_loaded(tab: Any, log: LogFn) -> None:
    """Attend la page Admission/Registration Status."""
    attempts: int = max(1, int(MYBC_SCREENSHOT_LOAD_TIMEOUT_S / 1.0))
    for attempt in range(attempts):
        state: dict[str, Any] = await js_eval_json(
            tab,
            """
            () => {
                const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const url = (location.href || '').toLowerCase();
                const ready = document.readyState === 'complete';
                const bodyText = document.body?.innerText || '';
                const onStatusPage = (
                    url.includes('ias016n1s')
                    || /Admission\\/Registration Status/i.test(bodyText)
                );
                const hasWelcome = /Welcome/i.test(bodyText);
                const messageRows = Array.from(document.querySelectorAll('tr')).filter((row) => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length < 2) return false;
                    const severity = normalize(cells[0].textContent);
                    return severity.length > 0 && normalize(cells[1].textContent).length > 3;
                });
                const loaded = ready && onStatusPage && hasWelcome && messageRows.length >= 3;
                return {
                    loaded,
                    messageRows: messageRows.length,
                    url: url.slice(0, 120),
                };
            }
            """,
        )
        if state.get("loaded"):
            if attempt > 0:
                log(f"  Admission/Registration Status charge apres {attempt + 1}s.")
            return
        await tab.sleep(1.0)

    raise RuntimeError("Page Admission/Registration Status non chargee.")


async def _prepare_registration_status_dom_for_screenshot(tab: Any, log: LogFn) -> None:
    """Prepare le DOM de la page Admission/Registration Status avant capture."""
    objective_json: str = json.dumps(MYBC_PRIMARY_OBJECTIVE_DISPLAY)
    state: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        () => {{
            const objectiveText = {objective_json};
            const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
            const rowsToRemove = [
                'Hold DU - Dual Enrollment',
                'Hold ZE - Email Not Active Yet',
                'No Test Scores For: ENGLISH, MATHEMATICS, READING',
                'Program Objective Not Approved For VA',
                'Program Objective Not Approved For Financial Aid',
            ];

            let removedOrientation = 0;
            let removedContact = 0;
            let removedRows = 0;
            let replacedSeverity = 0;
            let replacedBeginDate = 0;
            let replacedTranscript = 0;
            let replacedObjective = 0;

            document.querySelectorAll('table.fccsc-headerbar-bg-4').forEach((table) => {{
                table.remove();
                removedOrientation += 1;
            }});

            document.querySelectorAll('b').forEach((element) => {{
                const text = normalize(element.textContent);
                if (text.includes('If you have any questions regarding registration errors')) {{
                    element.remove();
                    removedContact += 1;
                }}
            }});

            Array.from(document.querySelectorAll('tr')).forEach((row) => {{
                const rowText = normalize(row.textContent);
                if (rowsToRemove.some((pattern) => rowText.includes(pattern))) {{
                    row.remove();
                    removedRows += 1;
                    return;
                }}

                const cells = row.querySelectorAll('td');
                if (cells.length < 2) return;

                const label = normalize(cells[0].textContent).toLowerCase();
                if (label.includes('primary program objective')) {{
                    cells[1].textContent = objectiveText;
                    replacedObjective += 1;
                    return;
                }}

                const severity = normalize(cells[0].textContent);
                if (severity === 'May Hinder Registration') {{
                    cells[0].textContent = 'Informative';
                    replacedSeverity += 1;
                }}

                const messageCell = cells[1];
                const messageText = normalize(messageCell.textContent);

                if (messageText.includes('Your Registration Begin date not found')) {{
                    const font = messageCell.querySelector('font');
                    if (font) {{
                        font.textContent = ' You are enrolled for Summer Term 2026 ';
                    }} else {{
                        messageCell.textContent = 'You are enrolled for Summer Term 2026';
                    }}
                    replacedBeginDate += 1;
                }}

                if (messageText.includes('Transcript Not Received')) {{
                    const updated = messageText.replace(
                        'Transcript Not Received',
                        'Transcript Received',
                    );
                    const font = messageCell.querySelector('font');
                    if (font) {{
                        font.textContent = ` ${{updated}} `;
                    }} else {{
                        messageCell.textContent = updated;
                    }}
                    replacedTranscript += 1;
                }}
            }});

            const headingIntact = /Admission\\/Registration Status/i.test(
                document.body?.innerText || '',
            );
            const welcomeIntact = /Welcome/i.test(document.body?.innerText || '');

            return {{
                removedOrientation,
                removedContact,
                removedRows,
                replacedSeverity,
                replacedBeginDate,
                replacedTranscript,
                replacedObjective,
                headingIntact,
                welcomeIntact,
            }};
        }}
        """,
    )
    log(
        "  DOM Registration Status prepare :"
        f" orientation={state.get('removedOrientation', 0)},"
        f" contact={state.get('removedContact', 0)},"
        f" rows={state.get('removedRows', 0)},"
        f" severity={state.get('replacedSeverity', 0)},"
        f" beginDate={state.get('replacedBeginDate', 0)},"
        f" transcript={state.get('replacedTranscript', 0)},"
        f" objective={state.get('replacedObjective', 0)}",
    )

    if not state.get("headingIntact"):
        raise RuntimeError("DOM Registration Status : titre Admission/Registration Status manquant.")
    if not state.get("welcomeIntact"):
        raise RuntimeError("DOM Registration Status : message Welcome manquant.")
    if int(state.get("removedOrientation") or 0) < 1:
        raise RuntimeError("DOM Registration Status : banniere orientation non supprimee.")
    if int(state.get("removedContact") or 0) < 1:
        raise RuntimeError("DOM Registration Status : texte contact registration non supprime.")
    if int(state.get("replacedObjective") or 0) < 1:
        raise RuntimeError("DOM Registration Status : Primary Program Objective non remplace.")


def _mybc_screenshots_dir(account_id: int) -> Path:
    """Repertoire temporaire pour les captures myBC d'un compte."""
    base: Path = Path(tempfile.gettempdir()) / "alyvo-mybc-screenshots" / str(account_id)
    base.mkdir(parents=True, exist_ok=True)
    return base


async def _read_chrome_window_bounds(tab: Any) -> dict[str, int]:
    """Lit la position et la taille de la fenetre Chrome (coordonnees ecran)."""
    bounds: dict[str, Any] = await js_eval_json(
        tab,
        """
        () => ({
            left: Math.max(0, Math.round(window.screenX || 0)),
            top: Math.max(0, Math.round(window.screenY || 0)),
            width: Math.max(320, Math.round(window.outerWidth || 0)),
            height: Math.max(240, Math.round(window.outerHeight || 0)),
        })
        """,
    )
    return {
        "left": int(bounds.get("left") or 0),
        "top": int(bounds.get("top") or 0),
        "width": int(bounds.get("width") or 0),
        "height": int(bounds.get("height") or 0),
    }


def _optimize_screenshot_png_sync(output_path: Path) -> int:
    """Reduit la taille PNG (resize + compression) pour l'upload API."""
    from PIL import Image

    with Image.open(output_path) as image:
        width, height = image.size
        if width > MYBC_SCREENSHOT_MAX_WIDTH:
            ratio: float = MYBC_SCREENSHOT_MAX_WIDTH / width
            new_height: int = max(1, int(height * ratio))
            image = image.resize((MYBC_SCREENSHOT_MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
        image.save(output_path, format="PNG", optimize=True, compress_level=9)

    return output_path.stat().st_size


def _capture_chrome_window_png_sync(left: int, top: int, width: int, height: int, output_path: Path) -> int:
    """Capture la fenetre Chrome via mss (barre d'adresse Chrome incluse)."""
    import mss
    import mss.tools

    try:
        import ctypes

        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:  # noqa: BLE001
        pass

    monitor: dict[str, int] = {
        "left": left,
        "top": top,
        "width": width,
        "height": height,
    }
    with mss.mss() as screenshotter:
        shot = screenshotter.grab(monitor)
        mss.tools.to_png(shot.rgb, shot.size, output=str(output_path))

    return _optimize_screenshot_png_sync(output_path)


async def _take_chrome_window_screenshot(
    tab: Any,
    output_path: Path,
    page_url: str,
    log: LogFn,
) -> str:
    """Capture PNG de la fenetre Chrome entiere (URL reelle visible)."""
    await tab.activate()
    await js_eval_bool(tab, "() => { window.scrollTo(0, 0); return true; }")
    await tab.sleep(MYBC_SCREENSHOT_POST_DOM_WAIT_S)

    bounds: dict[str, int] = await _read_chrome_window_bounds(tab)
    file_size_bytes: int = await asyncio.to_thread(
        _capture_chrome_window_png_sync,
        bounds["left"],
        bounds["top"],
        bounds["width"],
        bounds["height"],
        output_path,
    )
    file_size_kb: int = max(1, file_size_bytes // 1024)
    log(
        f"  Capture fenetre Chrome ({page_url}) : {output_path.name}"
        f" [{bounds['width']}x{bounds['height']}, {file_size_kb} Ko]",
    )
    return str(output_path)


async def capture_mybc_activation_screenshots(
    tab: Any,
    account_id: int,
    log: LogFn,
    *,
    after_policies: bool = False,
) -> MybcScreenshotPaths:
    """
    Captures myBC :
    1) Student Home (DOM nettoye)  2) My Details  3) Registration Status.
    """
    active_tab: Any = tab
    mybc_tab: Any | None = await _find_mybc_tab(active_tab)
    if mybc_tab is not None:
        await mybc_tab.activate()
        active_tab = mybc_tab

    if after_policies:
        log("  Student Home via menu myBC Home (apres politiques / question securite)...")
        await _navigate_to_mybc_home_via_menu(active_tab, log)
    else:
        log(f"  Navigation Student Home : {MYBC_STUDENT_HOME_URL}")
        await active_tab.get(MYBC_STUDENT_HOME_URL)

    if after_policies:
        log(f"Etape 24/{MYBC_TOTAL_STEPS} — Captures myBC Student Home (DOM prepare)...")
    else:
        log(f"Etape 13/{MYBC_TOTAL_STEPS} — Captures myBC (politiques deja acceptees)...")
    screenshots_dir: Path = _mybc_screenshots_dir(account_id)
    student_home_path: Path = screenshots_dir / "mybc-student-home.png"

    log("  Attente chargement complet Student Home...")
    await _wait_for_student_home_loaded(active_tab, log)

    if not after_policies:
        log("  Capture 1/3 — Student Home (DOM prepare)...")
    await _prepare_mybc_student_home_dom_for_screenshot(active_tab, log)
    await _take_chrome_window_screenshot(
        active_tab,
        student_home_path,
        MYBC_STUDENT_HOME_URL,
        log,
    )

    log("  Capture 2/3 — My Details via menu Information...")
    await _navigate_to_prospect_my_details_via_menu(active_tab, log)
    log("  Attente chargement complet My Details...")
    await _wait_for_prospect_menu_loaded(active_tab, log)

    prospect_path: Path = screenshots_dir / "mybc-prospect-menu.png"
    if after_policies:
        log(f"Etape 25/{MYBC_TOTAL_STEPS} — Capture My Details...")
    else:
        log("  Capture 2/3 — My Details...")
    await _take_chrome_window_screenshot(
        active_tab,
        prospect_path,
        MYBC_PROSPECT_MENU_URL,
        log,
    )

    log("  Capture 3/3 — Registration Status via menu Registration...")
    await _navigate_to_registration_dates_via_menu(active_tab, log)
    log("  Attente chargement Registration Information...")
    await _wait_for_registration_information_loaded(active_tab, log)
    await _click_view_registration_details(active_tab, log)
    log("  Attente chargement Admission/Registration Status...")
    await _wait_for_registration_status_loaded(active_tab, log)

    registration_path: Path = screenshots_dir / "mybc-registration-status.png"
    if after_policies:
        log(f"Etape 26/{MYBC_TOTAL_STEPS} — Capture Registration Status (DOM prepare)...")
    else:
        log("  Capture 3/3 — Registration Status (DOM prepare)...")
    await _prepare_registration_status_dom_for_screenshot(active_tab, log)
    await active_tab.sleep(MYBC_SCREENSHOT_POST_DOM_WAIT_S)
    registration_status_url: str = (
        f"{MYBC_BASE}{MYBC_REGISTRATION_STATUS_SERVLET_PATH}"
    )
    await _take_chrome_window_screenshot(
        active_tab,
        registration_path,
        registration_status_url,
        log,
    )

    return MybcScreenshotPaths(
        student_home=str(student_home_path),
        prospect_menu=str(prospect_path),
        registration_status=str(registration_path),
    )


async def _read_mybc_security_question_state(tab: Any) -> dict[str, Any]:
    """Detecte la page Security Verification Question and Answer (post-politiques)."""
    return await js_eval_json(
        tab,
        """
            const url = (location.href || '').toLowerCase();
            const body = (document.body?.innerText || '').toLowerCase();
            const form = document.querySelector(
                'form[name="secqst"], form[action*="security.IAS005N1s"]',
            );
            const select = document.querySelector('select[name="securityCode"]');
            const answer = document.querySelector('input[name="securityResponse"]');
            const isSecurityQuestion =
                body.includes('security verification question')
                || body.includes('set-up your security verification')
                || !!(form && select && answer);
            return {
                isSecurityQuestion,
                hasForm: !!form,
                url: (location.href || '').slice(0, 140),
            };
        """,
    )


async def _is_mybc_security_question_page(tab: Any) -> bool:
    """True si l'onglet affiche le formulaire question de securite myBC."""
    state: dict[str, Any] = await _read_mybc_security_question_state(tab)
    return bool(state.get("isSecurityQuestion"))


async def _complete_mybc_security_question(tab: Any, log: LogFn) -> None:
    """Remplit question/reponse de securite myBC et clique Update."""
    question_code_json: str = json.dumps(MYBC_SECURITY_QUESTION_CODE)
    answer_json: str = json.dumps(MYBC_SECURITY_QUESTION_ANSWER)
    filled: dict[str, Any] = await js_eval_json(
        tab,
        f"""
            const select = document.querySelector('select[name="securityCode"]');
            const answer = document.querySelector('input[name="securityResponse"]');
            if (!select || !answer) {{
                return {{ ok: false }};
            }}
            const code = {question_code_json};
            const hasOption = Array.from(select.options).some((opt) => opt.value === code);
            if (hasOption) {{
                select.value = code;
            }} else if (select.options.length > 0) {{
                select.selectedIndex = 0;
            }}
            select.dispatchEvent(new Event('change', {{ bubbles: true }}));
            answer.value = {answer_json};
            answer.dispatchEvent(new Event('input', {{ bubbles: true }}));
            const selected = select.options[select.selectedIndex];
            return {{
                ok: true,
                question: ((selected && selected.textContent) || '').trim(),
            }};
        """,
    )
    if not filled.get("ok"):
        raise RuntimeError("Formulaire Security Verification Question introuvable.")

    question_label: str = str(filled.get("question") or "").strip()
    log(f"  Question securite : {question_label or MYBC_SECURITY_QUESTION_CODE}")

    if not await _click_mybc_submit_by_value(tab, ["update", "mettre à jour", "mettre a jour"]):
        raise RuntimeError("Bouton Update (Security Verification Question) introuvable.")

    log("  Security Verification Question : Update.")
    await tab.sleep(2.5)


async def _complete_mybc_security_question_if_present(tab: Any, log: LogFn) -> Any:
    """Complete la question de securite si la page apparait apres les politiques."""
    active_tab: Any = tab
    mybc_tab: Any | None = await _find_mybc_tab(active_tab)
    if mybc_tab is not None:
        await mybc_tab.activate()
        active_tab = mybc_tab

    attempts: int = max(1, int(MYBC_POLICY_TIMEOUT_S / 1.0))
    for i in range(attempts):
        if await _is_mybc_security_question_page(active_tab):
            log(f"Etape 23/{MYBC_TOTAL_STEPS} — Security Verification Question...")
            await _complete_mybc_security_question(active_tab, log)
            return active_tab
        await active_tab.sleep(1.0)
        if i > 0 and i % 10 == 0:
            log(f"  Attente page Security Verification Question ({i}/{attempts})...")

    log("  Page Security Verification Question absente (deja configuree ?).")
    return active_tab


async def _find_mybc_tab(tab: Any) -> Any | None:
    """Retourne un onglet mybc.broward.edu si ouvert."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            url: str = await _read_tab_url(candidate)
        except Exception:  # noqa: BLE001
            continue
        if "mybc.broward.edu" in url.lower():
            return candidate
    return None


async def _dismiss_microsoft_stay_signed_in(tab: Any) -> None:
    """Clique « Oui » / « Yes » sur l'ecran Rester connecte si present."""
    await js_eval_bool(
        tab,
        """
        () => {
            const pageId = document.querySelector('meta[name="PageID"]');
            const pgid = ((pageId && pageId.getAttribute('content')) || '').trim();
            if (pgid !== 'ConvergedSignIn' && pgid !== 'Kmsi') return false;
            const body = (document.body?.innerText || '').toLowerCase();
            if (!body.includes('stay signed in') && !body.includes('rester connect')) return false;
            const btn = document.querySelector('#idSIButton9, input[type="submit"].win-button');
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        }
        """,
    )


async def _read_onelogin_username_screen(tab: Any) -> dict[str, Any]:
    """Detecte l'ecran username du portail OneLogin (MyBC SAML)."""
    return await js_eval_json(
        tab,
        """
            const username = document.querySelector('#username, input[data-testid="username"]');
            const visible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 4 && rect.height > 4;
            };
            const body = (document.body?.innerText || '').toLowerCase();
            return {
                hasUsername: !!(username && visible(username)),
                isMyBcSaml:
                    body.includes('mybc')
                    || body.includes('connecting to'),
                url: (location.href || '').slice(0, 120),
            };
        """,
    )


async def _find_onelogin_username_tab(tab: Any) -> Any | None:
    """Retourne un onglet BC One Access (login2) affichant le champ username — pas le portail /portal."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            url: str = (await _read_tab_url(candidate)).lower()
        except Exception:  # noqa: BLE001
            continue
        if "onelogin.com" not in url:
            continue
        if "/portal" in url:
            continue
        try:
            state: dict[str, Any] = await _read_onelogin_username_screen(candidate)
        except Exception:  # noqa: BLE001
            continue
        if state.get("hasUsername"):
            return candidate
    return None


_ONLOGIN_PORTAL_MYBC_MATCH_JS: str = """
function isMyBcPortalApp(label) {
    const text = (label || '').toLowerCase();
    if (!text) return false;
    if (text.includes('mybc') || text.includes('my bc')) return true;
    if (text.includes('broward') && text.includes('college') && text.includes('student')) return true;
    return false;
}
"""


async def _read_onelogin_portal_state(tab: Any) -> dict[str, Any]:
    """Detecte le portail utilisateur OneLogin (liste d'applications)."""
    return await js_eval_json(
        tab,
        _ONLOGIN_PORTAL_MYBC_MATCH_JS
        + """
            const url = (location.href || '').toLowerCase();
            const hasSearch = !!document.querySelector(
                '[data-testid="search-input"], #search-input',
            );
            const appLinks = document.querySelectorAll('a.app-cell, .app-cell-wrapper a');
            const hasApps = appLinks.length > 0 || !!document.querySelector(
                '#apps-view-container, .apps-list, .app-cell-wrapper',
            );
            const isPortal = url.includes('onelogin.com/portal') || (hasSearch && hasApps);
            let myBcHref = '';
            let myBcLabel = '';
            for (const app of appLinks) {
                const aria = (app.getAttribute('aria-label') || '').toLowerCase();
                const nameEl = app.querySelector('.app-cell-appname');
                const name = ((nameEl && nameEl.textContent) || app.textContent || '').toLowerCase();
                const label = aria || name;
                if (isMyBcPortalApp(label)) {
                    myBcHref = app.getAttribute('href') || '';
                    myBcLabel = (nameEl && nameEl.textContent) || aria || 'MyBC';
                    break;
                }
            }
            return {
                isPortal,
                hasMyBcApp: !!myBcHref,
                appsLoaded: appLinks.length > 0,
                appCount: appLinks.length,
                myBcHref: myBcHref.slice(0, 160),
                myBcLabel: (myBcLabel || '').slice(0, 80),
                url: (location.href || '').slice(0, 120),
            };
        """,
    )


async def _wait_for_onelogin_portal_ready(tab: Any, log: LogFn) -> dict[str, Any]:
    """
    Attend le chargement React du portail OneLogin et la tuile MyBC si presente.
    Ne conclut pas « MyBC absent » tant que les applications ne sont pas rendues.
    """
    attempts: int = max(1, int(ONELOGIN_TIMEOUT_S / 1.0))
    last_state: dict[str, Any] = {}

    for i in range(attempts):
        last_state = await _read_onelogin_portal_state(tab)
        if not last_state.get("isPortal"):
            await tab.sleep(1.0)
            continue

        if last_state.get("hasMyBcApp"):
            label: str = str(last_state.get("myBcLabel") or "MyBC").strip()
            log(f"  Portail OneLogin pret — tuile {label} detectee.")
            return last_state

        if last_state.get("appsLoaded"):
            log("  Portail OneLogin charge — tuile MyBC absente.")
            return last_state

        await tab.sleep(1.0)
        if i > 0 and i % 5 == 0:
            log(f"  Attente chargement tuiles portail OneLogin ({i}/{attempts})...")

    return last_state


async def _any_portal_has_mybc_tile(tab: Any) -> bool:
    """True si un onglet portail OneLogin affiche deja la tuile MyBC."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            url: str = (await _read_tab_url(candidate)).lower()
        except Exception:  # noqa: BLE001
            continue
        if "onelogin.com" not in url:
            continue
        try:
            state: dict[str, Any] = await _read_onelogin_portal_state(candidate)
        except Exception:  # noqa: BLE001
            continue
        if state.get("isPortal") and state.get("hasMyBcApp"):
            return True
    return False


async def _find_onelogin_portal_tab(tab: Any) -> Any | None:
    """Retourne un onglet sur le portail OneLogin (User Portal - Home)."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            url: str = await _read_tab_url(candidate)
        except Exception:  # noqa: BLE001
            continue
        if "onelogin.com" not in url.lower():
            continue
        if "/portal" in url.lower():
            return candidate
        try:
            state: dict[str, Any] = await _read_onelogin_portal_state(candidate)
        except Exception:  # noqa: BLE001
            continue
        if state.get("isPortal"):
            return candidate
    return None


async def _open_mybc_direct(tab: Any, log: LogFn, *, new_tab: bool = True) -> Any:
    """
    Ouvre myBC quand la tuile MyBC est absente du portail OneLogin.
    Prefere un nouvel onglet (comportement proche d'un clic target=_blank).
    """
    browser: Any | None = getattr(tab, "browser", None)
    if new_tab and browser is not None:
        try:
            mybc_tab: Any = await browser.get(MYBC_BASE, new_tab=True)
            log(f"  myBC ouvert (nouvel onglet) : {MYBC_BASE}")
            await mybc_tab.sleep(2.5)
            return mybc_tab
        except Exception:  # noqa: BLE001
            log("  Nouvel onglet myBC indisponible — navigation dans l'onglet courant...")

    log(f"  Navigation directe myBC : {MYBC_BASE}")
    await tab.get(MYBC_BASE)
    await tab.sleep(2.5)
    return tab


async def _activate_mybc_tab_if_open(tab: Any) -> Any | None:
    """Active un onglet mybc.broward.edu deja ouvert, le cas echeant."""
    mybc_tab: Any | None = await _find_mybc_tab(tab)
    if mybc_tab is None:
        return None
    await mybc_tab.activate()
    return mybc_tab


async def _navigate_mybc_saml_link(tab: Any, mybc_href: str, label: str, log: LogFn) -> Any:
    """Ouvre le lien SAML MyBC (target=_blank) dans un nouvel onglet."""
    log(f"  OneLogin Portal : lancement tuile {label}...")
    browser: Any | None = getattr(tab, "browser", None)
    if browser is not None:
        try:
            saml_tab: Any = await browser.get(mybc_href, new_tab=True)
            await saml_tab.sleep(2.5)
            return saml_tab
        except Exception:  # noqa: BLE001
            log("  Nouvel onglet SAML indisponible — navigation dans l'onglet courant...")
    await tab.get(mybc_href)
    await tab.sleep(2.5)
    return tab


async def _launch_mybc_from_onelogin_portal(tab: Any, log: LogFn) -> Any | None:
    """
    Lance myBC depuis le portail OneLogin :
    - tuile MyBC (ex. « MyBC - Spring/Summer ») si presente ;
    - sinon ouverture directe de https://mybc.broward.edu/ (nouvel onglet).
    @returns Onglet myBC/SAML actif, ou None si l'onglet courant n'est pas le portail.
    """
    state: dict[str, Any] = await _wait_for_onelogin_portal_ready(tab, log)
    if not state.get("isPortal"):
        return None

    mybc_href: str = str(state.get("myBcHref") or "").strip()
    if mybc_href:
        label: str = str(state.get("myBcLabel") or "MyBC").strip()
        return await _navigate_mybc_saml_link(tab, mybc_href, label, log)

    if state.get("appsLoaded"):
        log("  MyBC absent du portail OneLogin — ouverture directe mybc.broward.edu...")
        return await _open_mybc_direct(tab, log)

    log("  Portail OneLogin sans tuiles chargees — nouvel essai au prochain cycle.")
    return None


async def _ensure_mybc_post_logon_session(
    tab: Any,
    school_email: str,
    school_password: str,
    log: LogFn,
    *,
    temp_password: str = "",
) -> Any:
    """
    Apres changement de mot de passe : portail OneLogin, myBC (tuile ou URL directe), puis Student Post-Logon.
    BC One Access (login2) uniquement si la tuile MyBC est absente du portail.
    """
    active_tab: Any = tab
    try:
        active_url: str = (await _read_tab_url(active_tab)).lower()
    except Exception:  # noqa: BLE001
        active_url = ""

    existing_mybc: Any | None = await _find_mybc_tab(active_tab)
    existing_portal: Any | None = await _find_onelogin_portal_tab(active_tab)

    if existing_mybc is not None:
        log("  myBC deja ouvert dans le navigateur.")
        await existing_mybc.activate()
        active_tab = existing_mybc
    elif existing_portal is not None:
        log("  Portail OneLogin deja ouvert (User Portal).")
        await existing_portal.activate()
        active_tab = existing_portal
        await dismiss_onetrust_if_present(active_tab)
    elif "onelogin.com/portal" in active_url:
        log("  Portail OneLogin detecte (onglet actif).")
        await dismiss_onetrust_if_present(active_tab)
    else:
        log(f"  Navigation portail OneLogin : {ONELOGIN_USER_PORTAL_URL}")
        await active_tab.get(ONELOGIN_USER_PORTAL_URL)
        await active_tab.sleep(2.5)
        await dismiss_onetrust_if_present(active_tab)

    attempts: int = max(1, int(MYBC_SESSION_TIMEOUT_S / 1.0))
    username_submitted: bool = False
    mybc_launched: bool = False
    portal_direct_open_tried: bool = False

    for i in range(attempts):
        mybc_tab: Any | None = await _find_mybc_tab(active_tab)
        if mybc_tab is not None:
            await mybc_tab.activate()
            active_tab = mybc_tab
            if await _is_mybc_student_home_page(active_tab):
                log("  myBC Student Home detecte (politiques deja acceptees).")
                return active_tab
            if await _is_mybc_post_logon_page(active_tab):
                log("  myBC Student Post-Logon pret.")
                return active_tab

            current_url: str = (await _read_tab_url(active_tab)).lower()
            if "studentpostlogon" not in current_url and "ias900n1.jsp" not in current_url:
                log("  myBC ouvert — redirection Student Post-Logon...")
                await active_tab.get(MYBC_POST_LOGON_URL)
                await active_tab.sleep(2.0)
                if await _is_mybc_post_logon_page(active_tab):
                    log("  myBC Student Post-Logon pret.")
                    return active_tab

        portal_has_mybc: bool = await _any_portal_has_mybc_tile(active_tab)

        ms_tab, _ms_state = await _find_microsoft_login_tab(active_tab)
        if ms_tab is not None and not portal_has_mybc:
            await ms_tab.activate()
            active_tab, _used_bcproud = await submit_microsoft_school_login(
                ms_tab,
                school_email,
                temp_password,
                log,
                fallback_password=school_password,
            )
            await _dismiss_microsoft_stay_signed_in(active_tab)
            await active_tab.sleep(2.0)
            continue

        if not mybc_launched:
            portal_tab: Any | None = await _find_onelogin_portal_tab(active_tab)
            if portal_tab is None and "onelogin.com/portal" in (
                await _read_tab_url(active_tab)
            ).lower():
                portal_tab = active_tab
            if portal_tab is not None:
                await portal_tab.activate()
                active_tab = portal_tab
                await dismiss_onetrust_if_present(active_tab)
                launched_tab: Any | None = await _launch_mybc_from_onelogin_portal(
                    active_tab,
                    log,
                )
                if launched_tab is not None:
                    mybc_launched = True
                    active_tab = launched_tab
                    await active_tab.sleep(2.0)
                continue

        if not username_submitted and not portal_has_mybc:
            onelogin_tab: Any | None = await _find_onelogin_username_tab(active_tab)
            if onelogin_tab is not None:
                await onelogin_tab.activate()
                active_tab = onelogin_tab
                await dismiss_onetrust_if_present(active_tab)
                await submit_bc_one_access_username(active_tab, school_email, log)
                username_submitted = True
                log("  BC One Access : email ecole saisi, redirection myBC attendue...")
                await active_tab.sleep(3.0)
                continue

        if not mybc_launched and not portal_has_mybc and not portal_direct_open_tried:
            portal_tab = await _find_onelogin_portal_tab(active_tab)
            portal_state: dict[str, Any] = {}
            if portal_tab is not None:
                portal_state = await _wait_for_onelogin_portal_ready(portal_tab, log)
            if portal_state.get("isPortal") and portal_state.get("appsLoaded") and not portal_state.get(
                "hasMyBcApp",
            ):
                log(f"  Repli : ouverture directe {MYBC_BASE} (tuile MyBC absente)...")
                active_tab = await _open_mybc_direct(active_tab, log)
                mybc_launched = True
                portal_direct_open_tried = True
                continue

        await active_tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente OneLogin → myBC Student Post-Logon ({i}/{attempts})...")

    raise RuntimeError(
        f"Page Student Post-Logon myBC introuvable apres {int(MYBC_SESSION_TIMEOUT_S)}s "
        f"(portail OneLogin / {MYBC_BASE} + email {school_email}).",
    )


async def _return_to_mybc_post_logon(tab: Any, log: LogFn) -> Any:
    """Recharge la page post-logon et attend la liste des politiques."""
    await tab.get(MYBC_POST_LOGON_URL)
    await tab.sleep(2.0)
    attempts: int = max(1, int(MYBC_POLICY_TIMEOUT_S / 1.0))
    for i in range(attempts):
        if await _is_mybc_post_logon_page(tab):
            return tab
        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente retour Student Post-Logon ({i}/{attempts})...")
    raise RuntimeError("Retour Student Post-Logon myBC impossible.")


async def _open_mybc_post_logon_item(
    tab: Any,
    link_patterns: list[str],
    direct_url: str,
    log: LogFn,
) -> None:
    """Clique un item de la table post-logon ou navigue vers l'URL directe."""
    patterns_json: str = json.dumps(link_patterns)
    opened: dict[str, Any] = await js_eval_json(
        tab,
        f"""
            const patterns = {patterns_json};
            const norm = (value) => (value || '')
                .toLowerCase()
                .normalize('NFD')
                .replace(/\\p{{Diacritic}}/gu, '')
                .trim();
            const matches = (text) => patterns.some((pattern) => norm(text).includes(norm(pattern)));
            for (const link of document.querySelectorAll('a[href]')) {{
                if (matches(link.textContent || '')) {{
                    link.scrollIntoView({{ block: 'center' }});
                    link.click();
                    return {{ opened: true, method: 'link', href: link.href || '' }};
                }}
            }}
            for (const row of document.querySelectorAll('tr.fccsc-detail-1, tr.fccsc-detail-2')) {{
                const text = row.textContent || '';
                if (!matches(text)) continue;
                const link = row.querySelector('a[href]');
                if (link) {{
                    link.scrollIntoView({{ block: 'center' }});
                    link.click();
                    return {{ opened: true, method: 'row-link', href: link.href || '' }};
                }}
                const cell = row.querySelector('td');
                if (cell) {{
                    cell.click();
                    return {{ opened: true, method: 'row-click', href: '' }};
                }}
            }}
            return {{ opened: false, method: '', href: '' }};
        """,
    )

    if opened.get("opened"):
        method: str = str(opened.get("method") or "")
        log(f"  Ouverture post-logon ({method}).")
        await tab.sleep(2.5)
        return

    log(f"  Lien post-logon introuvable — navigation directe : {direct_url}")
    await tab.get(direct_url)
    await tab.sleep(2.5)


async def _complete_mybc_college_policy(tab: Any, log: LogFn) -> None:
    """Accepte les politiques du college (policy.jsp)."""
    clicked: bool = await _click_mybc_submit_by_value(tab, ["accept", "accepter"])
    if not clicked:
        clicked = await js_eval_bool(
            tab,
            """
            () => {
                const form = document.querySelector(
                    'form[action*="security.IAS008N1s"] input[name="flag"][value="policy"]',
                )?.form;
                const submit = form?.querySelector('input[type="submit"]');
                if (!submit) return false;
                submit.click();
                return true;
            }
            """,
        )
    if not clicked:
        raise RuntimeError("Bouton Accept/Accepter (College Policies) introuvable.")
    log("  Politiques du college acceptees.")
    await tab.sleep(2.5)


async def _complete_mybc_financial_authorization(tab: Any, log: LogFn) -> None:
    """Review Now puis Submit sur le formulaire d'autorisation financiere."""
    attempts: int = max(1, int(MYBC_POLICY_TIMEOUT_S / 1.0))
    for i in range(attempts):
        state: dict[str, Any] = await js_eval_json(
            tab,
            """
                const body = (document.body?.innerText || '').toLowerCase();
                const reviewNow = Array.from(document.querySelectorAll('input[type="submit"]'))
                    .find((el) => /review now/i.test(el.value || ''));
                const submitBtn = document.querySelector(
                    'input.savebutton[value="Submit"], input[type="submit"][value="Submit"]',
                );
                const authForm = document.querySelector('input[name="function"][value="U"]');
                return {
                    hasReviewNow: !!reviewNow,
                    hasAuthForm: !!(submitBtn && authForm),
                    isStatusPage: body.includes('financial authorization status'),
                    isFormPage: body.includes('broward authorization information form'),
                };
            """,
        )

        if state.get("hasReviewNow"):
            if not await _click_mybc_submit_by_value(tab, ["review now"]):
                raise RuntimeError("Bouton Review Now (Financial Authorization) introuvable.")
            log("  Financial Authorization : Review Now clique.")
            await tab.sleep(2.5)
            continue

        if state.get("hasAuthForm"):
            if not await _click_mybc_submit_by_value(tab, ["submit"]):
                raise RuntimeError("Bouton Submit (Financial Authorization) introuvable.")
            log("  Autorisation financiere soumise (options Yes par defaut).")
            await tab.sleep(2.5)
            return

        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente page Financial Authorization ({i}/{attempts})...")

    raise RuntimeError("Formulaire Financial Authorization introuvable ou non soumis.")


async def _complete_mybc_1098t_delivery(tab: Any, log: LogFn) -> None:
    """Accepte la livraison electronique du 1098-T."""
    clicked: bool = await js_eval_bool(
        tab,
        """
        () => {
            const buttons = Array.from(document.querySelectorAll('input[type="button"], input[type="submit"]'));
            const accept = buttons.find((el) => /accept.*electronic/i.test(el.value || ''));
            if (accept) {
                accept.scrollIntoView({ block: 'center' });
                accept.click();
                return true;
            }
            const form = document.querySelector('form[action*="security.IAS008N1s"]');
            if (!form) return false;
            const flagValue = form.querySelector('input[name="flagValue"]') || form.flagValue;
            if (flagValue) flagValue.value = 'E';
            if (typeof form.submit === 'function') {
                form.submit();
                return true;
            }
            return false;
        }
        """,
    )
    if not clicked:
        raise RuntimeError("Bouton ACCEPT Electronic Delivery (1098T) introuvable.")
    log("  Livraison electronique 1098-T acceptee.")
    await tab.sleep(2.5)


async def _complete_mybc_state_required_info(tab: Any, log: LogFn) -> None:
    """Selectionne Not Applicable sur les deux listes puis Continue."""
    filled: bool = await js_eval_bool(
        tab,
        """
        () => {
            const single = document.querySelector('#SingleParent, select[name="SingleParent"]');
            const displaced = document.querySelector('#DisplacedHomemaker, select[name="DisplacedHomemaker"]');
            if (!single || !displaced) return false;
            single.value = 'Z';
            single.dispatchEvent(new Event('change', { bubbles: true }));
            displaced.value = 'Z';
            displaced.dispatchEvent(new Event('change', { bubbles: true }));
            return single.value === 'Z' && displaced.value === 'Z';
        }
        """,
    )
    if not filled:
        raise RuntimeError("Selects State Required Information introuvables.")

    if not await _click_mybc_submit_by_value(tab, ["continue", "continuer"]):
        raise RuntimeError("Bouton Continue (State Required Information) introuvable.")
    log("  State Required Information : Not Applicable x2, Continue.")
    await tab.sleep(2.5)


async def _complete_mybc_personal_information(tab: Any, log: LogFn) -> None:
    """Confirme les informations personnelles (Yes)."""
    clicked: bool = await js_eval_bool(
        tab,
        """
        () => {
            const flag = document.querySelector('input[name="flag"][value="personalinfo"]');
            const form = flag?.form;
            const yes = form?.querySelector('input[type="submit"][value="Yes"]')
                || document.querySelector('input[type="submit"][value="Yes"]');
            if (!yes) return false;
            yes.scrollIntoView({ block: 'center' });
            yes.click();
            return true;
        }
        """,
    )
    if not clicked:
        raise RuntimeError("Bouton Yes (Personal Information) introuvable.")
    log("  Informations personnelles confirmees (Yes).")
    await tab.sleep(2.5)


async def _complete_mybc_security_flag_submit(
    tab: Any,
    flag: str,
    button_patterns: list[str],
    log_message: str,
    log: LogFn,
) -> None:
    """Soumet un formulaire security.IAS008N1s avec flag fixe (Ok, Confirm, etc.)."""
    flag_json: str = json.dumps(flag)
    patterns_json: str = json.dumps([p.lower() for p in button_patterns])
    clicked: bool = await js_eval_bool(
        tab,
        f"""
        () => {{
            const patterns = {patterns_json};
            const flagValue = {flag_json};
            const norm = (value) => (value || '').trim().toLowerCase();
            const matches = (value) => patterns.some((pattern) => norm(value).includes(pattern));
            const flagInput = document.querySelector(
                'form[action*="security.IAS008N1s"] input[name="flag"][value="' + flagValue + '"]',
            );
            const form = flagInput?.form;
            if (form) {{
                const submit = Array.from(form.querySelectorAll('input[type="submit"], button'))
                    .find((el) => matches(el.value || el.textContent || ''));
                if (submit) {{
                    submit.scrollIntoView({{ block: 'center' }});
                    submit.click();
                    return true;
                }}
            }}
            const controls = Array.from(
                document.querySelectorAll('input[type="submit"], input[type="button"], button'),
            );
            for (const el of controls) {{
                if (!matches(el.value || el.textContent || '')) continue;
                el.scrollIntoView({{ block: 'center' }});
                el.click();
                return true;
            }}
            return false;
        }}
        """,
    )
    if not clicked:
        raise RuntimeError(f"Bouton {button_patterns!r} introuvable (flag={flag}).")
    log(log_message)
    await tab.sleep(2.5)


async def complete_mybc_post_logon_policies(
    tab: Any,
    school_email: str,
    school_password: str,
    log: LogFn,
    *,
    account_id: int,
    temp_password: str = "",
) -> tuple[Any, MybcScreenshotPaths | None]:
    """
    Apres changement de mot de passe : complete les 9 politiques Student Post-Logon myBC,
    ou captures d'ecran si Student Home (politiques deja acceptees).
    """
    log(f"Etape 13/{MYBC_TOTAL_STEPS} — Portail OneLogin → myBC Student Post-Logon...")
    active_tab: Any = await _ensure_mybc_post_logon_session(
        tab,
        school_email,
        school_password,
        log,
        temp_password=temp_password,
    )

    if await _is_mybc_student_home_page(active_tab):
        log("  Student Home detecte — politiques et question de securite deja validees, captures directes.")
        screenshots: MybcScreenshotPaths = await capture_mybc_activation_screenshots(
            active_tab,
            account_id,
            log,
        )
        return active_tab, screenshots

    policy_steps: list[tuple[int, str, list[str], str, Callable[..., Any]]] = [
        (
            14,
            "College Policies",
            ["college policies", "politiques et directives", "policy.jsp"],
            f"{MYBC_BASE}/FCCSC/student/policy.jsp",
            _complete_mybc_college_policy,
        ),
        (
            15,
            "Financial Authorization",
            ["financial authorization", "autorisation financière", "autorisation financiere"],
            f"{MYBC_BASE}/FCCSC/servlet/student.IAC050N1s",
            _complete_mybc_financial_authorization,
        ),
        (
            16,
            "1098T Delivery Preference",
            ["1098t delivery", "préférence de livraison 1098", "preference de livraison 1098"],
            f"{MYBC_BASE}/FCCSC/servlet/student.IAC095N1s",
            _complete_mybc_1098t_delivery,
        ),
        (
            17,
            "Review State Required Information",
            [
                "review state required",
                "state required information",
                "informations requises par l",
            ],
            f"{MYBC_BASE}/FCCSC/security/reviewmilitarystatus.jsp",
            _complete_mybc_state_required_info,
        ),
        (
            18,
            "Personal Information",
            ["personal information", "informations personnelles", "verify information"],
            f"{MYBC_BASE}/FCCSC/security/verifyinfo.jsp",
            _complete_mybc_personal_information,
        ),
        (
            19,
            "Drug and Alcohol Disclosure",
            ["drug and alcohol", "drogues et à l'alcool", "drogues et a l'alcool", "alcohol disclosure"],
            f"{MYBC_BASE}/FCCSC/student/verifyalcoholpolicy.jsp",
            lambda policy_tab, policy_log: _complete_mybc_security_flag_submit(
                policy_tab,
                "alcoholpolicy",
                ["ok"],
                "  Drug and Alcohol Disclosure : Ok.",
                policy_log,
            ),
        ),
        (
            20,
            "Active Shooter Preparedness",
            ["active shooter", "tireur actif", "shots fired"],
            f"{MYBC_BASE}/FCCSC/student/activeshooterpolicy.jsp",
            lambda policy_tab, policy_log: _complete_mybc_security_flag_submit(
                policy_tab,
                "activeshooterpolicy",
                ["ok"],
                "  Active Shooter Preparedness : OK.",
                policy_log,
            ),
        ),
        (
            21,
            "ID Card Terms and Conditions",
            ["id card terms", "conditions générales", "conditions generales", "carte d'identité"],
            f"{MYBC_BASE}/FCCSC/student/idcardtermsandconditions.jsp",
            lambda policy_tab, policy_log: _complete_mybc_security_flag_submit(
                policy_tab,
                "idcardtermsandconditions",
                ["ok"],
                "  ID Card Terms and Conditions : OK.",
                policy_log,
            ),
        ),
        (
            22,
            "Economic Security Report",
            ["economic security", "rapport sur la sécurité", "rapport sur la securite"],
            f"{MYBC_BASE}/FCCSC/student/economicsecurityreport.jsp",
            lambda policy_tab, policy_log: _complete_mybc_security_flag_submit(
                policy_tab,
                "economicsecurityreport",
                ["confirm", "confirmer"],
                "  Economic Security Report : Confirm.",
                policy_log,
            ),
        ),
    ]

    for step_num, name, link_patterns, direct_url, action in policy_steps:
        log(f"Etape {step_num}/{MYBC_TOTAL_STEPS} — myBC : {name}...")
        active_tab = await _return_to_mybc_post_logon(active_tab, log)
        await _open_mybc_post_logon_item(active_tab, link_patterns, direct_url, log)
        await action(active_tab, log)

    log("  Politiques myBC Student Post-Logon terminees.")
    active_tab = await _complete_mybc_security_question_if_present(active_tab, log)
    screenshots = await capture_mybc_activation_screenshots(
        active_tab,
        account_id,
        log,
        after_policies=True,
    )
    return active_tab, screenshots


async def _complete_fresh_bcproud_post_login_steps(
    tab: Any,
    school_email: str,
    temp_password: str,
    final_password: str,
    log: LogFn,
) -> Any:
    """
    Compte neuf (mot de passe BCProud accepte) :
    ProofUp Suivant -> My Sign-Ins Suivant x2 -> QR manuel -> changement MDP.
    Reprise automatique via retour BC One Access si ConvergedError (AADSTS90100).
    """
    log("  Compte neuf (BCProud) — enchainement MFA automatique (ProofUp + My Sign-Ins).")
    active_tab: Any = tab
    max_attempts: int = 2

    for attempt in range(max_attempts):
        try:
            mfa_tab: Any = await submit_proof_up_redirect(active_tab, log)
        except RuntimeError as exc:
            if attempt + 1 >= max_attempts or "reprise BC One Access" not in str(exc).lower():
                raise
            active_tab = await _recover_fresh_bcproud_via_onelogin_back(
                active_tab,
                school_email,
                temp_password,
                final_password,
                log,
            )
            continue

        error_tab, _error_state = await _find_tab_with_converged_error(mfa_tab)
        if error_tab is not None:
            if attempt + 1 >= max_attempts:
                raise RuntimeError(
                    "Erreur Microsoft persistante apres reprise BC One Access (AADSTS90100).",
                )
            active_tab = await _recover_fresh_bcproud_via_onelogin_back(
                mfa_tab,
                school_email,
                temp_password,
                final_password,
                log,
            )
            continue

        mfa_tab = await advance_mysignins_register_steps(mfa_tab, log)

        change_password_tab: Any = await complete_post_qr_mfa_flow(mfa_tab, log)

        _route_tab, phase, _state = await _detect_flow_resume_phase(change_password_tab)
        if phase == PHASE_CHANGE_PASSWORD:
            return await submit_microsoft_change_password(
                change_password_tab,
                temp_password,
                final_password,
                log,
            )

        return change_password_tab

    raise RuntimeError("Flux MFA compte neuf (BCProud) echoue apres reprises BC One Access.")


async def complete_post_school_login_steps(
    tab: Any,
    school_email: str,
    temp_password: str,
    final_password: str,
    log: LogFn,
    *,
    fresh_bcproud_login: bool = False,
) -> Any:
    """
    Apres connexion Microsoft ecole : detecte l'etape courante et enchaine
    (MFA, changement MDP) ou saute vers myBC si le compte est deja partiellement active.
    Compte neuf (BCProud) : enchainement MFA automatique force.
    """
    if fresh_bcproud_login:
        return await _complete_fresh_bcproud_post_login_steps(
            tab,
            school_email,
            temp_password,
            final_password,
            log,
        )

    active_tab: Any = tab

    resume_tab: Any | None = await _try_resume_mybc_entry(active_tab, log)
    if resume_tab is not None:
        return resume_tab

    route_attempts: int = max(1, int(POST_LOGIN_ROUTE_TIMEOUT_S / 1.0))
    for i in range(route_attempts):
        resume_tab = await _try_resume_mybc_entry(active_tab, log)
        if resume_tab is not None:
            return resume_tab

        _route_tab, phase, _state = await _detect_flow_resume_phase(active_tab)
        if phase == PHASE_CHANGE_PASSWORD:
            log("  Reprise : changement de mot de passe Microsoft detecte.")
            return await submit_microsoft_change_password(
                active_tab,
                temp_password,
                final_password,
                log,
            )
        if phase in (PHASE_PROOF_UP, PHASE_CONVERGED_TFA, PHASE_MYSIGNINS):
            if phase == PHASE_MYSIGNINS:
                log("  Reprise : compte deja partiellement active (My Sign-Ins) — suite MFA.")
            elif phase == PHASE_PROOF_UP:
                log("  Reprise : enregistrement MFA Microsoft (ProofUp) — suite du flux.")
            else:
                log("  Reprise : MFA Microsoft deja en cours — suite du flux.")
            break

        await active_tab.sleep(1.0)
        if i > 0 and i % 10 == 0:
            log(f"  Attente redirection post-connexion ({i}/{route_attempts})...")

    resume_tab = await _try_resume_mybc_entry(active_tab, log)
    if resume_tab is not None:
        return resume_tab

    _route_tab, phase, _state = await _detect_flow_resume_phase(active_tab)
    working_tab: Any = _route_tab if _route_tab is not None else active_tab

    if phase == PHASE_PROOF_UP:
        working_tab = await submit_proof_up_redirect(working_tab, log)
    elif phase not in (PHASE_MYSIGNINS, PHASE_CONVERGED_TFA, PHASE_CHANGE_PASSWORD):
        working_tab = await submit_proof_up_redirect(active_tab, log)

    resume_tab = await _try_resume_mybc_entry(working_tab, log)
    if resume_tab is not None:
        return resume_tab

    _route_tab, phase, mysignins_state = await _detect_flow_resume_phase(working_tab)
    if phase == PHASE_MYSIGNINS:
        mysignins_step: str = str(mysignins_state.get("step") or "")
        if mysignins_state.get("isAutomatedStep") or mysignins_step in ("install_app", "setup_account"):
            mfa_tab: Any = await advance_mysignins_register_steps(working_tab, log)
        else:
            log(
                "  My Sign-Ins : etapes auto deja passees "
                f"(etape courante : {mysignins_step or 'inconnue'}) — suite MFA.",
            )
            mfa_tab = _route_tab if _route_tab is not None else working_tab
    else:
        mfa_tab = working_tab

    resume_tab = await _try_resume_mybc_entry(mfa_tab, log)
    if resume_tab is not None:
        return resume_tab

    change_password_tab: Any = await complete_post_qr_mfa_flow(mfa_tab, log)

    resume_tab = await _try_resume_mybc_entry(change_password_tab, log)
    if resume_tab is not None:
        return resume_tab

    _route_tab, phase, _state = await _detect_flow_resume_phase(change_password_tab)
    if phase == PHASE_CHANGE_PASSWORD:
        return await submit_microsoft_change_password(
            change_password_tab,
            temp_password,
            final_password,
            log,
        )

    resume_tab = await _try_resume_mybc_entry(change_password_tab, log)
    if resume_tab is not None:
        return resume_tab

    return change_password_tab


async def find_student_id_email(tab: Any, log: LogFn) -> None:
    """Attend et ouvre le mail Student ID dans Outlook."""
    await wait_for_outlook_inbox(tab, log, timeout_s=90.0)

    attempts: int = max(1, int(OUTLOOK_MAIL_TIMEOUT_S / 2.0))
    mail_clicked: bool = False

    for i in range(attempts):
        if not mail_clicked:
            mail_clicked = await click_student_id_email(tab, log)
            if mail_clicked:
                await tab.sleep(2.5)

        if mail_clicked:
            body: str = await read_student_id_mail_body(tab)
            if STUDENT_ID_SUBJECT.lower() in body.lower() or SCHOOL_EMAIL_RE.search(body):
                return

        await tab.sleep(2.0)
        if i > 0 and i % 10 == 0:
            log(f"  Attente email « {STUDENT_ID_SUBJECT} » ({i}/{attempts})...")

    raise StudentIdMailNotFoundError(
        f"Email « {STUDENT_ID_SUBJECT} » introuvable dans Outlook apres {int(OUTLOOK_MAIL_TIMEOUT_S)}s.",
    )


async def run_student_id_flow(tab: Any, account: StudentIdAccountInput, log: LogFn) -> StudentIdFlowResult:
    """
    Flow complet : Outlook -> mail Student ID -> BC One Access -> MFA manuel -> changement MDP.
    @param tab - Onglet nodriver.
    @param account - Compte a traiter.
    @param log - Journal stderr.
    @returns Donnees extraites.
    """
    broward_account: BrowardAccountInput = to_broward_account(account)

    log("Etape 1/12 — Connexion Outlook...")
    await open_outlook_sign_in_from_microsoft_page(tab, log)
    await fill_microsoft_login_if_needed(tab, broward_account, log)

    log("Etape 2/12 — Recherche du mail Student ID...")
    await find_student_id_email(tab, log)

    body: str = await read_student_id_mail_body(tab)
    school_email, student_id = parse_student_id_mail(body)
    log(f"  Email ecole : {school_email}")
    log(f"  Student ID : {student_id}")

    log("Etape 3/12 — Ouverture BC One Access...")
    onelogin_tab: Any = await open_bc_one_access_from_mail(tab, log)

    log("Etape 4/12 — Saisie email sur OneLogin...")
    await submit_bc_one_access_username(onelogin_tab, school_email, log)

    temp_password: str = bc_proud_temp_password(account.birthday)
    if temp_password:
        log(f"  Mot de passe temporaire : {temp_password[:2]}**** (MMYYYY@BCProud!)")

    log("Etape 5/12 — Connexion Microsoft (email ecole + mot de passe)...")
    ms_tab: Any
    used_bcproud_password: bool
    ms_tab, used_bcproud_password = await submit_microsoft_school_login(
        onelogin_tab,
        school_email,
        temp_password,
        log,
        fallback_password=account.password,
    )

    post_login_tab: Any = await complete_post_school_login_steps(
        ms_tab,
        school_email,
        temp_password,
        account.password,
        log,
        fresh_bcproud_login=used_bcproud_password,
    )

    _final_tab, mybc_screenshots = await complete_mybc_post_logon_policies(
        post_login_tab,
        school_email,
        account.password,
        log,
        account_id=account.account_id,
        temp_password=temp_password,
    )

    return StudentIdFlowResult(
        account_id=account.account_id,
        school_email=school_email,
        student_id=student_id,
        school_email_password=account.password,
        mybc_screenshots=mybc_screenshots,
    )
