"""
Recuperation Student ID / email ecole Broward depuis Outlook + BC One Access.
"""
from __future__ import annotations

import json
import re
import sys
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
MYBC_TOTAL_STEPS: int = 22

MYBC_BASE: str = "https://mybc.broward.edu"
MYBC_POST_LOGON_URL: str = f"{MYBC_BASE}/FCCSC/security/studentpostlogon.jsp"
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
class StudentIdFlowResult:
    account_id: int
    school_email: str
    student_id: str
    school_email_password: str


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


async def _find_onelogin_tab(tab: Any, log: LogFn) -> Any | None:
    """Retourne l'onglet BC One Access (meme onglet ou nouvel onglet target=_blank)."""
    current_url: str = await _read_tab_url(tab)
    if "onelogin.com" in current_url.lower():
        log(f"  BC One Access ouvert : {current_url[:100]}...")
        return tab

    browser: Any | None = getattr(tab, "browser", None)
    if browser is None:
        return None

    await browser.update_targets()
    for candidate in browser.tabs:
        if candidate is tab:
            continue
        try:
            candidate_url: str = await _read_tab_url(candidate)
        except Exception:  # noqa: BLE001
            continue
        if "onelogin.com" in candidate_url.lower():
            log(f"  BC One Access (nouvel onglet) : {candidate_url[:100]}...")
            await candidate.activate()
            return candidate

    return None


async def open_bc_one_access_from_mail(tab: Any, log: LogFn) -> Any:
    """
    Clique le lien « BC One Access » dans le mail Student ID, puis retourne l'onglet OneLogin.
    Repli : navigation directe vers l'URL extraite du corps du message.
    """
    click_data: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        {_outlook_mail_body_roots_js()}
            const links = findBcOneAccessLinks();
            if (!links.length) {{
                return {{ clicked: false, href: '', count: 0 }};
            }}
            const link = links[0];
            const href = normalizeMailLinkHref(link);
            link.scrollIntoView({{ block: 'center' }});
            link.click();
            return {{ clicked: true, href, count: links.length }};
        """,
    )

    href: str = str(click_data.get("href") or "").strip()
    link_count: int = int(click_data.get("count") or 0)

    if click_data.get("clicked"):
        if link_count > 1:
            log(f"  {link_count} lien(s) « BC One Access » trouve(s) — clic sur le premier.")
        else:
            log("  Clic sur le lien « BC One Access » dans le mail.")
        await tab.sleep(3.0)

        onelogin_tab: Any | None = await _find_onelogin_tab(tab, log)
        if onelogin_tab is not None:
            return onelogin_tab

        log("  Clic effectue mais OneLogin non detecte — navigation directe vers l'URL du mail...")
    else:
        log("  Lien « BC One Access » non cliquable — extraction de l'URL dans le corps du mail...")

    if not href:
        href = await extract_bc_one_access_href(tab)

    if not href or "onelogin.com/login2" not in href.lower():
        raise RuntimeError("Lien « BC One Access » (broward.onelogin.com/login2) introuvable dans le mail Student ID.")

    log(f"  Navigation BC One Access : {href[:100]}...")
    await tab.get(href)
    await tab.sleep(2.5)
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


async def submit_microsoft_school_login(
    tab: Any,
    school_email: str,
    temp_password: str,
    log: LogFn,
) -> Any:
    """
    Apres OneLogin username : redirection Microsoft ConvergedSignIn.
    Saisit l'email @mail.broward.edu puis le mot de passe temporaire MMYYYY@BCProud!.
    """
    if not temp_password:
        raise RuntimeError("Mot de passe temporaire MMYYYY@BCProud! introuvable (date de naissance invalide).")

    attempts: int = max(1, int(ONELOGIN_TIMEOUT_S / 1.0))
    active_tab: Any = tab

    for i in range(attempts):
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
            log("  Microsoft : saisie mot de passe...")
            if not await fill_microsoft_login_field(ms_tab, "password", temp_password):
                raise RuntimeError("Impossible de remplir le mot de passe Microsoft (#i0118).")
            if not await click_microsoft_primary(ms_tab):
                raise RuntimeError("Bouton Se connecter Microsoft introuvable (#idSIButton9).")
            log("  Microsoft : mot de passe soumis.")
            await ms_tab.sleep(3.0)
            return ms_tab

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
            const btn = document.querySelector('#idSubmit_ProofUp_Redirect');
            const visible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 4 && rect.height > 4;
            };
            return {
                isProofUpRedirect: pgid === 'ConvergedProofUpRedirect',
                hasNext: !!(btn && visible(btn)),
                pgid,
                url: (location.href || '').slice(0, 120),
                host: location.hostname || '',
            };
        """,
    )


async def _find_tab_with_proof_up_redirect(tab: Any) -> tuple[Any | None, dict[str, Any]]:
    """Retourne l'onglet ConvergedProofUpRedirect avec bouton Suivant."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            state: dict[str, Any] = await _read_proof_up_redirect_state(candidate)
        except Exception:  # noqa: BLE001
            continue
        if state.get("isProofUpRedirect") and state.get("hasNext"):
            return candidate, state
    return None, {}


async def submit_proof_up_redirect(tab: Any, log: LogFn) -> Any:
    """
    Apres le mot de passe temporaire : page ConvergedProofUpRedirect.
    Clique Suivant (#idSubmit_ProofUp_Redirect) pour lancer l'enregistrement MFA.
    """
    log("Etape 6/12 — Securisons votre compte (ConvergedProofUpRedirect)...")
    attempts: int = max(1, int(MFA_SETUP_TIMEOUT_S / 1.0))
    active_tab: Any = tab

    for i in range(attempts):
        proof_tab, state = await _find_tab_with_proof_up_redirect(active_tab)
        if proof_tab is None:
            await active_tab.sleep(1.0)
            if i > 0 and i % 15 == 0:
                log(f"  Attente page ConvergedProofUpRedirect ({i}/{attempts})...")
            continue

        await proof_tab.activate()
        clicked: bool = await js_eval_bool(
            proof_tab,
            """
            () => {
                const btn = document.querySelector('#idSubmit_ProofUp_Redirect');
                if (!btn) return false;
                btn.scrollIntoView({ block: 'center' });
                btn.click();
                return true;
            }
            """,
        )
        if not clicked:
            raise RuntimeError("Bouton Suivant ConvergedProofUpRedirect introuvable (#idSubmit_ProofUp_Redirect).")

        log("  ConvergedProofUpRedirect : Suivant clique.")
        await proof_tab.sleep(3.0)
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
            let step = 'other';
            if (
                titleText.includes('installer microsoft authenticator')
                || titleText.includes('install microsoft authenticator')
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
            if (!btn) return false;
            btn.scrollIntoView({ block: 'center' });
            btn.click();
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
    automated_plan: list[tuple[int, str, str]] = [
        (7, "install_app", "Installer Microsoft Authenticator"),
        (8, "setup_account", "Configurer votre compte dans l'application"),
    ]
    active_tab: Any = tab
    attempts_per_step: int = max(1, int(MFA_SETUP_TIMEOUT_S / 1.0))

    for step_num, step_id, step_label in automated_plan:
        log(f"Etape {step_num}/12 — {step_label} (My Sign-Ins)...")
        found: bool = False

        for i in range(attempts_per_step):
            ms_tab, state = await _find_tab_with_mysignins_automated_step(active_tab)
            if ms_tab is None or str(state.get("step") or "") != step_id:
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
            found = True
            break

        if not found:
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
    """Retourne un onglet OneLogin affichant le champ username."""
    for candidate in await _iter_browser_tabs(tab):
        try:
            url: str = await _read_tab_url(candidate)
        except Exception:  # noqa: BLE001
            continue
        if "onelogin.com" not in url.lower():
            continue
        try:
            state: dict[str, Any] = await _read_onelogin_username_screen(candidate)
        except Exception:  # noqa: BLE001
            continue
        if state.get("hasUsername"):
            return candidate
    return None


async def _read_onelogin_portal_state(tab: Any) -> dict[str, Any]:
    """Detecte le portail utilisateur OneLogin (liste d'applications)."""
    return await js_eval_json(
        tab,
        """
            const url = (location.href || '').toLowerCase();
            const hasSearch = !!document.querySelector(
                '[data-testid="search-input"], #search-input',
            );
            const hasApps = !!document.querySelector(
                '#apps-view-container, .apps-list, .app-cell-wrapper',
            );
            const isPortal = url.includes('onelogin.com/portal') || (hasSearch && hasApps);
            let myBcHref = '';
            let myBcLabel = '';
            for (const app of document.querySelectorAll('a.app-cell, .app-cell-wrapper a')) {
                const aria = (app.getAttribute('aria-label') || '').toLowerCase();
                const nameEl = app.querySelector('.app-cell-appname');
                const name = ((nameEl && nameEl.textContent) || app.textContent || '').toLowerCase();
                const label = aria || name;
                if (label.includes('mybc')) {
                    myBcHref = app.getAttribute('href') || '';
                    myBcLabel = (nameEl && nameEl.textContent) || aria || 'MyBC';
                    break;
                }
            }
            return {
                isPortal,
                hasMyBcApp: !!myBcHref,
                myBcHref: myBcHref.slice(0, 160),
                myBcLabel: (myBcLabel || '').slice(0, 80),
                url: (location.href || '').slice(0, 120),
            };
        """,
    )


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


async def _launch_mybc_from_onelogin_portal(tab: Any, log: LogFn) -> bool:
    """Clique sur la tuile MyBC dans le portail OneLogin (ex. MyBC - Spring/Summer)."""
    state: dict[str, Any] = await _read_onelogin_portal_state(tab)
    if not state.get("isPortal"):
        return False

    clicked: dict[str, Any] = await js_eval_json(
        tab,
        """
            for (const app of document.querySelectorAll('a.app-cell, .app-cell-wrapper a')) {
                const aria = (app.getAttribute('aria-label') || '').toLowerCase();
                const nameEl = app.querySelector('.app-cell-appname');
                const name = ((nameEl && nameEl.textContent) || app.textContent || '').toLowerCase();
                const label = aria || name;
                if (label.includes('mybc')) {
                    app.click();
                    return {
                        clicked: true,
                        label: ((nameEl && nameEl.textContent) || aria || 'MyBC').trim(),
                        href: app.getAttribute('href') || '',
                    };
                }
            }
            return { clicked: false, label: '', href: '' };
        """,
    )
    if clicked.get("clicked"):
        label: str = str(clicked.get("label") or "MyBC").strip()
        log(f"  OneLogin Portal : lancement {label}...")
        return True

    mybc_href: str = str(state.get("myBcHref") or clicked.get("href") or "").strip()
    if mybc_href:
        label = str(state.get("myBcLabel") or "MyBC").strip()
        log(f"  OneLogin Portal : navigation directe vers {label}...")
        await tab.get(mybc_href)
        return True

    return False


async def _ensure_mybc_post_logon_session(
    tab: Any,
    school_email: str,
    school_password: str,
    log: LogFn,
) -> Any:
    """
    Apres changement de mot de passe : portail OneLogin, email ecole, puis Student Post-Logon.
    """
    active_tab: Any = tab
    log(f"  Navigation portail OneLogin : {ONELOGIN_PORTAL_URL}")
    await active_tab.get(ONELOGIN_PORTAL_URL)
    await active_tab.sleep(2.5)
    await dismiss_onetrust_if_present(active_tab)

    attempts: int = max(1, int(MYBC_SESSION_TIMEOUT_S / 1.0))
    username_submitted: bool = False
    mybc_launched_from_portal: bool = False

    for i in range(attempts):
        mybc_tab: Any | None = await _find_mybc_tab(active_tab)
        if mybc_tab is not None:
            await mybc_tab.activate()
            active_tab = mybc_tab
            if await _is_mybc_post_logon_page(active_tab):
                log("  myBC Student Post-Logon pret (via portail OneLogin).")
                return active_tab

        ms_tab, _ms_state = await _find_microsoft_login_tab(active_tab)
        if ms_tab is not None:
            await ms_tab.activate()
            active_tab = await submit_microsoft_school_login(
                ms_tab,
                school_email,
                school_password,
                log,
            )
            await _dismiss_microsoft_stay_signed_in(active_tab)
            await active_tab.sleep(2.0)
            continue

        if not mybc_launched_from_portal:
            portal_tab: Any | None = await _find_onelogin_portal_tab(active_tab)
            if portal_tab is not None:
                await portal_tab.activate()
                active_tab = portal_tab
                await dismiss_onetrust_if_present(active_tab)
                if await _launch_mybc_from_onelogin_portal(active_tab, log):
                    mybc_launched_from_portal = True
                    await active_tab.sleep(3.0)
                continue

        if not username_submitted:
            onelogin_tab: Any | None = await _find_onelogin_username_tab(active_tab)
            if onelogin_tab is not None:
                await onelogin_tab.activate()
                active_tab = onelogin_tab
                await dismiss_onetrust_if_present(active_tab)
                await submit_bc_one_access_username(active_tab, school_email, log)
                username_submitted = True
                log("  OneLogin : email ecole saisi, redirection myBC attendue...")
                await active_tab.sleep(3.0)
                continue

        await active_tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente OneLogin → myBC Student Post-Logon ({i}/{attempts})...")

    raise RuntimeError(
        f"Page Student Post-Logon myBC introuvable apres {int(MYBC_SESSION_TIMEOUT_S)}s "
        f"(portail OneLogin + email {school_email}).",
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
) -> Any:
    """
    Apres changement de mot de passe : complete les 9 politiques Student Post-Logon myBC.
    """
    log(f"Etape 13/{MYBC_TOTAL_STEPS} — Portail OneLogin → myBC Student Post-Logon...")
    active_tab: Any = await _ensure_mybc_post_logon_session(tab, school_email, school_password, log)

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
    return active_tab


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

    log("Etape 5/12 — Connexion Microsoft (email ecole + mot de passe temporaire)...")
    ms_tab: Any = await submit_microsoft_school_login(onelogin_tab, school_email, temp_password, log)

    proof_tab: Any = await submit_proof_up_redirect(ms_tab, log)
    mfa_tab: Any = await advance_mysignins_register_steps(proof_tab, log)
    change_password_tab: Any = await complete_post_qr_mfa_flow(mfa_tab, log)
    change_password_tab = await submit_microsoft_change_password(
        change_password_tab,
        temp_password,
        account.password,
        log,
    )

    await complete_mybc_post_logon_policies(
        change_password_tab,
        school_email,
        account.password,
        log,
    )

    return StudentIdFlowResult(
        account_id=account.account_id,
        school_email=school_email,
        student_id=student_id,
        school_email_password=account.password,
    )
