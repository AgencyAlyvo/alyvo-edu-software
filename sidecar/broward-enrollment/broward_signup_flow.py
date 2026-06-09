"""
Automatisation inscription Broward College (TargetX / Salesforce).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any, Callable

from nodriver import cdp

from capsolver_client import CapSolverError, CapSolverProxyBannedError, solve_recaptcha_v2

SIGNUP_URL: str = (
    "https://broward.my.site.com/dualenrollment/TX_CommunitiesSelfReg"
    "?startURL=%2Fdualenrollment%2FTargetX_Base__Portal"
)
FORGOT_PASSWORD_URL: str = "https://broward.my.site.com/dualenrollment/TX_ForgotPassword"
OUTLOOK_ENTRY_URL: str = (
    "https://www.microsoft.com/fr-fr/microsoft-365/outlook/email-and-calendar-software-microsoft-outlook"
    "?deeplink=%2Fmail%2F&sdf=0"
)
RECAPTCHA_SITE_KEY: str = "6Lf5Gq8bAAAAAC3lTeW2iPoEkegr_8Xlc4TxbeKD"

SELECTOR_FIRST_NAME: str = 'input[name*="theForm:firstName"]'
SELECTOR_LAST_NAME: str = 'input[name*="theForm:lastName"]'
SELECTOR_BIRTHDATE: str = 'input[name*="theForm:Birthdate"]'
SELECTOR_EMAIL: str = 'input[name*="theForm:email"]'
SELECTOR_CONFIRM_EMAIL: str = 'input[name*="theForm:confirmEmail"]'
SELECTOR_SUBMIT: str = 'input[name*="theForm:submit"]'
SELECTOR_TOKEN_VALUE: str = 'input[name*="theForm:tokenValue"]'
SELECTOR_RECAPTCHA_RESPONSE: str = "#g-recaptcha-response"
SELECTOR_FORM_ERROR: str = "#j_id0\\:j_id2\\:theForm\\:error"
# TargetX : data-callback="recaptcha" -> recaptcha() -> callback() (jQuery, bas de page)

FIELD_SETTLE_DELAY_S: float = 0.15
STEP_PAUSE_AFTER_NAVIGATION_S: float = 1.0
RECAPTCHA_WIDGET_TIMEOUT_S: float = 45.0
SUBMIT_ENABLE_TIMEOUT_S: float = 45.0
POST_SUBMIT_TIMEOUT_S: float = 120.0
MANUAL_CAPTCHA_WAIT_S: float = 60.0
OUTLOOK_LOGIN_TIMEOUT_S: float = 180.0
OUTLOOK_MAIL_TIMEOUT_S: float = 180.0
BROWARD_PASSWORD_TIMEOUT_S: float = 120.0
BROWARD_OUTLOOK_SUBJECT: str = "Set your Broward College Application Password"
FORGOT_PASSWORD_EMAIL_SELECTOR: str = (
    'input[name*="theForm:username"], input[id*="theForm:username"], input[id$="username"]'
)
FORGOT_PASSWORD_SUBMIT_SELECTOR: str = (
    'input[name*="theForm:submit"], input[id*="theForm:submit"], input[id$="submit"]'
)
FORGOT_PASSWORD_VALIDATION_TIMEOUT_S: float = 60.0
FORGOT_PASSWORD_SUBMIT_STABLE_CHECKS: int = 3
FORGOT_PASSWORD_PRE_SUBMIT_DELAY_S: float = 1.0
FORGOT_PASSWORD_SUBMIT_PASSES: int = 1
FORGOT_PASSWORD_BETWEEN_PASSES_PAUSE_S: float = 2.0
OUTLOOK_MAIL_FORGOT_PASSWORD_RETRY_AT: int = 10
FORGOT_PASSWORD_OUTLOOK_RETRY_PASSES: int = 1
FORGOT_PASSWORD_TYPE_DELAY_S: float = 0.09
FORGOT_PASSWORD_TYPE_PUNCTUATION_DELAY_S: float = 0.16

PORTAL_URL: str = "https://broward.my.site.com/dualenrollment/TargetX_Base__Portal#/"
PORTAL_START_APPLICATION_SELECTOR: str = (
    '.portal-block__button.new-app a[href*="TargetX_App__NewApplication"], '
    '.portal-block__button.new-app button, '
    'a[href*="TargetX_App__NewApplication"] button'
)
NEW_APPLICATION_US_BORN_SELECTOR: str = 'select[aria-label*="born in the US"]'
NEW_APPLICATION_TERM_SELECTOR: str = 'select[ng-model="deadline"]'
NEW_APPLICATION_START_SELECTOR: str = (
    'input.targetx-button.targetx-application-action[value="Start Application"]'
)
HELPFUL_TIPS_ACK_RADIO_SELECTOR: str = (
    'input[name*="BC_Helpful_Tips_Acknowledgement"][value="true"], '
    'input[id*="BC_Helpful_Tips_Acknowledgement__c_true"]'
)
HELPFUL_TIPS_SECTION_SELECTOR: str = '[id*="Helpful Tips"]'

APPLICATION_PORTAL_TIMEOUT_S: float = 120.0
APPLICATION_FORM_TIMEOUT_S: float = 180.0
BROWARD_PORTAL_URL: str = PORTAL_URL
BROWARD_APPLICATION_START_TIMEOUT_S: float = APPLICATION_FORM_TIMEOUT_S
VERIFY_SUBMIT_SELECTOR: str = (
    '.targetx-card-buttons input.targetx-button:not(.secondary), '
    'input.targetx-button[value*="Verify"]'
)
VERIFY_SUBMIT_MARKER: str = "alyvo-verify-submit"
VERIFY_SUBMIT_PRE_CLICK_DELAY_S: float = 0.4
NEW_APPLICATION_SELECT_SETTLE_S: float = 2.5
NEW_APPLICATION_TERM_OPTIONS_TIMEOUT_S: float = 90.0
NEW_APPLICATION_SELECT_MAX_ATTEMPTS: int = 8

LogFn = Callable[[str], None]


def normalize_broward_email(email: str) -> str:
    """
    Normalise l'email personnel (trim + minuscules, sans espaces parasites).
    @param email - Email brut.
    @returns Email normalise pour Broward / Outlook.
    """
    return email.strip().lower()


BROWARD_SSN_BASE: str = "579537797"
BROWARD_SSN_PREFIX: str = "57953"
BROWARD_SSN_BASE_SERIAL: int = 7797
BROWARD_SSN_MAX_ACCOUNTS: int = 1000


def derive_broward_ssn(account_id: int) -> str:
    """
    Derive a unique 9-digit SSN from the base by incrementing the serial (last 4 digits).
    account_id 1 -> 579537797, account_id 1000 -> 579538796.
    @param account_id - Managed account id (stable per candidate, 1..1000).
    @returns Nine-digit SSN string.
    """
    if account_id < 1 or account_id > BROWARD_SSN_MAX_ACCOUNTS:
        raise ValueError(
            f"account_id must be between 1 and {BROWARD_SSN_MAX_ACCOUNTS}, got {account_id}"
        )

    serial: int = BROWARD_SSN_BASE_SERIAL + (account_id - 1)
    if serial > 9999:
        raise ValueError(f"SSN serial overflow for account_id {account_id}")

    return f"{BROWARD_SSN_PREFIX}{serial:04d}"


@dataclass(frozen=True)
class BrowardAccountInput:
    account_id: int
    first_name: str
    last_name: str
    birthday: str
    email: str
    password: str
    born_in_us_territory: str = "Yes"
    application_term: str = "Summer"
    street: str = "3020 Lake Spier Dr"
    city: str = "El Paso"
    state: str = "Texas"
    postal_code: str = "79936"
    mobile_phone: str = "9155550184"
    home_phone: str = ""
    ssn: str = BROWARD_SSN_BASE
    emergency_first_name: str = "Maria"
    emergency_last_name: str = "Johnson"
    emergency_relationship: str = "Other"
    emergency_mobile_phone: str = "9155550186"
    gender: str = "Female"
    race: str = "White"
    primary_language: str = "English"
    high_school_degree: str = "Standard High School Diploma"
    high_school_graduation_date: str = "2030-05-05"
    high_school_state: str = "Texas"
    high_school_name: str = "El Paso High School"


def unwrap_cdp_value(value: Any) -> Any:
    """
    Recupere la vraie valeur Python depuis les RemoteObject nodriver/CDP.
    @param value - Valeur brute retournee par nodriver.
    @returns Valeur serialisee si disponible.
    """
    if hasattr(value, "value"):
        remote_value: Any = getattr(value, "value")
        if remote_value is not None:
            return remote_value

    deep_serialized: Any = getattr(value, "deep_serialized_value", None)
    if deep_serialized is None:
        return value

    deep_value: Any = getattr(deep_serialized, "value", None)
    deep_type: str = str(getattr(deep_serialized, "type_", ""))

    if deep_type == "object" and isinstance(deep_value, list):
        output: dict[str, Any] = {}
        for item in deep_value:
            if not isinstance(item, list) or len(item) != 2:
                continue
            key, nested = item
            output[str(key)] = unwrap_deep_serialized_value(nested)
        return output

    if deep_type == "array" and isinstance(deep_value, list):
        return [unwrap_deep_serialized_value(item) for item in deep_value]

    return deep_value if deep_value is not None else value


def unwrap_deep_serialized_value(value: Any) -> Any:
    """
    Convertit une entree deep_serialized_value en valeur Python.
    @param value - Entree CDP (dict ou objet).
    @returns Valeur Python.
    """
    if isinstance(value, dict):
        value_type: str = str(value.get("type", ""))
        nested_value: Any = value.get("value")
        if value_type == "object" and isinstance(nested_value, list):
            return {
                str(item[0]): unwrap_deep_serialized_value(item[1])
                for item in nested_value
                if isinstance(item, list) and len(item) == 2
            }
        if value_type == "array" and isinstance(nested_value, list):
            return [unwrap_deep_serialized_value(item) for item in nested_value]
        return nested_value

    return unwrap_cdp_value(value)


async def fill_input_fast(tab: Any, selector: str, value: str) -> None:
    """Remplit un champ texte immediatement (pas de frappe simulee)."""
    element: Any = await tab.select(selector, timeout=45)
    value_json: str = json.dumps(value)
    selector_json: str = json.dumps(selector)
    await element.clear_input()
    await element.apply(
        f"(el) => {{ const v = {value_json}; el.focus(); el.value = v; "
        'el.dispatchEvent(new Event("input", { bubbles: true })); '
        'el.dispatchEvent(new Event("change", { bubbles: true })); '
        "el.classList.add('targetx-dirty', 'targetx-has-value'); "
        'el.dispatchEvent(new Event("blur", { bubbles: true })); }}',
        return_by_value=True,
    )
    filled: bool = await js_eval_bool(
        tab,
        f"""
        () => {{
            const el = document.querySelector({selector_json});
            return !!(el && el.value === {value_json});
        }}
        """,
    )
    if not filled:
        await element.send_keys(value)
    await tab.sleep(FIELD_SETTLE_DELAY_S)


async def fill_date_input_fast(tab: Any, selector: str, iso_date: str) -> None:
    """Remplit un input type=date (YYYY-MM-DD) immediatement."""
    element: Any = await tab.select(selector, timeout=45)
    date_json: str = json.dumps(iso_date)
    selector_json: str = json.dumps(selector)
    day, month, year = iso_date[8:10], iso_date[5:7], iso_date[0:4]
    localized_date_json: str = json.dumps(f"{day}/{month}/{year}")
    await element.clear_input()
    await element.apply(
        f"(el) => {{ const v = {date_json}; el.focus(); el.value = v; "
        "if (el.value !== v) { "
        "  const [y, m, d] = v.split('-').map(Number); "
        "  el.valueAsDate = new Date(y, m - 1, d); "
        "} "
        'el.dispatchEvent(new Event("input", { bubbles: true })); '
        'el.dispatchEvent(new Event("change", { bubbles: true })); '
        "el.classList.add('targetx-dirty', 'targetx-has-value'); "
        'el.dispatchEvent(new Event("blur", { bubbles: true })); }}',
        return_by_value=True,
    )
    filled: bool = await js_eval_bool(
        tab,
        f"""
        () => {{
            const el = document.querySelector({selector_json});
            return !!(el && el.value === {date_json});
        }}
        """,
    )
    if not filled:
        await element.clear_input()
        await element.send_keys(json.loads(localized_date_json))
    await tab.sleep(FIELD_SETTLE_DELAY_S)


async def wait_for_page_text(tab: Any, text: str, timeout_s: float, log: LogFn | None = None) -> bool:
    """
    Attend qu'un texte apparaisse dans la page.
    @param tab - Onglet nodriver.
    @param text - Texte attendu.
    @param timeout_s - Delai max.
    @param log - Log optionnel.
    @returns True si trouve.
    """
    needle: str = text.lower()
    attempts: int = max(1, int(timeout_s / 1.0))
    for i in range(attempts):
        found: bool = await js_eval_bool(
            tab,
            f"""
            () => {{
                const body = (document.body?.innerText || '').toLowerCase();
                return body.includes({json.dumps(needle)});
            }}
            """,
        )
        if found:
            return True
        await tab.sleep(1.0)
        if log and i > 0 and i % 15 == 0:
            log(f"  Attente texte « {text[:40]} » ({i}/{attempts})...")
    return False


async def click_first_match(tab: Any, selector: str) -> bool:
    """
    Clique le premier element correspondant.
    @param tab - Onglet nodriver.
    @param selector - Selecteur CSS.
    @returns True si clic effectue.
    """
    selector_json: str = json.dumps(selector)
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            const el = document.querySelector({selector_json});
            if (!el) return false;
            el.scrollIntoView({{ block: 'center' }});
            el.click();
            return true;
        }}
        """,
    )


async def js_eval(tab: Any, expression: str, *, await_promise: bool = False) -> Any:
    """
    Execute du JS dans la page (nodriver exige return_by_value pour lire le resultat).
    @param tab - Onglet nodriver.
    @param expression - Expression JS (souvent `() => ...`).
    @param await_promise - Attendre les promesses JS.
    @returns Valeur serialisee depuis Chrome.
    """
    return unwrap_cdp_value(
        await tab.evaluate(
            executable_js_expression(expression),
            await_promise=await_promise,
            return_by_value=True,
        )
    )


async def js_eval_bool(tab: Any, expression: str) -> bool:
    """Comme js_eval mais force un bool Python."""
    return bool(await js_eval(tab, expression))


def executable_js_expression(expression: str) -> str:
    """
    Convertit une fonction flechee JS en expression executee pour nodriver.
    @param expression - Expression JS brute.
    @returns Expression executable.
    """
    stripped: str = expression.strip()
    if stripped.startswith("() =>") or stripped.startswith("async () =>"):
        return f"({stripped})()"
    return stripped


async def js_eval_json(tab: Any, body: str) -> dict[str, Any]:
    """
    Execute un bloc JS qui retourne un objet, via JSON.stringify (fiable avec nodriver).
    @param tab - Onglet nodriver.
    @param body - Corps JS avec `return { ... };` final, ou `() => { return ... }`.
    @returns Objet Python parse depuis JSON.
    """
    stripped: str = body.strip()
    if stripped.startswith("() =>") or stripped.startswith("async () =>"):
        value_expr: str = executable_js_expression(stripped)
    else:
        value_expr = f"(() => {{\n{body}\n}})()"

    expression: str = f"""
    (() => {{
        try {{
            const value = {value_expr};
            return JSON.stringify(value ?? null);
        }} catch (e) {{
            return JSON.stringify({{ jsError: String(e) }});
        }}
    }})()
    """
    raw: Any = unwrap_cdp_value(await tab.evaluate(expression, await_promise=True, return_by_value=True))
    if isinstance(raw, str) and raw:
        try:
            parsed: Any = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            return {"parsed": parsed}
        except json.JSONDecodeError:
            return {"jsonError": raw[:240]}
    return {"evalError": type(raw).__name__, "raw": str(raw)[:240]}


async def prepare_captcha_section(tab: Any, log: LogFn) -> None:
    """Scroll vers le captcha et laisse le temps aux scripts TargetX (bas de page)."""
    await js_eval(tab, "() => { window.scrollTo(0, document.body.scrollHeight); }")
    await tab.sleep(0.8)
    await js_eval(
        tab,
        """
        () => {
            const w = document.querySelector('.g-recaptcha');
            if (w) w.scrollIntoView({ block: 'center' });
        }
        """,
    )
    await tab.sleep(0.5)
    ready_state: Any = await js_eval(tab, "() => document.readyState")
    log(f"  Page prete pour captcha (readyState={ready_state}).")


async def wait_for_broward_captcha_scripts(tab: Any, log: LogFn) -> bool:
    """Attend le widget reCAPTCHA TargetX + jQuery + callback() (script bas de page Broward)."""
    attempts: int = max(1, int(RECAPTCHA_WIDGET_TIMEOUT_S / 0.5))
    for i in range(attempts):
        status: dict[str, Any] = await js_eval_json(
            tab,
            """
            const hasDollar = typeof $ === 'function' && !!$.fn;
            const hasJquery = typeof jQuery === 'function';
            return {
                widget: !!document.querySelector('.g-recaptcha[data-callback="recaptcha"]'),
                tokenField: !!document.querySelector('input[id$="tokenValue"], input[name*="tokenValue"]'),
                submit: !!document.querySelector('input[id$="submit"], input[name*="theForm:submit"]'),
                jquery: hasDollar || hasJquery,
                callback: typeof callback === 'function',
                recaptcha: typeof recaptcha === 'function',
                readyState: document.readyState,
            };
            """,
        )
        dom_ready: bool = bool(
            status.get("widget") and status.get("tokenField") and status.get("submit")
        )
        scripts_ready: bool = bool(status.get("callback") or status.get("jquery"))
        if dom_ready and (scripts_ready or i >= 10):
            parts: list[str] = []
            if status.get("callback"):
                parts.append("callback")
            if status.get("recaptcha"):
                parts.append("recaptcha")
            if status.get("jquery"):
                parts.append("jQuery")
            log(
                "  Formulaire captcha pret"
                + (f" ({', '.join(parts)})" if parts else " (injection DOM directe)")
                + "."
            )
            return True
        await tab.sleep(0.5)
        if i > 0 and i % 8 == 0:
            missing: str = ", ".join(
                key
                for key in ("widget", "tokenField", "submit", "callback", "jquery")
                if not status.get(key)
            )
            log(f"  En attente captcha ({i}/{attempts}) — manque : {missing or 'inconnu'}")
    log("  Delai captcha depasse (widget/token/submit).")
    return False


async def inject_recaptcha_token(tab: Any, token: str, log: LogFn) -> dict[str, Any]:
    """
    Injecte le token CapSolver selon le flux Broward/TargetX :
    - textarea #g-recaptcha-response
    - input tokenValue (cache)
    - callback(token) jQuery : $("input[id$=tokenValue]").val(token) + active Submit
    - recaptcha(token) data-callback (relaye vers callback)
    La case visuelle peut rester decochee ; pas de clic requis si callback() reussit.
    """
    token_json: str = json.dumps(token)

    result: dict[str, Any] = await js_eval_json(
        tab,
        f"""
            const token = {token_json};
            const steps = [];
            const errors = [];

            document.querySelectorAll('#g-recaptcha-response, textarea.g-recaptcha-response').forEach((el) => {{
                el.value = token;
            }});
            steps.push('g-recaptcha-response');

            const tokenInput = document.querySelector(
                'input[id$="tokenValue"], input[name*="tokenValue"]',
            );
            const submit = document.querySelector(
                'input[id$="submit"], input[name*="theForm:submit"]',
            );

            if (tokenInput) {{
                tokenInput.value = token;
                steps.push('tokenValue-dom');
            }} else {{
                errors.push('tokenValue introuvable');
            }}

            if (submit && token) {{
                submit.disabled = false;
                submit.removeAttribute('disabled');
                steps.push('submit-dom-enable');
            }}

            try {{
                if (typeof callback === 'function') {{
                    callback(token);
                    steps.push('callback()');
                }}
            }} catch (e) {{
                errors.push('callback:' + String(e));
            }}

            try {{
                if (typeof recaptcha === 'function') {{
                    recaptcha(token);
                    steps.push('recaptcha()');
                }}
            }} catch (e) {{
                errors.push('recaptcha:' + String(e));
            }}

            try {{
                if (typeof $ === 'function' && $.fn) {{
                    $('input[id$=tokenValue]').val(token);
                    if (token) $('input[id$=submit]').prop('disabled', false);
                    steps.push('jQuery');
                }} else if (typeof jQuery === 'function') {{
                    jQuery('input[id$=tokenValue]').val(token);
                    if (token) jQuery('input[id$=submit]').prop('disabled', false);
                    steps.push('jQuery.noConflict');
                }}
            }} catch (e) {{
                errors.push('jquery:' + String(e));
            }}

            let submitEnabled = !!(submit && !submit.disabled);
            if (!submitEnabled && typeof $ === 'function' && $.fn) {{
                const jq = $('input[id$=submit]');
                submitEnabled = jq.length > 0 && !jq.prop('disabled');
            }}

            const tokenValueLen = tokenInput && tokenInput.value ? tokenInput.value.length : 0;
            return {{ steps, errors, submitEnabled, tokenValueLen }};
        """,
    )

    steps: list[str] = list(result.get("steps") or [])
    errors: list[str] = list(result.get("errors") or [])
    if result.get("jsError"):
        errors.append(str(result["jsError"]))
    if result.get("jsonError"):
        errors.append(str(result["jsonError"]))
    if result.get("evalError"):
        errors.append(str(result.get("evalError")))
    token_value_len: int = int(result.get("tokenValueLen") or 0)
    submit_enabled: bool = bool(result.get("submitEnabled"))

    if steps:
        log(f"  Injection TargetX : {', '.join(steps)}")
    if errors:
        log(f"  Injection — avertissements : {'; '.join(errors[:4])}")

    log(
        f"  tokenValue ({token_value_len} car.), Submit actif : "
        f"{'oui' if submit_enabled else 'non'}."
    )

    return result


async def is_submit_enabled(tab: Any) -> bool:
    """Verifie si le bouton Soumettre est actif (DOM + etat jQuery TargetX)."""
    return await js_eval_bool(
        tab,
        """
        () => {
            const btn = document.querySelector('input[id$="submit"], input[name*="theForm:submit"]');
            if (!btn) return false;
            if (typeof $ === 'function' && $.fn) {
                const jq = $('input[id$=submit]');
                if (jq.length && jq.prop('disabled')) return false;
            } else if (btn.disabled) {
                return false;
            }
            const style = window.getComputedStyle(btn);
            if (style.display === 'none' || style.visibility === 'hidden') return false;
            return true;
        }
        """,
    )


async def force_enable_submit(tab: Any) -> None:
    """Reactive Submit comme le script TargetX (jQuery ou DOM)."""
    await js_eval(
        tab,
        """
        () => {
            if (typeof $ === 'function' && $.fn) {
                $('input[id$=submit]').prop('disabled', false);
            } else if (typeof jQuery === 'function') {
                jQuery('input[id$=submit]').prop('disabled', false);
            }
            const btn = document.querySelector('input[id$="submit"], input[name*="theForm:submit"]');
            if (!btn) return;
            btn.disabled = false;
            btn.removeAttribute('disabled');
        }
        """,
    )


async def wait_for_submit_enabled(tab: Any, log: LogFn, timeout_s: float) -> bool:
    """Attend que le bouton Submit ne soit plus disabled."""
    attempts: int = max(1, int(timeout_s / 0.5))
    for i in range(attempts):
        if await is_submit_enabled(tab):
            log("  Bouton Submit actif.")
            return True
        await force_enable_submit(tab)
        await tab.sleep(0.5)
        if i > 0 and i % 10 == 0:
            log(f"  En attente bouton Submit ({i}/{attempts})...")
    return False


async def wait_for_manual_captcha(tab: Any, log: LogFn) -> bool:
    """Attend qu'un humain coche le captcha ou que Submit s'active."""
    log(
        f"  CapSolver n'a pas active Submit — {int(MANUAL_CAPTCHA_WAIT_S)} s pour cocher le captcha a la main "
        "(case « Je ne suis pas un robot »)..."
    )
    attempts: int = max(1, int(MANUAL_CAPTCHA_WAIT_S / 1.0))
    for i in range(attempts):
        has_token: bool = await js_eval_bool(
            tab,
            """
            () => {
                const hidden = document.querySelector('input[id$="tokenValue"], input[name*="tokenValue"]');
                if (hidden && hidden.value && hidden.value.length > 20) return true;
                const el = document.querySelector('#g-recaptcha-response');
                return !!(el && el.value && el.value.length > 20);
            }
            """,
        )
        if has_token and await is_submit_enabled(tab):
            log("  reCAPTCHA resolu (manuel ou auto).")
            return True
        if await is_submit_enabled(tab):
            log("  Bouton Submit actif (captcha valide).")
            return True
        await tab.sleep(1.0)
    return False


async def resolve_captcha(tab: Any, api_key: str, log: LogFn) -> bool:
    """Resout le captcha via CapSolver puis callback() TargetX (jQuery)."""
    await prepare_captcha_section(tab, log)
    if not await wait_for_broward_captcha_scripts(tab, log):
        log("  Widget/token/submit pas tous visibles — injection DOM tentera quand meme.")

    try:
        token: str = solve_recaptcha_v2(
            api_key,
            SIGNUP_URL,
            RECAPTCHA_SITE_KEY,
            log=log,
        )
        await inject_recaptcha_token(tab, token, log)

        if await wait_for_submit_enabled(tab, log, SUBMIT_ENABLE_TIMEOUT_S):
            return True

        log("  Submit toujours inactif apres injection — nouvel essai de callbacks...")
        await inject_recaptcha_token(tab, token, log)
        if await wait_for_submit_enabled(tab, log, timeout_s=10.0):
            return True

        log(
            "  CapSolver a fourni le token mais la page n'a pas active Submit. "
            "Pas besoin de cocher si le callback fonctionne ; sinon cochez manuellement."
        )
        return await wait_for_manual_captcha(tab, log)
    except CapSolverProxyBannedError:
        raise
    except CapSolverError as error:
        log(f"  CapSolver : {error}")
        return await wait_for_manual_captcha(tab, log)


async def click_submit(tab: Any, log: LogFn) -> None:
    """Clique sur Soumettre (jQuery TargetX ou nodriver)."""
    await force_enable_submit(tab)

    clicked: bool = await js_eval_bool(
        tab,
        """
        () => {
            if (typeof $ === 'function' && $.fn) {
                const btn = $('input[id$=submit]');
                if (btn.length) {
                    btn.prop('disabled', false);
                    btn[0].scrollIntoView({ block: 'center' });
                    btn.trigger('click');
                    btn[0].click();
                    return true;
                }
            }
            const btn = document.querySelector('input[id$="submit"], input[name*="theForm:submit"]');
            if (!btn) return false;
            btn.disabled = false;
            btn.removeAttribute('disabled');
            btn.scrollIntoView({ block: 'center' });
            btn.click();
            return true;
        }
        """,
    )
    if clicked:
        log("  Clic sur Soumettre.")
        return

    submit: Any = await tab.select(SELECTOR_SUBMIT, timeout=15)
    await submit.scroll_into_view()
    await submit.click()
    log("  Clic sur Soumettre (nodriver).")


async def wait_for_post_submit(tab: Any, log: LogFn) -> None:
    """Attend une confirmation ou l'absence d'erreur formulaire."""
    log("  Attente de la confirmation apres Submit...")
    initial_url: str = str(await js_eval(tab, "() => window.location.href") or "")
    attempts: int = max(1, int(POST_SUBMIT_TIMEOUT_S / 1.0))

    for i in range(attempts):
        error_text: Any = await js_eval(
            tab,
            f"""
            () => {{
                const el = document.querySelector('{SELECTOR_FORM_ERROR}');
                return el ? (el.innerText || el.textContent || '').trim() : '';
            }}
            """,
        )
        if isinstance(error_text, str) and error_text.strip():
            raise RuntimeError(f"Erreur formulaire Broward : {error_text.strip()}")

        current_url: str = str(await js_eval(tab, "() => window.location.href") or "")
        if current_url != initial_url and "TX_CommunitiesSelfReg" not in current_url:
            log(f"  Navigation detectee : {current_url[:80]}...")
            return

        still_on_form: bool = await js_eval_bool(
            tab,
            f"() => !!document.querySelector('{SELECTOR_FIRST_NAME}')",
        )
        if not still_on_form:
            log("  Formulaire d'inscription plus visible — succes probable.")
            return

        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Toujours en attente confirmation ({i}/{attempts})...")

    log("  Delai post-Submit atteint — inscription consideree comme terminee si pas d'erreur.")


async def broward_fire_keyup_check_email(tab: Any, key: str = "") -> None:
    """
    Reproduit onkeyup=\"checkEmail(this.value)\" apres chaque touche.
    @param tab - Onglet nodriver.
    @param key - Touche frappe (pour l'evenement clavier).
    """
    email_selector_json: str = json.dumps(FORGOT_PASSWORD_EMAIL_SELECTOR)
    key_json: str = json.dumps(key)
    await js_eval(
        tab,
        f"""
        () => {{
            const input = document.querySelector({email_selector_json});
            if (!input) return;
            const value = input.value || '';
            input.dispatchEvent(
                new KeyboardEvent('keyup', {{ bubbles: true, key: {key_json}, cancelable: true }}),
            );
            if (typeof checkEmail === 'function') {{
                checkEmail(value);
            }}
        }}
        """,
    )


async def type_broward_forgot_password_email(
    tab: Any,
    element: Any,
    email: str,
    log: LogFn,
) -> None:
    """
    Saisit l'email comme un humain, avec checkEmail() apres chaque touche.
    @param tab - Onglet nodriver.
    @param element - Champ username TargetX.
    @param email - Email a taper (deja normalise).
    @param log - Journal stderr.
    """
    await element.scroll_into_view()
    await element.click()
    await tab.sleep(0.35)
    await element.clear_input()
    await tab.sleep(0.25)

    log(f"  Frappe email Broward ({len(email)} caracteres) avec checkEmail a chaque touche...")
    for char in email:
        await element.send_keys(char)
        await broward_fire_keyup_check_email(tab, char)
        await tab.sleep(
            FORGOT_PASSWORD_TYPE_PUNCTUATION_DELAY_S
            if char in "@._-"
            else FORGOT_PASSWORD_TYPE_DELAY_S
        )

    await tab.sleep(0.6)
    await broward_fire_keyup_check_email(tab, "Tab")
    await js_eval(
        tab,
        f"""
        () => {{
            const input = document.querySelector({json.dumps(FORGOT_PASSWORD_EMAIL_SELECTOR)});
            if (!input) return;
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            input.dispatchEvent(new FocusEvent('blur', {{ bubbles: true }}));
        }}
        """,
    )


async def read_broward_forgot_password_form_state(tab: Any) -> dict[str, Any]:
    """
    Lit la valeur email et l'etat du bouton Request Password.
    @param tab - Onglet nodriver.
    @returns Etat formulaire Forgot Password.
    """
    email_selector_json: str = json.dumps(FORGOT_PASSWORD_EMAIL_SELECTOR)
    submit_selector_json: str = json.dumps(FORGOT_PASSWORD_SUBMIT_SELECTOR)
    return await js_eval_json(
        tab,
        f"""
            const input = document.querySelector({email_selector_json});
            const btn = document.querySelector({submit_selector_json});
            const errorNode = document.querySelector(
                '#j_id0\\\\:j_id1\\\\:theForm\\\\:error, #j_id0\\\\:j_id2\\\\:theForm\\\\:error, [id*="theForm:error"], .message.errorM3, .errorMsg',
            );
            const inlineError = document.querySelector('#error-message');
            const inlineErrorText = ((inlineError && inlineError.textContent) || '').trim();
            const formErrorText = ((errorNode && errorNode.textContent) || '').trim();
            const btnDisabled = !btn
                || btn.disabled
                || btn.hasAttribute('disabled')
                || btn.classList.contains('targetx-button-disabled')
                || btn.getAttribute('aria-disabled') === 'true';
            return {{
                value: ((input && input.value) || '').trim().toLowerCase(),
                submitReady: !!btn && !btnDisabled,
                errorText: (formErrorText || inlineErrorText).slice(0, 240),
                inlineError: inlineErrorText.slice(0, 240),
                buttonClass: btn ? (btn.className || '') : '',
            }};
        """,
    )


async def wait_for_broward_forgot_password_ready(
    tab: Any,
    expected_email: str,
    log: LogFn,
    timeout_s: float = FORGOT_PASSWORD_VALIDATION_TIMEOUT_S,
) -> None:
    """
    Attend que checkEmail() reactive Request Password (stable plusieurs cycles avant clic).
    @param tab - Onglet nodriver.
    @param expected_email - Email Outlook normalise attendu.
    @param log - Journal stderr.
    @param timeout_s - Delai max.
    """
    attempts: int = max(1, int(timeout_s / 0.5))
    last_error: str = ""
    last_value: str = ""
    stable_ready: int = 0

    for i in range(attempts):
        state: dict[str, Any] = await read_broward_forgot_password_form_state(tab)
        last_value = str(state.get("value") or "")
        last_error = str(state.get("errorText") or "")
        inline_error: str = str(state.get("inlineError") or "")

        if last_error or inline_error:
            stable_ready = 0
        elif last_value == expected_email and state.get("submitReady"):
            stable_ready += 1
            if stable_ready >= FORGOT_PASSWORD_SUBMIT_STABLE_CHECKS:
                log(
                    "  checkEmail OK — Request Password actif de facon stable"
                    f" ({stable_ready * 0.5:.1f}s).",
                )
                await tab.sleep(FORGOT_PASSWORD_PRE_SUBMIT_DELAY_S)
                return
        else:
            stable_ready = 0

        if stable_ready == 0 and i > 0 and i % 20 == 0:
            await broward_fire_keyup_check_email(tab)

        await tab.sleep(0.5)
        if i > 0 and i % 16 == 0:
            log(
                f"  Attente validation checkEmail ({i}/{attempts})"
                f" — email={last_value!r}, bouton={'actif' if state.get('submitReady') else 'desactive'}"
                f", stable={stable_ready}/{FORGOT_PASSWORD_SUBMIT_STABLE_CHECKS}...",
            )

    detail: str = f"champ={last_value!r}, attendu={expected_email!r}"
    if last_error:
        detail = f"{detail}, erreur={last_error!r}"
    raise RuntimeError(
        "Email Forgot Password : checkEmail n'a pas active Request Password assez longtemps "
        f"— {detail}. Verifiez l'email d'inscription sur TX_ForgotPassword.",
    )


async def fill_broward_forgot_password_email(tab: Any, email: str, log: LogFn) -> str:
    """
    Saisit l'email Outlook sur TX_ForgotPassword (saisie + checkEmail).
    @param tab - Onglet nodriver.
    @param email - Email brut.
    @param log - Journal stderr.
    @returns Email normalise effectivement present dans le champ.
    """
    normalized: str = normalize_broward_email(email)
    log(f"  Email Outlook Forgot Password : {normalized}")

    element: Any = await tab.select(FORGOT_PASSWORD_EMAIL_SELECTOR, timeout=45)
    await type_broward_forgot_password_email(tab, element, normalized, log)

    value_json: str = json.dumps(normalized)
    selector_json: str = json.dumps(FORGOT_PASSWORD_EMAIL_SELECTOR)
    filled: bool = await js_eval_bool(
        tab,
        f"""
        () => {{
            const el = document.querySelector({selector_json});
            if (!el) return false;
            const v = (el.value || '').trim().toLowerCase();
            return v === {value_json};
        }}
        """,
    )
    if not filled:
        log("  Reessai saisie email...")
        await type_broward_forgot_password_email(tab, element, normalized, log)
        filled = await js_eval_bool(
            tab,
            f"""
            () => {{
                const el = document.querySelector({selector_json});
                return !!el && (el.value || '').trim().toLowerCase() === {value_json};
            }}
            """,
        )

    if not filled:
        state: dict[str, Any] = await read_broward_forgot_password_form_state(tab)
        actual: str = str(state.get("value") or "")
        raise RuntimeError(
            f"Impossible de saisir l'email Forgot Password (attendu {normalized!r}, lu {actual!r}).",
        )

    return normalized


async def click_broward_request_password_submit(tab: Any, log: LogFn) -> None:
    """
    Clique Request Password avec un vrai clic souris nodriver (soumission POST native).
    @param tab - Onglet nodriver.
    @param log - Journal stderr.
    """
    submit_selector_json: str = json.dumps(FORGOT_PASSWORD_SUBMIT_SELECTOR)
    marker: str = "alyvo-broward-submit"
    marker_json: str = json.dumps(marker)

    ready: bool = await js_eval_bool(
        tab,
        f"""
        () => {{
            const btn = document.querySelector({submit_selector_json});
            if (!btn) return false;
            const disabled = btn.disabled
                || btn.hasAttribute('disabled')
                || btn.classList.contains('targetx-button-disabled');
            if (disabled) return false;
            btn.setAttribute('data-alyvo-submit', {marker_json});
            btn.scrollIntoView({{ block: 'center' }});
            return true;
        }}
        """,
    )
    if not ready:
        raise RuntimeError(
            "Request Password encore desactive au moment du clic — checkEmail non termine.",
        )

    await tab.sleep(0.4)

    clicked_real: bool = False
    try:
        element: Any = await tab.select(f'input[data-alyvo-submit="{marker}"]', timeout=8)
        await element.scroll_into_view()
        await tab.sleep(0.3)
        await element.click()
        clicked_real = True
        log("  Clic Request Password (vrai clic souris nodriver).")
    except Exception as error:  # noqa: BLE001
        log(f"  Clic souris nodriver indisponible ({error}); soumission native du formulaire.")

    if not clicked_real:
        submitted: bool = await js_eval_bool(
            tab,
            f"""
            () => {{
                const btn = document.querySelector({submit_selector_json});
                if (!btn) return false;
                const form = btn.form || btn.closest('form');
                if (form && typeof form.requestSubmit === 'function') {{
                    form.requestSubmit(btn);
                    return true;
                }}
                if (typeof btn.click === 'function') {{
                    btn.click();
                    return true;
                }}
                if (form && typeof form.submit === 'function') {{
                    form.submit();
                    return true;
                }}
                return false;
            }}
            """,
        )
        if not submitted:
            raise RuntimeError("Soumission Request Password impossible (bouton/formulaire introuvable).")
        log("  Soumission Request Password (form.submit natif).")


async def _read_broward_forgot_password_post_submit(tab: Any) -> dict[str, Any]:
    """
    Lit erreurs et indicateurs de confirmation apres Request Password.
    @param tab - Onglet nodriver.
    @returns Dict errorText, hasThankYou, url.
    """
    return await js_eval_json(
        tab,
        """
            const errorNode = document.querySelector(
                '#j_id0\\\\:j_id1\\\\:theForm\\\\:error, #j_id0\\\\:j_id2\\\\:theForm\\\\:error, [id*="theForm:error"], #error-message, .message.errorM3, .errorMsg',
            );
            const body = (document.body?.innerText || '').trim();
            return {
                errorText: ((errorNode && errorNode.textContent) || '').trim().slice(0, 320),
                hasThankYou: body.toLowerCase().includes('you have been sent an email')
                    || body.toLowerCase().includes('create a new password'),
                url: (location.href || '').slice(0, 160),
            };
        """,
    )


async def _broward_forgot_password_confirmation_visible(tab: Any) -> bool:
    """
    Indique si la page confirme l'envoi du mail Set Password.
    @param tab - Onglet nodriver.
    @returns True si texte de confirmation present.
    """
    post_submit: dict[str, Any] = await _read_broward_forgot_password_post_submit(tab)
    if post_submit.get("hasThankYou"):
        return True
    body: str = str(
        await js_eval(tab, "() => (document.body?.innerText || '').toLowerCase()") or "",
    )
    return (
        "you have been sent an email" in body
        or "create a new password" in body
        or "forgotpasswordconfirm" in str(await js_eval(tab, "() => (location.href || '').toLowerCase()") or "")
    )


async def submit_broward_forgot_password_pass(
    tab: Any,
    account: BrowardAccountInput,
    log: LogFn,
    *,
    pass_index: int,
    pass_total: int,
) -> bool:
    """
    Une passe TX_ForgotPassword : saisie email, Request Password, verification courte.
    @param tab - Onglet nodriver.
    @param account - Compte courant.
    @param log - Journal stderr.
    @param pass_index - Numero de passe (1-based).
    @param pass_total - Nombre total de passes.
    @returns True si confirmation detectee apres cette passe.
    """
    log(f"  Passe {pass_index}/{pass_total} — TX_ForgotPassword (sans attente prealable)...")
    await tab.get(FORGOT_PASSWORD_URL)
    await tab.sleep(2.0)

    expected_email: str = await fill_broward_forgot_password_email(tab, account.email, log)
    await wait_for_broward_forgot_password_ready(tab, expected_email, log)

    view_state_before: str = str(
        await js_eval(
            tab,
            """
            () => {
                const vs = document.querySelector('#com\\\\.salesforce\\\\.visualforce\\\\.ViewState');
                return vs ? (vs.value || '').slice(0, 40) : '';
            }
            """,
        )
        or "",
    )

    await click_broward_request_password_submit(tab, log)
    await tab.sleep(2.5)

    view_state_after: str = str(
        await js_eval(
            tab,
            """
            () => {
                const vs = document.querySelector('#com\\\\.salesforce\\\\.visualforce\\\\.ViewState');
                return vs ? (vs.value || '').slice(0, 40) : '';
            }
            """,
        )
        or "",
    )
    if view_state_before and view_state_after and view_state_before != view_state_after:
        log("  POST Broward confirme (ViewState recharge apres Request Password).")

    post_submit: dict[str, Any] = await _read_broward_forgot_password_post_submit(tab)
    post_error: str = str(post_submit.get("errorText") or "").strip()
    if post_error:
        log(
            f"  Passe {pass_index}/{pass_total} : message Broward "
            f"({post_error[:120]}) — poursuite des passes suivantes.",
        )
        return False

    if post_submit.get("hasThankYou"):
        log(f"  Passe {pass_index}/{pass_total} : confirmation page OK.")
        return True

    if await wait_for_page_text(tab, "create a new password", 8.0):
        log(f"  Passe {pass_index}/{pass_total} : confirmation « create a new password ».")
        return True

    if await wait_for_page_text(tab, "You have been sent an email", 5.0):
        log(f"  Passe {pass_index}/{pass_total} : confirmation « You have been sent an email ».")
        return True

    if await _broward_forgot_password_confirmation_visible(tab):
        log(f"  Passe {pass_index}/{pass_total} : confirmation detectee (URL/texte).")
        return True

    log(f"  Passe {pass_index}/{pass_total} : pas de confirmation explicite (nouvelle passe si prevue).")
    return False


async def request_broward_password_email(tab: Any, account: BrowardAccountInput, log: LogFn) -> None:
    """
    Demande l'email Broward : 1 passe Request Password (relance possible depuis Outlook si mail absent).
    @param tab - Onglet nodriver.
    @param account - Compte courant.
    @param log - Journal stderr.
    """
    log(
        f"Etape 6/9 — Demande email Broward « Set Password » "
        f"({FORGOT_PASSWORD_SUBMIT_PASSES} passes sur TX_ForgotPassword)...",
    )
    expected_email: str = normalize_broward_email(account.email)
    confirmed: bool = False

    for pass_index in range(1, FORGOT_PASSWORD_SUBMIT_PASSES + 1):
        if pass_index > 1:
            log(
                f"  Retour sur TX_ForgotPassword pour une {pass_index}e passe "
                f"({FORGOT_PASSWORD_SUBMIT_PASSES} au total)...",
            )
            await tab.sleep(FORGOT_PASSWORD_BETWEEN_PASSES_PAUSE_S)

        pass_confirmed: bool = await submit_broward_forgot_password_pass(
            tab,
            account,
            log,
            pass_index=pass_index,
            pass_total=FORGOT_PASSWORD_SUBMIT_PASSES,
        )
        confirmed = confirmed or pass_confirmed

    if not confirmed:
        post_submit: dict[str, Any] = await _read_broward_forgot_password_post_submit(tab)
        if await wait_for_page_text(
            tab,
            "create a new password",
            BROWARD_PASSWORD_TIMEOUT_S,
            log,
        ):
            confirmed = True
        elif await wait_for_page_text(tab, "You have been sent an email", 5.0):
            confirmed = True

    if not confirmed:
        raise RuntimeError(
            "Confirmation Forgot Password Broward introuvable apres "
            f"{FORGOT_PASSWORD_SUBMIT_PASSES} passes Request Password "
            f"(url={post_submit.get('url', '')!r}).",
        )

    log(
        f"  {FORGOT_PASSWORD_SUBMIT_PASSES} passes Request Password terminees pour {expected_email}"
        " — verifiez la boite Outlook (delai possible 1-5 min).",
    )


def _microsoft_input_visible_js() -> str:
    """Fonction JS partagee : champ Microsoft reellement interactif (pas moveOffScreen / hidden)."""
    return """
            const visible = (el) => {
                if (!el || el.disabled) return false;
                if (el.type === 'hidden' || el.getAttribute('aria-hidden') === 'true') return false;
                if (el.classList.contains('moveOffScreen')) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) {
                    return false;
                }
                const rect = el.getBoundingClientRect();
                if (rect.width < 4 || rect.height < 4) return false;
                if (rect.bottom < 0 || rect.right < 0) return false;
                if (rect.top > window.innerHeight || rect.left > window.innerWidth) return false;
                return true;
            };
    """


async def get_microsoft_login_state(tab: Any) -> dict[str, Any]:
    """
    Detecte l'etape de connexion Microsoft (email vs mot de passe Fluent / legacy).
    @param tab - Onglet nodriver.
    @returns Etat { step, outlook, staySignedIn, host, ... }.
    """
    return await js_eval_json(
        tab,
        f"""
        {_microsoft_input_visible_js()}
            const passwordForm = document.querySelector('form[data-testid="passwordEntryForm"]');
            const passwordEntry = document.querySelector('#passwordEntry');
            const onFluentPassword = !!(passwordForm && passwordEntry && visible(passwordEntry));

            const legacyPasswordInput = Array.from(
                document.querySelectorAll('#i0118, input[name="passwd"][type="password"]'),
            ).find((el) => visible(el) && !el.classList.contains('moveOffScreen'));
            const onPassword = onFluentPassword || !!legacyPasswordInput;

            const usernameInput = document.querySelector('#i0116')
                || Array.from(document.querySelectorAll('input[name="loginfmt"]')).find(
                    (el) => visible(el) && el.type !== 'hidden',
                )
                || Array.from(document.querySelectorAll('input[type="email"]')).find(visible);
            const onUsername = !!usernameInput && visible(usernameInput) && !onPassword;

            const primaryInForm = passwordForm
                ? passwordForm.querySelector('button[data-testid="primaryButton"], button[type="submit"]')
                : null;
            const primaryButton = primaryInForm
                || document.querySelector('#idSIButton9')
                || document.querySelector('button[data-testid="primaryButton"]');

            const bodyText = document.body?.innerText || '';
            return {{
                step: onPassword ? 'password' : onUsername ? 'username' : 'other',
                onPassword,
                onUsername,
                next: !!primaryButton,
                host: location.hostname || '',
                href: (location.href || '').slice(0, 120),
                outlook: !!document.querySelector(
                    '#MailList, #topSearchInput, [data-test-id="mailMessageBodyContainer"]',
                ),
                staySignedIn: bodyText.includes('Stay signed in')
                    || bodyText.includes('Rester connecté')
                    || bodyText.includes('Rester connecte'),
            }};
        """,
    )


async def wait_for_microsoft_login_step(
    tab: Any,
    step: str,
    timeout_s: float,
    log: LogFn | None = None,
) -> bool:
    """
    Attend qu'une etape Microsoft (username | password) soit affichee.
    @param tab - Onglet nodriver.
    @param step - Etape attendue.
    @param timeout_s - Delai max.
    @param log - Journal optionnel.
    @returns True si l'etape est atteinte.
    """
    key: str = "onPassword" if step == "password" else "onUsername"
    attempts: int = max(1, int(timeout_s / 0.5))
    for i in range(attempts):
        state: dict[str, Any] = await get_microsoft_login_state(tab)
        if state.get(key):
            return True
        if state.get("outlook"):
            return step == "password"
        await tab.sleep(0.5)
        if log and i > 0 and i % 20 == 0:
            log(f"  Attente ecran Microsoft « {step} » ({i}/{attempts})...")
    return False


async def fill_microsoft_visible_input(tab: Any, selector: str, value: str) -> bool:
    """
    Remplit un champ Microsoft visible (ignore moveOffScreen / hidden comme #i0118 sur l'ecran email).
    @param tab - Onglet nodriver.
    @param selector - Selecteurs CSS candidats.
    @param value - Valeur a poser.
    @returns True si un champ visible a ete rempli.
    """
    selector_json: str = json.dumps(selector)
    marker: str = "alyvo-ms-input"
    marker_json: str = json.dumps(marker)
    value_json: str = json.dumps(value)
    filled_by_js: bool = await js_eval_bool(
        tab,
        f"""
        () => {{
            {_microsoft_input_visible_js()}
            const input = Array.from(document.querySelectorAll({selector_json})).find(visible);
            if (!input) return false;
            input.focus();
            input.setAttribute('data-alyvo-ms-input', {marker_json});
            const nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype,
                'value',
            )?.set;
            if (nativeSetter) {{
                nativeSetter.call(input, '');
            }} else {{
                input.value = '';
            }}
            input.dispatchEvent(new InputEvent('input', {{ bubbles: true, inputType: 'deleteContentBackward' }}));
            if (nativeSetter) {{
                nativeSetter.call(input, {value_json});
            }} else {{
                input.value = {value_json};
            }}
            input.dispatchEvent(
                new InputEvent('input', {{
                    bubbles: true,
                    inputType: 'insertText',
                    data: {value_json},
                }}),
            );
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            input.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true, key: 'Tab' }}));
            return input.value === {value_json};
        }}
        """,
    )

    if filled_by_js:
        return True

    try:
        element: Any = await tab.select(f'input[data-alyvo-ms-input="{marker}"]', timeout=10)
        await element.clear_input()
        await element.send_keys(value)
        await tab.sleep(0.3)
    except Exception:
        for direct_selector in selector.split(","):
            candidate: str = direct_selector.strip()
            if not candidate:
                continue
            try:
                element = await tab.select(candidate, timeout=4)
                await element.clear_input()
                await element.send_keys(value)
                await tab.sleep(0.3)
                break
            except Exception:
                continue
        else:
            return False

    return await js_eval_bool(
        tab,
        f"""
        () => {{
            const input = document.querySelector('input[data-alyvo-ms-input={marker_json}]')
                || Array.from(document.querySelectorAll({selector_json})).find((el) => {{
                    if (!el) return false;
                    return el.value === {value_json};
                }});
            if (!input) return false;
            const ok = input.value === {value_json};
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return ok;
        }}
        """,
    )


async def fill_microsoft_login_field(tab: Any, step: str, value: str) -> bool:
    """
    Remplit email (#i0116) ou mot de passe (#passwordEntry / legacy) selon l'etape.
    @param tab - Onglet nodriver.
    @param step - username | password.
    @param value - Valeur a saisir.
    @returns True si le champ a ete rempli.
    """
    if step == "username":
        selectors: str = "#i0116, input[name='loginfmt'][type='email'], input[name='loginfmt']:not([type='hidden'])"
        direct_ids: tuple[str, ...] = ("#i0116",)
    else:
        selectors = (
            "#passwordEntry, form[data-testid='passwordEntryForm'] input[name='passwd'], "
            "#i0118:not(.moveOffScreen), input[name='passwd']:not(.moveOffScreen)"
        )
        direct_ids = ("#passwordEntry",)

    for selector in direct_ids:
        try:
            element: Any = await tab.select(selector, timeout=8)
            await element.clear_input()
            await element.send_keys(value)
            await tab.sleep(0.35)
            value_json: str = json.dumps(value)
            selector_json: str = json.dumps(selector)
            if await js_eval_bool(
                tab,
                f"""
                () => {{
                    const el = document.querySelector({selector_json});
                    return !!(el && el.value === {value_json});
                }}
                """,
            ):
                return True
        except Exception:
            continue

    return await fill_microsoft_visible_input(tab, selectors, value)


async def click_microsoft_primary(tab: Any) -> bool:
    """
    Clique le bouton principal Microsoft moderne (Fluent) ou legacy (#idSIButton9).
    @param tab - Onglet nodriver.
    @returns True si le clic a ete effectue.
    """
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            {_microsoft_input_visible_js()}
            const visibleButton = (el) => {{
                if (!el || el.disabled) return false;
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style.display !== 'none'
                    && style.visibility !== 'hidden'
                    && rect.width > 0
                    && rect.height > 0;
            }};
            const scopes = [
                document.querySelector('form[data-testid="passwordEntryForm"]'),
                document.querySelector('[data-viewid="1"]'),
                document.querySelector('.sign-in-box'),
                document,
            ].filter(Boolean);
            const selector = [
                'button[data-testid="primaryButton"]',
                '#idSIButton9',
                'input[type="submit"]',
                'button[type="submit"]',
            ].join(', ');
            for (const scope of scopes) {{
                const button = Array.from(scope.querySelectorAll(selector)).find(visibleButton);
                if (button) {{
                    button.scrollIntoView({{ block: 'center' }});
                    button.click();
                    return true;
                }}
            }}
            return false;
        }}
        """,
    )


async def fill_microsoft_login_if_needed(tab: Any, account: BrowardAccountInput, log: LogFn) -> None:
    """
    Renseigne l'email/mot de passe Outlook si la page Microsoft le demande.
    @param tab - Onglet nodriver.
    @param account - Compte courant.
    @param log - Journal stderr.
    """
    attempts: int = max(1, int(OUTLOOK_LOGIN_TIMEOUT_S / 1.0))
    for i in range(attempts):
        state: dict[str, Any] = await get_microsoft_login_state(tab)

        if state.get("outlook"):
            log("  Outlook est ouvert.")
            return

        step: str = str(state.get("step") or "other")
        host: str = str(state.get("host") or "")

        if step == "password":
            log(f"  Microsoft login : mot de passe Outlook ({host or 'login.live.com'})...")
            filled: bool = await fill_microsoft_login_field(tab, "password", account.password)
            if not filled:
                raise RuntimeError("Impossible de remplir le mot de passe Outlook (#passwordEntry).")
            if not await click_microsoft_primary(tab):
                raise RuntimeError("Bouton Suivant mot de passe Outlook introuvable.")
            await tab.sleep(3.0)
            continue

        if step == "username":
            log(f"  Microsoft login : email Outlook ({host or 'login.microsoftonline.com'})...")
            filled = await fill_microsoft_login_field(tab, "username", account.email)
            if not filled:
                raise RuntimeError("Impossible de remplir l'email Outlook (#i0116).")
            if not await click_microsoft_primary(tab):
                raise RuntimeError("Bouton Suivant email Outlook introuvable (#idSIButton9).")
            await wait_for_microsoft_login_step(tab, "password", 45.0, log)
            await tab.sleep(1.0)
            continue

        if state.get("staySignedIn") and state.get("next"):
            log("  Microsoft login : Rester connecte.")
            await click_microsoft_primary(tab)
            await tab.sleep(2.0)
            continue

        await tab.sleep(1.0)
        if i > 0 and i % 20 == 0:
            log(f"  Attente Outlook/login Microsoft ({i}/{attempts}) — {host}...")

    raise RuntimeError("Connexion Outlook non terminee dans le delai.")


async def open_outlook_sign_in_from_microsoft_page(tab: Any, log: LogFn) -> None:
    """
    Ouvre la page marketing Outlook puis suit le CTA Se connecter.
    @param tab - Onglet nodriver.
    @param log - Journal stderr.
    """
    log("  Ouverture page Microsoft Outlook...")
    await tab.get(OUTLOOK_ENTRY_URL)
    await tab.sleep(2.0)

    attempts: int = 45
    for i in range(attempts):
        link_data: dict[str, Any] = await js_eval_json(
            tab,
            """
            const links = Array.from(document.querySelectorAll('a[href]'));
            const match = links.find((link) => {
                const text = (link.textContent || '').trim().toLowerCase();
                const aria = (link.getAttribute('aria-label') || '').trim().toLowerCase();
                const href = link.href || '';
                return href.includes('LinkID=2125442')
                    || href.includes('linkid=2125442')
                    || (href.includes('go.microsoft.com/fwlink') && href.includes('deeplink=mail'))
                    || text === 'se connecter'
                    || aria.includes('connectez-vous à outlook');
            });
            return { href: match ? (match.href || match.getAttribute('href') || '') : '' };
            """,
        )

        href: str = str(link_data.get("href") or "").strip()
        if href:
            log("  CTA Outlook « Se connecter » trouve.")
            await tab.get(href.replace("&amp;", "&"))
            await tab.sleep(2.0)
            return

        await tab.sleep(1.0)
        if i > 0 and i % 10 == 0:
            log(f"  Attente CTA Outlook « Se connecter » ({i}/{attempts})...")

    raise RuntimeError("Lien Outlook « Se connecter » introuvable sur la page Microsoft.")


def _broward_outlook_mail_js() -> str:
    """JS partage : repérer / cliquer le mail Broward Set Password dans OWA."""
    subject_json: str = json.dumps(BROWARD_OUTLOOK_SUBJECT.lower())
    return f"""
            const subjectNeedle = {subject_json};
            const isBrowardRow = (el) => {{
                if (!el) return false;
                const aria = (el.getAttribute('aria-label') || '').toLowerCase();
                if (aria.includes(subjectNeedle) || aria.includes('broward college')) {{
                    return true;
                }}
                const subject = el.querySelector('span.TtcXM, span.JdFsz');
                const subjectText = ((subject && subject.textContent) || '').trim().toLowerCase();
                if (subjectText.includes(subjectNeedle)) {{
                    return true;
                }}
                const preview = (el.textContent || '').toLowerCase();
                return preview.includes(subjectNeedle) && preview.includes('broward');
            }};
            const findBrowardRow = () => {{
                const listRows = Array.from(
                    document.querySelectorAll('#MailList [role="option"], [role="listbox"] [role="option"]'),
                );
                let row = listRows.find(isBrowardRow);
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


async def wait_for_outlook_inbox(tab: Any, log: LogFn, timeout_s: float = 90.0) -> None:
    """
    Attend que la liste de messages Outlook (OWA) soit chargee.
    @param tab - Onglet nodriver.
    @param log - Journal stderr.
    @param timeout_s - Delai max.
    """
    attempts: int = max(1, int(timeout_s / 1.0))
    for i in range(attempts):
        ready: bool = await js_eval_bool(
            tab,
            """
            () => !!document.querySelector('#MailList, #topSearchInput, #owaBranding_container')
                && (document.body?.innerText || '').toLowerCase().includes('outlook');
            """,
        )
        if ready:
            log("  Boite de reception Outlook chargee.")
            await tab.sleep(1.5)
            return
        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente liste messages Outlook ({i}/{attempts})...")


async def extract_broward_set_password_href(tab: Any) -> str:
    """
    Extrait le lien ForgotPasswordInterstitial (corps du message ou page).
    @param tab - Onglet nodriver.
    @returns URL ou chaine vide.
    """
    href_data: dict[str, Any] = await js_eval_json(
        tab,
        """
            const links = Array.from(
                document.querySelectorAll(
                    'a[href*="ForgotPasswordInterstitial"], a[title*="ForgotPasswordInterstitial"]',
                ),
            );
            const link = links.find((el) => {
                const href = el.href || el.getAttribute('href') || el.getAttribute('title') || '';
                return href.includes('ForgotPasswordInterstitial');
            });
            if (!link) {
                return { href: '' };
            }
            const href = (link.href || link.getAttribute('href') || link.getAttribute('title') || '')
                .replace(/&amp;/g, '&');
            return { href };
        """,
    )
    return str(href_data.get("href") or "").strip()


async def click_broward_set_password_email(tab: Any, log: LogFn) -> bool:
    """
    Clique la ligne du mail Broward « Set Password » dans la liste OWA.
    @param tab - Onglet nodriver.
    @param log - Journal stderr.
    @returns True si un clic a ete effectue.
    """
    click_data: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        {_broward_outlook_mail_js()}
            const row = findBrowardRow();
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
            log(f"  Clic email Broward : {aria[:80]}...")
        else:
            log("  Clic email Broward « Set your Broward College Application Password ».")
        return True
    return False


async def retry_forgot_password_and_reopen_outlook(
    tab: Any,
    account: BrowardAccountInput,
    log: LogFn,
) -> None:
    """
    Relance une passe TX_ForgotPassword puis rouvre Outlook (mail Broward toujours absent).
    @param tab - Onglet nodriver.
    @param account - Compte courant.
    @param log - Journal stderr.
    """
    log(
        f"  Email Broward introuvable apres {OUTLOOK_MAIL_FORGOT_PASSWORD_RETRY_AT} tentatives — "
        f"nouvelle passe Request Password puis reconnexion Outlook...",
    )
    await submit_broward_forgot_password_pass(
        tab,
        account,
        log,
        pass_index=1,
        pass_total=FORGOT_PASSWORD_OUTLOOK_RETRY_PASSES,
    )
    await open_outlook_sign_in_from_microsoft_page(tab, log)
    await fill_microsoft_login_if_needed(tab, account, log)
    await wait_for_outlook_inbox(tab, log)


async def find_broward_set_password_link(
    tab: Any,
    account: BrowardAccountInput,
    log: LogFn,
) -> str:
    """
    Trouve le lien Set Password dans Outlook.
    @param tab - Onglet nodriver.
    @param account - Compte courant (relance Forgot Password si mail absent).
    @param log - Journal stderr.
    @returns URL Set Password.
    """
    await wait_for_outlook_inbox(tab, log)

    attempts: int = max(1, int(OUTLOOK_MAIL_TIMEOUT_S / 2.0))
    mail_clicked: bool = False
    outlook_mail_retry_done: bool = False
    for i in range(attempts):
        if not mail_clicked:
            mail_clicked = await click_broward_set_password_email(tab, log)
            if mail_clicked:
                await tab.sleep(2.5)

        if mail_clicked:
            href: str = await extract_broward_set_password_href(tab)
            if "ForgotPasswordInterstitial" in href:
                log("  Lien Set Password Broward trouve dans Outlook.")
                return href.replace("&amp;", "&")

        await tab.sleep(2.0)
        if i > 0 and i % 10 == 0:
            log(f"  Recherche email/lien Broward dans Outlook ({i}/{attempts})...")
            if i == OUTLOOK_MAIL_FORGOT_PASSWORD_RETRY_AT and not outlook_mail_retry_done:
                outlook_mail_retry_done = True
                await retry_forgot_password_and_reopen_outlook(tab, account, log)
                mail_clicked = False

    raise RuntimeError(f"Email Broward « {BROWARD_OUTLOOK_SUBJECT} » introuvable.")


async def open_outlook_and_extract_password_link(tab: Any, account: BrowardAccountInput, log: LogFn) -> str:
    """
    Ouvre Outlook et extrait le lien Set Password Broward.
    @param tab - Onglet nodriver.
    @param account - Compte courant.
    @param log - Journal stderr.
    @returns URL Set Password.
    """
    log("Etape 7/9 — Ouverture Outlook pour recuperer le lien Set Password...")
    await open_outlook_sign_in_from_microsoft_page(tab, log)
    await fill_microsoft_login_if_needed(tab, account, log)
    return await find_broward_set_password_link(tab, account, log)


async def read_broward_reset_password_state(tab: Any) -> dict[str, Any]:
    """
    Lit l'etat de la sequence Salesforce ForgotPasswordInterstitial / Save Password.
    @param tab - Onglet nodriver.
    @returns Dict url, hasInterstitial, hasPasswordForm, urlNoLongerExists, onPortal.
    """
    return await js_eval_json(
        tab,
        """
            const body = (document.body?.innerText || '').toLowerCase();
            const url = location.href || '';
            const resetButton = document.querySelector(
                'form#editPage input[name="save"][type="submit"], '
                + 'input[name="save"][value="Reset Password"], input[title="Reset Password"]',
            );
            const passwordInputs = Array.from(
                document.querySelectorAll(
                    'input[name*="theForm:psw"], input[id$=":psw"], '
                    + 'input[name*="theForm:j_id59:vpsw"], input[id$=":vpsw"]',
                ),
            );
            const visiblePasswordInputs = passwordInputs.filter((el) => {
                if (!el || el.disabled) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 4 && rect.height > 4;
            });
            return {
                url: url.slice(0, 240),
                hasInterstitial: !!resetButton
                    || body.includes('reset your password?')
                    || body.includes("let's get you set up with a new password"),
                hasPasswordForm: visiblePasswordInputs.length >= 2,
                passwordInputCount: visiblePasswordInputs.length,
                urlNoLongerExists: body.includes('url no longer exists'),
                onPortal: url.includes('TargetX_Base__Portal'),
                bodyText: body.slice(0, 240),
            };
        """,
    )


async def submit_broward_reset_password_interstitial(tab: Any, log: LogFn) -> bool:
    """
    Soumet la page intermediaire « Reset your password? » via submit natif.
    @param tab - Onglet nodriver.
    @param log - Journal stderr.
    @returns True si un submit/clic a ete effectue.
    """
    submitted: bool = await js_eval_bool(
        tab,
        """
        () => {
            const form = document.querySelector('form#editPage');
            const btn = document.querySelector(
                'form#editPage input[name="save"][type="submit"], '
                + 'input[name="save"][value="Reset Password"], input[title="Reset Password"]',
            );
            if (btn) {
                btn.scrollIntoView({ block: 'center' });
            }
            if (form) {
                if (typeof form.requestSubmit === 'function') {
                    form.requestSubmit(btn || undefined);
                } else if (btn) {
                    btn.click();
                } else {
                    form.submit();
                }
                return true;
            }
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        }
        """,
    )
    if submitted:
        log("  Soumission Reset Password (formulaire Salesforce natif).")
    return submitted


async def open_broward_password_form_from_link(tab: Any, link: str, log: LogFn) -> None:
    """
    Ouvre le lien Set Password et attend les champs New Password / Confirm.
    @param tab - Onglet nodriver.
    @param link - Lien ForgotPasswordInterstitial.
    @param log - Journal stderr.
    """
    await tab.get(link)
    await tab.sleep(2.0)

    submitted_interstitial: bool = False
    attempts: int = max(1, int(BROWARD_PASSWORD_TIMEOUT_S / 1.0))
    for i in range(attempts):
        state: dict[str, Any] = await read_broward_reset_password_state(tab)
        if state.get("urlNoLongerExists"):
            raise RuntimeError("Lien Reset Password Broward expire ou deja utilise (URL No Longer Exists).")
        if state.get("hasPasswordForm"):
            return
        if state.get("onPortal"):
            raise RuntimeError(
                "Reset Password Broward a redirige vers le portail sans afficher les champs mot de passe.",
            )
        if state.get("hasInterstitial") and not submitted_interstitial:
            if not await submit_broward_reset_password_interstitial(tab, log):
                raise RuntimeError("Bouton Reset Password visible mais impossible a soumettre.")
            submitted_interstitial = True
            await tab.sleep(3.0)
            continue

        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            url: str = str(state.get("url") or "")
            log(f"  Attente formulaire Save Password ({i}/{attempts}) — url={url[:90]!r}...")

    state = await read_broward_reset_password_state(tab)
    raise RuntimeError(
        "Formulaire Save Password Broward introuvable "
        f"(url={state.get('url', '')!r}, texte={state.get('bodyText', '')!r}).",
    )


async def save_broward_password_from_link(tab: Any, link: str, account: BrowardAccountInput, log: LogFn) -> None:
    """
    Ouvre le lien Broward et enregistre le mot de passe.
    @param tab - Onglet nodriver.
    @param link - Lien Set Password.
    @param account - Compte courant.
    @param log - Journal stderr.
    """
    log("Etape 8/9 — Ouverture lien Set Password Broward...")
    await open_broward_password_form_from_link(tab, link, log)

    log("Etape 9/9 — Definition du mot de passe Broward.")
    await fill_input_fast(tab, 'input[name*="theForm:psw"], input[id$=":psw"]', account.password)
    await fill_input_fast(tab, 'input[name*="theForm:j_id59:vpsw"], input[id$=":vpsw"]', account.password)

    if not await click_first_match(tab, 'a[id$="cpwbtn"], a.targetx-button'):
        raise RuntimeError("Bouton Save Password Broward introuvable.")

    attempts = max(1, int(BROWARD_PASSWORD_TIMEOUT_S / 1.0))
    for i in range(attempts):
        done: bool = await js_eval_bool(
            tab,
            """
            () => {
                const stillOnPasswordForm = !!document.querySelector(
                    'input[name*="theForm:psw"], input[id$=":psw"], input[name*="theForm:j_id59:vpsw"], input[id$=":vpsw"]',
                );
                const body = (document.body?.innerText || '').toLowerCase();
                if (body.includes('url no longer exists')) return false;
                return !stillOnPasswordForm
                    || body.includes('your password has been changed')
                    || body.includes('login')
                    || body.includes('log in');
            }
            """,
        )
        if done:
            log("  Mot de passe Broward enregistre.")
            return
        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente confirmation Save Password ({i}/{attempts})...")

    log("  Mot de passe Broward soumis (confirmation explicite non detectee).")


async def wait_for_url_contains(tab: Any, fragment: str, timeout_s: float, log: LogFn | None = None) -> bool:
    """
    Attend que l'URL de l'onglet contienne un fragment.
    @param tab - Onglet nodriver.
    @param fragment - Sous-chaine attendue dans l'URL.
    @param timeout_s - Delai max.
    @param log - Log optionnel.
    @returns True si trouve.
    """
    needle: str = fragment.lower()
    attempts: int = max(1, int(timeout_s / 1.0))
    for i in range(attempts):
        url: str = (tab.url or "").lower()
        if needle in url:
            return True
        await tab.sleep(1.0)
        if log and i > 0 and i % 15 == 0:
            log(f"  Attente URL « {fragment[:50]} » ({i}/{attempts})...")
    return False


def _targetx_new_application_select_js() -> str:
    """
    Utilitaires JS : cherche les <select> New Application (document principal + iframes).
    kinds : 'us_born' | 'term'
    """
    return """
            const optionText = (opt) => {
                const labelAttr = opt.getAttribute ? opt.getAttribute('label') : '';
                return (opt.label || labelAttr || opt.textContent || '').trim().toLowerCase();
            };
            const isPlaceholder = (text) =>
                !text || text === 'please select one' || text.startsWith('please select');

            const getSearchRoots = () => {
                const roots = [document];
                document.querySelectorAll('iframe').forEach((iframe) => {
                    try {
                        const doc = iframe.contentDocument;
                        if (doc) roots.push(doc);
                    } catch (e) {}
                });
                return roots;
            };

            const selectHasOption = (select, needle, partial) => {
                if (!select || !select.options) return false;
                const want = String(needle || '').toLowerCase();
                for (let i = 0; i < select.options.length; i++) {
                    const text = optionText(select.options[i]);
                    if (isPlaceholder(text)) continue;
                    if (partial ? text.includes(want) : text === want) return true;
                }
                return false;
            };

            const countRealOptions = (select) => {
                if (!select || !select.options) return 0;
                return Array.from(select.options).filter((o) => !isPlaceholder(optionText(o))).length;
            };

            const findUsBornSelectInRoot = (root) => {
                const patterns = [
                    'select[aria-label*="born"]',
                    'select[aria-label*="territory"]',
                    'select[aria-label*="Born"]',
                ];
                for (const pattern of patterns) {
                    const el = root.querySelector(pattern);
                    if (el && countRealOptions(el) > 0) return el;
                }
                const selects = root.querySelectorAll(
                    'form[ng-submit="handleSubmit()"] select.targetx-select-box, select.targetx-select-box',
                );
                for (const el of selects) {
                    if ((el.getAttribute('ng-model') || '') === 'deadline') continue;
                    if (selectHasOption(el, 'yes', false) || selectHasOption(el, 'no', false)) {
                        return el;
                    }
                }
                return null;
            };

            const findTermSelectInRoot = (root) => {
                let el = root.querySelector('select[ng-model="deadline"]');
                if (el) return el;
                const selects = root.querySelectorAll('select.targetx-select-box');
                for (const candidate of selects) {
                    if ((candidate.getAttribute('ng-model') || '') === 'deadline') {
                        return candidate;
                    }
                }
                return null;
            };

            const findNewApplicationSelect = (kind) => {
                const roots = getSearchRoots();
                for (const root of roots) {
                    const el = kind === 'term'
                        ? findTermSelectInRoot(root)
                        : findUsBornSelectInRoot(root);
                    if (el) return el;
                }
                return null;
            };

            const triggerSelectChange = (select) => {
                const win = select.ownerDocument && select.ownerDocument.defaultView
                    ? select.ownerDocument.defaultView
                    : window;
                select.dispatchEvent(new Event('input', { bubbles: true }));
                select.dispatchEvent(new Event('change', { bubbles: true }));
                try {
                    if (win.angular) {
                        const ngEl = win.angular.element(select);
                        ngEl.triggerHandler('change');
                        const scope = ngEl.scope();
                        if (scope && !scope.$$phase) scope.$applyAsync();
                    }
                } catch (e) {}
                try {
                    if (win.jQuery) win.jQuery(select).trigger('change');
                } catch (e) {}
            };
    """


async def read_targetx_new_application_select(tab: Any, select_kind: str) -> dict[str, Any]:
    """
    Lit l'etat d'un <select> New Application (us_born | term).
    @param tab - Onglet nodriver.
    @param select_kind - 'us_born' ou 'term'.
    @returns Dict found, selectedText, realOptionCount, reason.
    """
    kind_json: str = json.dumps(select_kind)
    return await js_eval_json(
        tab,
        f"""
        {_targetx_new_application_select_js()}
        const kind = {kind_json};
        const select = findNewApplicationSelect(kind);
        if (!select) {{
            return {{ found: false, reason: 'no-select', realOptionCount: 0 }};
        }}
        const opt = select.options[select.selectedIndex];
        const labelAttr = opt && opt.getAttribute ? opt.getAttribute('label') : '';
        const selectedText = opt
            ? (opt.label || labelAttr || opt.textContent || '').trim()
            : '';
        return {{
            found: true,
            selectedText,
            optionCount: select.options.length,
            realOptionCount: countRealOptions(select),
            ariaLabel: (select.getAttribute('aria-label') || '').slice(0, 80),
        }};
        """,
    )


async def wait_for_targetx_select_option(
    tab: Any,
    select_kind: str,
    option_label: str,
    log: LogFn,
    *,
    partial_match: bool = False,
    timeout_s: float = 60.0,
) -> bool:
    """
    Attend qu'une option soit presente dans le <select> New Application (page + iframes).
    @param tab - Onglet nodriver.
    @param select_kind - 'us_born' ou 'term'.
    @param option_label - Libelle recherche.
    @param log - Journal stderr.
    @param partial_match - Correspondance partielle sur le libelle.
    @param timeout_s - Delai max.
    @returns True si l'option est disponible.
    """
    kind_json: str = json.dumps(select_kind)
    label_json: str = json.dumps(option_label)
    partial_json: str = "true" if partial_match else "false"
    attempts: int = max(1, int(timeout_s / 0.5))
    for i in range(attempts):
        state: dict[str, Any] = await js_eval_json(
            tab,
            f"""
            {_targetx_new_application_select_js()}
            const kind = {kind_json};
            const select = findNewApplicationSelect(kind);
            if (!select) {{
                return {{ ready: false, reason: 'no-select', realOptionCount: 0 }};
            }}
            const want = {label_json}.toLowerCase();
            const partial = {partial_json};
            if (selectHasOption(select, want, partial)) {{
                return {{
                    ready: true,
                    realOptionCount: countRealOptions(select),
                    ariaLabel: (select.getAttribute('aria-label') || '').slice(0, 80),
                }};
            }}
            return {{
                ready: false,
                reason: 'no-match',
                realOptionCount: countRealOptions(select),
                optionCount: select.options.length,
            }};
            """,
        )
        if state.get("ready"):
            return True
        await tab.sleep(0.5)
        if i > 0 and i % 20 == 0:
            reason: str = str(state.get("reason") or "unknown")
            real_count: int = int(state.get("realOptionCount") or 0)
            aria: str = str(state.get("ariaLabel") or "").strip()
            detail: str = f", aria={aria!r}" if aria else ""
            log(
                f"  Attente option « {option_label} » ({select_kind}, {reason}, "
                f"{real_count} option(s) reelles{detail}, {i}/{attempts})...",
            )
    return False


async def wait_for_new_application_form_ready(tab: Any, log: LogFn, timeout_s: float = 90.0) -> bool:
    """
    Attend que le <select> naissance US soit present (document ou iframe) avec Yes/No.
    @param tab - Onglet nodriver.
    @param log - Journal stderr.
    @param timeout_s - Delai max.
    @returns True si le formulaire est interactif.
    """
    attempts: int = max(1, int(timeout_s / 0.5))
    for i in range(attempts):
        state: dict[str, Any] = await read_targetx_new_application_select(tab, "us_born")
        real_count: int = int(state.get("realOptionCount") or 0)
        if state.get("found") and real_count >= 2:
            aria: str = str(state.get("ariaLabel") or "").strip()
            if aria:
                log(f"  Select naissance US detecte ({real_count} options, {aria[:60]}...).")
            else:
                log(f"  Select naissance US detecte ({real_count} options).")
            return True
        await tab.sleep(0.5)
        if i > 0 and i % 20 == 0:
            reason: str = str(state.get("reason") or "loading")
            log(f"  Attente formulaire New Application ({reason}, {i}/{attempts})...")
    return False


async def select_targetx_new_application_option(
    tab: Any,
    select_kind: str,
    option_label: str,
    *,
    partial_match: bool = False,
) -> bool:
    """
    Choisit une option dans un <select> New Application (selectedIndex + Angular).
    @param tab - Onglet nodriver.
    @param select_kind - 'us_born' ou 'term'.
    @param option_label - Libelle de l'option.
    @param partial_match - Correspondance partielle.
    @returns True si selection reussie.
    """
    kind_json: str = json.dumps(select_kind)
    label_json: str = json.dumps(option_label)
    partial_json: str = "true" if partial_match else "false"
    result: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        {_targetx_new_application_select_js()}
        const kind = {kind_json};
        const select = findNewApplicationSelect(kind);
        if (!select) return {{ ok: false, reason: 'no-select' }};
        const want = {label_json}.toLowerCase();
        const partial = {partial_json};
        let targetIndex = -1;
        for (let i = 0; i < select.options.length; i++) {{
            const text = optionText(select.options[i]);
            if (isPlaceholder(text)) continue;
            if (partial ? text.includes(want) : text === want) {{
                targetIndex = i;
                break;
            }}
        }}
        if (targetIndex < 0) {{
            return {{
                ok: false,
                reason: 'no-match',
                realOptionCount: countRealOptions(select),
            }};
        }}
        select.selectedIndex = targetIndex;
        triggerSelectChange(select);
        const selected = select.options[select.selectedIndex];
        const labelAttr = selected && selected.getAttribute ? selected.getAttribute('label') : '';
        const selectedText = selected
            ? (selected.label || labelAttr || selected.textContent || '').trim()
            : '';
        return {{ ok: true, selectedText, selectedIndex: select.selectedIndex }};
        """,
    )
    return bool(result.get("ok"))


async def verify_targetx_new_application_option(
    tab: Any,
    select_kind: str,
    option_label: str,
    *,
    partial_match: bool = False,
) -> bool:
    """
    Verifie la selection sur un <select> New Application.
    @param tab - Onglet nodriver.
    @param select_kind - 'us_born' ou 'term'.
    @param option_label - Libelle attendu.
    @param partial_match - Correspondance partielle.
    @returns True si la selection correspond.
    """
    state: dict[str, Any] = await read_targetx_new_application_select(tab, select_kind)
    if not state.get("found"):
        return False
    selected: str = str(state.get("selectedText") or "").strip().lower()
    want: str = option_label.strip().lower()
    if not selected or selected.startswith("please select"):
        return False
    return want in selected if partial_match else selected == want


async def select_targetx_new_application_with_retries(
    tab: Any,
    select_kind: str,
    option_label: str,
    log: LogFn,
    *,
    partial_match: bool = False,
    label_for_log: str = "",
) -> bool:
    """
    Selection avec tentatives sur le <select> New Application (page + iframes).
    @param tab - Onglet nodriver.
    @param select_kind - 'us_born' ou 'term'.
    @param option_label - Libelle cible.
    @param log - Journal stderr.
    @param partial_match - Correspondance partielle.
    @param label_for_log - Libelle affiche dans les logs.
    @returns True si selection verifiee.
    """
    display: str = label_for_log or option_label
    for attempt in range(1, NEW_APPLICATION_SELECT_MAX_ATTEMPTS + 1):
        if await select_targetx_new_application_option(
            tab,
            select_kind,
            option_label,
            partial_match=partial_match,
        ) and await verify_targetx_new_application_option(
            tab,
            select_kind,
            option_label,
            partial_match=partial_match,
        ):
            return True
        await tab.sleep(1.0)
        if attempt < NEW_APPLICATION_SELECT_MAX_ATTEMPTS:
            log(f"  Retentative select « {display} » ({attempt}/{NEW_APPLICATION_SELECT_MAX_ATTEMPTS})...")
    return False


async def click_portal_start_new_application(tab: Any, log: LogFn) -> None:
    """
    Sur le portail TargetX, clique « Start a New Application ».
    @param tab - Onglet nodriver.
    @param log - Journal stderr.
    """
    selectors: tuple[str, ...] = (
        ".portal-block__button.new-app a",
        'a[href*="TargetX_App__NewApplication"] button',
        '.portal-block__button.new-app button[type="button"]',
        'a[href*="TargetX_App__NewApplication"]',
    )
    for selector in selectors:
        if await click_first_match(tab, selector):
            log("  Clic Start a New Application.")
            return
    raise RuntimeError("Bouton Start a New Application introuvable sur le portail.")


async def fill_new_application_key_questions(
    tab: Any,
    account: BrowardAccountInput,
    log: LogFn,
) -> None:
    """
    Page New Application : naissance US/territoire, terme, puis Start Application.
    @param tab - Onglet nodriver.
    @param account - Compte (born_in_us_territory, application_term).
    @param log - Journal stderr.
    """
    if not await wait_for_page_text(tab, "New Application", BROWARD_APPLICATION_START_TIMEOUT_S, log):
        raise RuntimeError("Page New Application introuvable.")

    log("  Attente chargement des listes (Angular / remoting)...")
    if not await wait_for_new_application_form_ready(tab, log, timeout_s=90.0):
        raise RuntimeError(
            "Formulaire New Application introuvable (select naissance US absent — "
            "verifiez URL / iframe).",
        )

    if not await wait_for_targetx_select_option(
        tab,
        "us_born",
        account.born_in_us_territory,
        log,
        partial_match=False,
        timeout_s=60.0,
    ):
        raise RuntimeError(
            f"Option « {account.born_in_us_territory} » absente du select naissance US "
            "(liste non chargee).",
        )

    if not await select_targetx_new_application_with_retries(
        tab,
        "us_born",
        account.born_in_us_territory,
        log,
        partial_match=False,
        label_for_log="naissance US/territoire",
    ):
        raise RuntimeError(
            f"Impossible de selectionner « {account.born_in_us_territory} » (naissance US/territoire).",
        )
    log(f"  Question naissance US : {account.born_in_us_territory}.")
    await tab.sleep(NEW_APPLICATION_SELECT_SETTLE_S)

    log(f"  Attente des termes contenant « {account.application_term} »...")
    if not await wait_for_targetx_select_option(
        tab,
        "term",
        account.application_term,
        log,
        partial_match=True,
        timeout_s=NEW_APPLICATION_TERM_OPTIONS_TIMEOUT_S,
    ):
        term_state: dict[str, Any] = await read_targetx_new_application_select(tab, "term")
        raise RuntimeError(
            f"Terme « {account.application_term} » introuvable "
            f"({term_state.get('realOptionCount', 0)} option(s) dans le select Term).",
        )

    if not await select_targetx_new_application_with_retries(
        tab,
        "term",
        account.application_term,
        log,
        partial_match=True,
        label_for_log="Term",
    ):
        raise RuntimeError(
            f"Impossible de selectionner le terme « {account.application_term} ».",
        )
    log(f"  Terme selectionne (match « {account.application_term} »).")
    await tab.sleep(NEW_APPLICATION_SELECT_SETTLE_S)

    attempts: int = max(1, int(BROWARD_APPLICATION_START_TIMEOUT_S / 1.0))
    for i in range(attempts):
        ready: bool = await js_eval_bool(
            tab,
            """
            () => {
                const btn = document.querySelector(
                    'input.targetx-application-action[type="submit"], input[value="Start Application"]',
                );
                return !!btn && !btn.disabled;
            }
            """,
        )
        if ready:
            break
        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente activation Start Application ({i}/{attempts})...")
    else:
        raise RuntimeError("Bouton Start Application reste desactive.")

    if not await click_first_match(
        tab,
        'input.targetx-application-action[type="submit"]:not([disabled]), '
        'input[value="Start Application"]:not([disabled])',
    ):
        submitted: bool = await js_eval_bool(
            tab,
            """
            () => {
                const form = document.querySelector('form[ng-submit="handleSubmit()"]');
                if (!form) return false;
                if (typeof form.requestSubmit === 'function') {
                    form.requestSubmit();
                    return true;
                }
                form.submit();
                return true;
            }
            """,
        )
        if not submitted:
            raise RuntimeError("Impossible de soumettre Start Application.")
    log("  Clic Start Application.")


async def complete_helpful_tips_section(tab: Any, log: LogFn) -> None:
    """
    Formulaire Apply2 : coche « I'm ready to begin » puis Continue sur Helpful Tips.
    @param tab - Onglet nodriver.
    @param log - Journal stderr.
    """
    if not await wait_for_page_text(tab, "Helpful Tips", BROWARD_APPLICATION_START_TIMEOUT_S, log):
        raise RuntimeError("Section Helpful Tips introuvable.")

    radio_selectors: tuple[str, ...] = (
        'input#m0000-TargetX_SRMb__Application__c-BC_Helpful_Tips_Acknowledgement__c_true',
        'input[name*="BC_Helpful_Tips_Acknowledgement"][value="true"]',
        'label[aria-label="I\'m ready to begin"] input[type="radio"]',
    )
    checked: bool = False
    for selector in radio_selectors:
        if await click_first_match(tab, selector):
            checked = True
            break
    if not checked:
        checked = await js_eval_bool(
            tab,
            """
            () => {
                const radios = document.querySelectorAll(
                    'input[name*="BC_Helpful_Tips_Acknowledgement"]',
                );
                for (const input of radios) {
                    if (input.value === true || input.value === 'true') {
                        input.click();
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        return true;
                    }
                }
                const label = Array.from(document.querySelectorAll('label')).find(
                    (el) => (el.getAttribute('aria-label') || '').toLowerCase().includes('ready to begin'),
                );
                if (label) {
                    label.click();
                    return true;
                }
                return false;
            }
            """,
        )
    if not checked:
        raise RuntimeError("Radio « I'm ready to begin » introuvable.")
    log("  Option I'm ready to begin selectionnee.")
    await tab.sleep(0.5)

    continue_clicked: bool = await js_eval_bool(
        tab,
        """
        () => {
            const section = document.querySelector('[id*="Helpful Tips"]');
            const root = section || document;
            const buttons = root.querySelectorAll('button.targetx-button');
            for (const btn of buttons) {
                const text = (btn.textContent || '').trim().toLowerCase();
                if (text === 'continue' && !btn.disabled) {
                    btn.scrollIntoView({ block: 'center' });
                    btn.click();
                    return true;
                }
            }
            return false;
        }
        """,
    )
    if not continue_clicked:
        if not await click_first_match(tab, "#p0_Helpful\\ Tips0 button.targetx-button"):
            raise RuntimeError("Bouton Continue (Helpful Tips) introuvable.")
    log("  Clic Continue (Helpful Tips).")


def _apply2_field_js() -> str:
    """Utilitaires JS pour les champs Angular TargetX Apply2."""
    return """
            const visible = (el) => {
                if (!el || el.disabled) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 2 && rect.height > 2;
            };
            const norm = (text) => String(text || '').trim().toLowerCase();
            const trigger = (el) => {
                const win = el.ownerDocument?.defaultView || window;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
                try {
                    if (win.angular) {
                        const ngEl = win.angular.element(el);
                        ngEl.triggerHandler('input');
                        ngEl.triggerHandler('change');
                        ngEl.triggerHandler('blur');
                        const scope = ngEl.scope();
                        if (scope && !scope.$$phase) scope.$applyAsync();
                    }
                } catch (e) {}
                try {
                    if (win.jQuery) win.jQuery(el).trigger('input').trigger('change').trigger('blur');
                } catch (e) {}
            };
            const findByNamePart = (selector, namePart) => {
                const needle = norm(namePart);
                return Array.from(document.querySelectorAll(selector)).find((el) => {
                    const id = norm(el.id);
                    const name = norm(el.getAttribute('name'));
                    const placeholder = norm(el.getAttribute('placeholder'));
                    return id.includes(needle) || name.includes(needle) || placeholder.includes(needle);
                });
            };
            const findAutocompleteRoot = (namePart) => {
                const needle = norm(namePart);
                return Array.from(document.querySelectorAll('autocomplete-secure')).find((el) => {
                    if (!visible(el)) return false;
                    const attrs = [el.getAttribute('name'), el.getAttribute('label'), el.getAttribute('htmlname')];
                    if (attrs.some((value) => norm(value).includes(needle))) return true;
                    return Array.from(el.querySelectorAll('[name], [id]')).some((node) => {
                        const id = norm(node.id);
                        const name = norm(node.getAttribute('name'));
                        return id.includes(needle) || name.includes(needle);
                    });
                });
            };
            const autocompleteSelectedText = (root) => {
                const matchText = root.querySelector('.ui-select-match-text');
                if (!matchText || matchText.classList.contains('ng-hide')) return '';
                return norm(matchText.textContent);
            };
            const openAutocompleteSearch = (root) => {
                const toggle = root.querySelector('.ui-select-toggle, .ui-select-focusser');
                if (toggle) {
                    toggle.scrollIntoView({ block: 'center' });
                    toggle.click();
                }
                const input = root.querySelector('input.ui-select-search');
                if (input) input.focus();
                return input;
            };
            const optionText = (option) =>
                norm(option.label || option.getAttribute?.('label') || option.textContent || '');
            const setSelectOption = (select, wanted, partial) => {
                const want = norm(wanted);
                if (!select) return false;
                const options = Array.from(select.options);
                let index = options.findIndex((option) => {
                    const text = optionText(option);
                    const value = norm(option.value).replace(/^string:/, '');
                    if (!text || text.startsWith('please select')) return false;
                    return partial ? text.includes(want) || value.includes(want) : text === want || value === want;
                });
                if (index < 0) return false;
                select.selectedIndex = index;
                trigger(select);
                return true;
            };
    """


async def fill_apply2_text_field(tab: Any, name_part: str, value: str) -> bool:
    """
    Remplit un champ texte Apply2 par fragment id/name/placeholder.
    @param tab - Onglet nodriver.
    @param name_part - Fragment stable du champ.
    @param value - Valeur.
    @returns True si rempli.
    """
    name_json: str = json.dumps(name_part)
    value_json: str = json.dumps(value)
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            {_apply2_field_js()}
            const input = findByNamePart('input:not([type="hidden"]), textarea', {name_json});
            if (!input) return false;
            input.scrollIntoView({{ block: 'center' }});
            input.focus();
            input.value = {value_json};
            trigger(input);
            return true;
        }}
        """,
    )


async def fill_apply2_hidden_or_text_field(tab: Any, name_part: str, value: str) -> bool:
    """
    Remplit un champ visible ou hidden Apply2 (utile adresse widget).
    @param tab - Onglet nodriver.
    @param name_part - Fragment stable.
    @param value - Valeur.
    @returns True si rempli.
    """
    name_json: str = json.dumps(name_part)
    value_json: str = json.dumps(value)
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            {_apply2_field_js()}
            const input = findByNamePart('input, textarea', {name_json});
            if (!input) return false;
            input.value = {value_json};
            trigger(input);
            return true;
        }}
        """,
    )


async def select_apply2_option(
    tab: Any,
    name_part: str,
    option_label: str,
    *,
    partial_match: bool = False,
) -> bool:
    """
    Selectionne une option d'un select Apply2 par fragment id/name/placeholder.
    @param tab - Onglet nodriver.
    @param name_part - Fragment stable du select.
    @param option_label - Libelle ou valeur option.
    @param partial_match - Correspondance partielle.
    @returns True si selectionne.
    """
    name_json: str = json.dumps(name_part)
    label_json: str = json.dumps(option_label)
    partial_json: str = "true" if partial_match else "false"
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            {_apply2_field_js()}
            const select = findByNamePart('select', {name_json});
            if (!select) return false;
            select.scrollIntoView({{ block: 'center' }});
            return setSelectOption(select, {label_json}, {partial_json});
        }}
        """,
    )


async def click_apply2_radio(tab: Any, name_part: str, value: str) -> bool:
    """
    Clique un radio Apply2 par name/id partiel et valeur.
    @param tab - Onglet nodriver.
    @param name_part - Fragment stable du groupe.
    @param value - Valeur cible (Yes/No/true...).
    @returns True si clique.
    """
    name_json: str = json.dumps(name_part)
    value_json: str = json.dumps(value.lower())
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            {_apply2_field_js()}
            const needle = norm({name_json});
            const want = norm({value_json});
            const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
            const radio = radios.find((el) => {{
                const id = norm(el.id);
                const name = norm(el.name);
                const val = norm(el.value);
                return (id.includes(needle) || name.includes(needle)) && val === want;
            }});
            if (!radio) return false;
            radio.scrollIntoView({{ block: 'center' }});
            radio.click();
            trigger(radio);
            return true;
        }}
        """,
    )


async def click_apply2_checkbox(tab: Any, name_part: str, checked: bool = True) -> bool:
    """
    Coche/decoche une checkbox Apply2 par fragment id/name.
    @param tab - Onglet nodriver.
    @param name_part - Fragment stable.
    @param checked - Etat souhaite.
    @returns True si champ trouve.
    """
    name_json: str = json.dumps(name_part)
    checked_json: str = "true" if checked else "false"
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            {_apply2_field_js()}
            const checkbox = findByNamePart('input[type="checkbox"]', {name_json});
            if (!checkbox) return false;
            checkbox.scrollIntoView({{ block: 'center' }});
            checkbox.checked = {checked_json};
            trigger(checkbox);
            return true;
        }}
        """,
    )


async def click_apply2_multicheckbox_option(tab: Any, name_part: str, option_text: str) -> bool:
    """
    Coche une option multicheckbox par id/name contenant name_part + label.
    @param tab - Onglet nodriver.
    @param name_part - Fragment stable du champ.
    @param option_text - Texte option.
    @returns True si coche.
    """
    name_json: str = json.dumps(name_part)
    option_json: str = json.dumps(option_text.lower())
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            {_apply2_field_js()}
            const needle = norm({name_json});
            const want = norm({option_json});
            const boxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
            const checkbox = boxes.find((el) => {{
                const id = norm(el.id);
                const name = norm(el.name);
                const label = norm(el.closest('label')?.textContent || '');
                return (id.includes(needle) || name.includes(needle)) && label.includes(want);
            }});
            if (!checkbox) return false;
            checkbox.scrollIntoView({{ block: 'center' }});
            checkbox.checked = true;
            trigger(checkbox);
            return true;
        }}
        """,
    )


async def select_apply2_date_dropdown(tab: Any, name_part: str, iso_date: str) -> bool:
    """
    Selectionne une date dans un composant date-dropdown Apply2 (jour/mois/annee).
    @param tab - Onglet nodriver.
    @param name_part - Fragment stable du composant.
    @param iso_date - Date YYYY-MM-DD.
    @returns True si les 3 selects sont renseignes.
    """
    name_json: str = json.dumps(name_part)
    date_json: str = json.dumps(iso_date[:10])
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            {_apply2_field_js()}
            const [yearText, monthText, dayText] = {date_json}.split('-');
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const monthName = monthNames[Math.max(0, Number(monthText) - 1)];
            const needle = norm({name_json});
            const root = Array.from(document.querySelectorAll('date-dropdown')).find((el) => {{
                const name = norm(el.getAttribute('name'));
                const text = norm(el.textContent);
                return name.includes(needle) || text.includes(needle);
            }});
            if (!root) return false;
            const selects = Array.from(root.querySelectorAll('select'));
            if (selects.length < 3) return false;
            const daySelect = selects.find((select) => norm(select.closest('label')?.getAttribute('aria-label')).includes('day'))
                || selects[0];
            const monthSelect = selects.find((select) => norm(select.closest('label')?.getAttribute('aria-label')).includes('month'))
                || selects[1];
            const yearSelect = selects.find((select) => norm(select.closest('label')?.getAttribute('aria-label')).includes('year'))
                || selects[2];
            const dayOk = setSelectOption(daySelect, String(Number(dayText)), false);
            const monthOk = setSelectOption(monthSelect, monthName, false);
            const yearOk = setSelectOption(yearSelect, yearText, false);
            root.scrollIntoView({{ block: 'center' }});
            return dayOk && monthOk && yearOk;
        }}
        """,
    )


async def ensure_apply2_autocomplete_value(tab: Any, name_part: str, expected_text: str) -> bool:
    """
    Verifie ou selectionne une valeur ui-select autocomplete Apply2.
    @param tab - Onglet nodriver.
    @param name_part - Fragment stable du champ autocomplete.
    @param expected_text - Texte attendu / recherche.
    @returns True si la valeur attendue est affichee ou selectionnee.
    """
    name_json: str = json.dumps(name_part)
    expected_json: str = json.dumps(expected_text)

    already_selected: bool = await js_eval_bool(
        tab,
        f"""
        () => {{
            {_apply2_field_js()}
            const root = findAutocompleteRoot({name_json});
            if (!root) return false;
            return autocompleteSelectedText(root).includes(norm({expected_json}));
        }}
        """,
    )
    if already_selected:
        return True

    opened: bool = await js_eval_bool(
        tab,
        f"""
        () => {{
            {_apply2_field_js()}
            const root = findAutocompleteRoot({name_json});
            if (!root) return false;
            const input = openAutocompleteSearch(root);
            return !!input;
        }}
        """,
    )
    if not opened:
        return False

    await tab.sleep(0.4)

    typed: bool = await js_eval_bool(
        tab,
        f"""
        () => {{
            {_apply2_field_js()}
            const root = findAutocompleteRoot({name_json});
            if (!root) return false;
            const input = root.querySelector('input.ui-select-search');
            if (!input) return false;
            input.focus();
            input.value = {expected_json};
            trigger(input);
            return true;
        }}
        """,
    )
    if not typed:
        return False

    await tab.sleep(2.0)
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            {_apply2_field_js()}
            const expected = norm({expected_json});
            const root = findAutocompleteRoot({name_json});
            const options = Array.from(
                document.querySelectorAll('.ui-select-choices-row, .ui-select-choices-row-inner, .ui-select-choices-row > a'),
            );
            const option = options.find((el) => visible(el) && norm(el.textContent).includes(expected))
                || options.find((el) => visible(el) && norm(el.textContent).length > 0);
            if (option) {{
                option.scrollIntoView({{ block: 'center' }});
                option.click();
            }}
            if (root && autocompleteSelectedText(root).includes(expected)) return true;
            return Array.from(document.querySelectorAll('autocomplete-secure')).some(
                (item) => autocompleteSelectedText(item).includes(expected),
            );
        }}
        """,
    )


async def click_apply2_review_application(tab: Any, log: LogFn) -> None:
    """
    Clique le bouton Review Application / Save and Review Application.
    @param tab - Onglet nodriver.
    @param log - Journal stderr.
    """
    attempts: int = max(1, int(BROWARD_APPLICATION_START_TIMEOUT_S / 1.0))
    for i in range(attempts):
        clicked: bool = await js_eval_bool(
            tab,
            """
            () => {
                const buttons = Array.from(document.querySelectorAll('button.targetx-button'));
                const btn = buttons.find((el) => {
                    const text = (el.textContent || '').trim().toLowerCase();
                    return !el.disabled && (
                        text.includes('review application')
                        || text.includes('save and review application')
                    );
                });
                if (!btn) return false;
                btn.scrollIntoView({ block: 'center' });
                btn.click();
                return true;
            }
            """,
        )
        if clicked:
            log("  Clic Review Application.")
            return
        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            invalid_state: dict[str, Any] = await js_eval_json(
                tab,
                """
                    const invalid = Array.from(document.querySelectorAll('.ng-invalid-required'))
                        .filter((el) => el.offsetParent !== null)
                        .slice(0, 8)
                        .map((el) => ({
                            id: el.id || '',
                            name: el.getAttribute('name') || '',
                            placeholder: el.getAttribute('placeholder') || '',
                        }));
                    return { invalidCount: invalid.length, invalid };
                """,
            )
            log(
                f"  Attente bouton Review Application ({i}/{attempts}) "
                f"— invalid visibles={invalid_state.get('invalidCount', 0)}...",
            )
    raise RuntimeError("Bouton Review Application introuvable ou formulaire encore invalide.")


async def submit_apply2_review_application(tab: Any, log: LogFn) -> None:
    """
    Sur la vue Review, clique « Submit Your Application ».
    @param tab - Onglet nodriver.
    @param log - Journal stderr.
    """
    attempts: int = max(1, int(BROWARD_APPLICATION_START_TIMEOUT_S / 1.0))
    for i in range(attempts):
        clicked: bool = await js_eval_bool(
            tab,
            """
            () => {
                const body = (document.body?.innerText || '').toLowerCase();
                const buttons = Array.from(document.querySelectorAll('button.targetx-button, button'));
                const btn = buttons.find((el) => {
                    const text = (el.textContent || '').trim().toLowerCase();
                    return !el.disabled && text.includes('submit your application');
                });
                if (!btn) return false;
                btn.scrollIntoView({ block: 'center' });
                btn.click();
                return true;
            }
            """,
        )
        if clicked:
            log("  Clic Submit Your Application.")
            await tab.sleep(3.0)
            return
        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente bouton Submit Your Application ({i}/{attempts})...")
    raise RuntimeError("Bouton Submit Your Application introuvable ou desactive.")


async def read_verify_submit_dom_state(tab: Any) -> dict[str, Any]:
    """
    Etat Verify & Submit via le DOM (aligne sur l'affichage visuel du bouton).
    @param tab - Onglet nodriver.
    @return - Certificat, signature, bouton et indicateurs Angular.
    """
    selector_json: str = json.dumps(VERIFY_SUBMIT_SELECTOR)
    return await js_eval_json(
        tab,
        f"""
        () => {{
            const checkbox = document.querySelector('#TargetX_SRMb__True_and_Correct__c');
            const signatureInput = document.querySelector('#TargetX_SRMb__Electronic_Signature__c');
            const btn = document.querySelector({selector_json});
            const certChecked = !!(checkbox && checkbox.checked);
            const hasSignature = !!(signatureInput && (signatureInput.value || '').trim());
            const btnFound = !!btn;
            const btnDisabled = btn
                ? !!btn.disabled
                    || btn.hasAttribute('disabled')
                    || btn.classList.contains('targetx-button-disabled')
                : true;
            let saving = false;
            let scopeReady = false;
            let scopeCert = false;
            let scopeSignature = false;
            try {{
                const root = document.querySelector('[ng-controller="submitController"]');
                const scope = root && window.angular ? angular.element(root).scope() : null;
                if (scope) {{
                    saving = !!scope.saving;
                    scopeReady = !!(scope.application && scope.application.Id);
                    if (scope.application) {{
                        scopeCert = !!scope.application.TargetX_SRMb__True_and_Correct__c;
                        scopeSignature = !!(
                            scope.application.TargetX_SRMb__Electronic_Signature__c || ''
                        ).trim();
                    }}
                }}
            }} catch (e) {{}}
            const formReady = (certChecked || scopeCert) && (hasSignature || scopeSignature);
            return {{
                certChecked,
                hasSignature,
                scopeCert,
                scopeSignature,
                btnFound,
                btnDisabled,
                saving,
                scopeReady,
                formReady,
                domReady: btnFound && !btnDisabled && formReady,
            }};
        }}
        """,
    )


async def sync_verify_submit_angular_scope(tab: Any, signature: str) -> bool:
    """
    Synchronise le scope Angular sans basculer la checkbox par erreur.
    @param tab - Onglet nodriver.
    @param signature - Signature electronique.
    @return - True si le scope est pret pour la soumission.
    """
    signature_json: str = json.dumps(signature)
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            const root = document.querySelector('[ng-controller="submitController"]');
            const checkbox = document.querySelector('#TargetX_SRMb__True_and_Correct__c');
            const signatureInput = document.querySelector('#TargetX_SRMb__Electronic_Signature__c');
            if (!root || !checkbox || !signatureInput || !window.angular) return false;

            const scope = angular.element(root).scope();
            if (!scope || !scope.application) return false;

            if (scope.saving) {{
                scope.saving = false;
            }}

            scope.application.TargetX_SRMb__True_and_Correct__c = true;
            scope.application.TargetX_SRMb__Electronic_Signature__c = {signature_json};

            if (!checkbox.checked) {{
                checkbox.checked = true;
            }}
            signatureInput.value = {signature_json};
            signatureInput.classList.add('preventLabelOverlap');

            const trigger = (el, events) => {{
                events.forEach((type) => el.dispatchEvent(new Event(type, {{ bubbles: true }})));
                try {{
                    const ngEl = angular.element(el);
                    events.forEach((type) => ngEl.triggerHandler(type));
                }} catch (e) {{}}
            }};
            trigger(checkbox, ['change', 'input']);
            trigger(signatureInput, ['input', 'change', 'blur']);

            try {{
                if (!scope.$$phase) scope.$apply();
            }} catch (e) {{
                try {{ scope.$applyAsync(); }} catch (ignored) {{}}
            }}

            return !!scope.application.TargetX_SRMb__True_and_Correct__c
                && !!(scope.application.TargetX_SRMb__Electronic_Signature__c || '').trim();
        }}
        """,
    )


async def invoke_verify_submit_remoting(tab: Any, signature: str) -> bool:
    """
    Soumet via Visualforce remoting (submitApp), sans passer par le bouton.
    @param tab - Onglet nodriver.
    @param signature - Signature electronique.
    @return - True si l'appel remoting a ete lance.
    """
    signature_json: str = json.dumps(signature)
    return await js_eval_bool(
        tab,
        f"""
        () => {{
            const root = document.querySelector('[ng-controller="submitController"]');
            if (!root || !window.angular || typeof Visualforce === 'undefined') return false;
            const scope = angular.element(root).scope();
            if (!scope || !scope.application || !scope.application.Id) return false;
            if (typeof sObject === 'undefined' || typeof sObject.setOptions !== 'function') return false;

            scope.application.TargetX_SRMb__True_and_Correct__c = true;
            scope.application.TargetX_SRMb__Electronic_Signature__c = {signature_json};
            scope.saving = false;

            const ns = scope.ns && scope.ns.full ? scope.ns.full : 'TargetX_App__';
            const pid = scope.application[ns + 'Application_Process__c'];
            if (!pid) return false;

            const app = {{
                Id: scope.application.Id,
                TargetX_SRMb__Electronic_Signature__c: scope.application.TargetX_SRMb__Electronic_Signature__c,
                TargetX_SRMb__True_and_Correct__c: scope.application.TargetX_SRMb__True_and_Correct__c,
            }};
            for (const key in app) {{
                if (app[key] && typeof app[key] === 'object') {{
                    delete app[key];
                }}
            }}

            scope.saving = true;
            const options = sObject.setOptions();
            Visualforce.remoting.Manager.invokeAction(
                'TargetX_App.ApplicationSubmitController.submitApp',
                pid,
                app,
                options,
                function(result, event) {{
                    scope.saving = false;
                    if (event.status) {{
                        const supplemental = scope.supplemental || {{ active: false }};
                        const enablePayment = scope.application[ns + 'Application_Process__r']
                            && scope.application[ns + 'Application_Process__r'][ns + 'EnablePaymentAfterSubmit__c'];
                        const payAmount = scope.application[ns + 'Application_Process__r']
                            && scope.application[ns + 'Application_Process__r'][ns + 'Amount__c'];
                        const discountAmount = scope.application[ns + 'Discount__c'];
                        const hasCost = !!payAmount
                            && !(discountAmount != null && payAmount - discountAmount <= 0);
                        if (!enablePayment || !hasCost || supplemental.active) {{
                            scope.submitted = true;
                        }}
                    }}
                    try {{
                        if (!scope.$$phase) scope.$apply();
                    }} catch (e) {{
                        try {{ scope.$applyAsync(); }} catch (ignored) {{}}
                    }}
                }},
                {{ escape: options.escape }},
            );
            return true;
        }}
        """,
    )


async def invoke_verify_submit_save(tab: Any, signature: str) -> bool:
    """
    Declenche save() Angular apres synchronisation du scope.
    @param tab - Onglet nodriver.
    @param signature - Signature electronique.
    @return - True si save() a ete appele.
    """
    if not await sync_verify_submit_angular_scope(tab, signature):
        return False
    return await js_eval_bool(
        tab,
        """
        () => {
            const root = document.querySelector('[ng-controller="submitController"]');
            if (!root || !window.angular) return false;
            const scope = angular.element(root).scope();
            if (!scope || typeof scope.save !== 'function') return false;
            if (scope.saving) {
                scope.saving = false;
            }
            try {
                if (scope.$$phase) {
                    scope.save();
                } else {
                    scope.$apply(() => scope.save());
                }
                return true;
            } catch (e) {
                return false;
            }
        }
        """,
    )


async def _wait_verify_submit_save_acknowledged(tab: Any, timeout_s: float = 2.5) -> bool:
    """
    Apres un clic, verifie que ng-click="save()" a bien demarre la soumission Angular.
    @param tab - Onglet nodriver.
    @param timeout_s - Duree max d'attente d'un signal d'accuse.
    @return - True si scope.saving / scope.submitted / ecran de succes detecte.
    """
    deadline_steps: int = max(1, int(timeout_s / 0.1))
    for _ in range(deadline_steps):
        await tab.sleep(0.1)
        acked: bool = await js_eval_bool(
            tab,
            """
            () => {
                const body = (document.body?.innerText || '').toLowerCase();
                if (
                    body.includes('thank you for submitting your application')
                    || body.includes('welcome to seahawk nation')
                    || body.includes('return home')
                ) {
                    return true;
                }
                try {
                    const root = document.querySelector('[ng-controller="submitController"]');
                    const scope = root && window.angular ? angular.element(root).scope() : null;
                    if (!scope) return false;
                    return !!scope.saving || !!scope.submitted;
                } catch (e) {
                    return false;
                }
            }
            """,
        )
        if acked:
            return True
    return False


async def _dump_verify_submit_diagnostic(tab: Any, log: LogFn) -> None:
    """
    Logge l'etat complet (scope, bouton, form valid) pour debugger un clic muet.
    """
    state: dict[str, Any] = await js_eval_json(
        tab,
        """
        () => {
            const out = { url: location.href };
            const root = document.querySelector('[ng-controller="submitController"]');
            out.rootFound = !!root;
            if (!root || !window.angular) return out;
            const scope = angular.element(root).scope();
            if (!scope) return out;
            const ns = scope.ns && scope.ns.full ? scope.ns.full : 'TargetX_App__';
            out.saving = !!scope.saving;
            out.submitted = !!scope.submitted;
            out.applicationId = scope.application && scope.application.Id || null;
            out.signature = scope.application
                ? (scope.application.TargetX_SRMb__Electronic_Signature__c || null) : null;
            out.trueAndCorrect = scope.application
                ? !!scope.application.TargetX_SRMb__True_and_Correct__c : null;
            out.percentComplete = scope.application
                ? scope.application[ns + 'Percent_Complete__c'] : null;
            out.processId = scope.application
                ? scope.application[ns + 'Application_Process__c'] : null;
            try {
                const form = scope.applicationForm
                    || (scope.$ctrl && scope.$ctrl.applicationForm)
                    || null;
                if (form) {
                    out.formValid = !!form.$valid;
                    out.formInvalid = !!form.$invalid;
                    out.formErrors = Object.keys(form.$error || {});
                }
            } catch (e) {}
            const btns = Array.from(
                document.querySelectorAll('input.targetx-button')
            ).map((el) => ({
                value: el.value || '',
                disabled: !!el.disabled,
                hasDisabledAttr: el.hasAttribute('disabled'),
                visualDisabled: el.classList.contains('targetx-button-disabled'),
                rect: (() => { const r = el.getBoundingClientRect();
                    return [Math.round(r.left), Math.round(r.top),
                            Math.round(r.width), Math.round(r.height)]; })(),
            }));
            out.buttons = btns;
            out.sObjectAvailable = typeof sObject !== 'undefined';
            out.visualforceAvailable = typeof Visualforce !== 'undefined';
            return out;
        }
        """,
    )
    log(f"  [debug Verify & Submit] {json.dumps(state, default=str)[:1200]}")


async def click_verify_submit_button(tab: Any, log: LogFn, signature: str) -> bool:
    """
    Clique Verify & Submit en cascade de strategies, ne retourne True que si
    `ng-click="save()"` a reellement demarre (scope.saving / scope.submitted / texte succes).

    Strategies, dans l'ordre :
      A. CDP raw : Input.dispatchMouseEvent (mouseMoved -> mousePressed -> mouseReleased)
      B. element.mouse_click (nodriver, CDP, centre recalcule)
      C. focus + Enter via Input.dispatchKeyEvent (declenche click natif sur <input type=submit>)
      D. angular.element(btn).triggerHandler('click') (bypass DOM, fire ng-click direct)

    Si tout echoue, dump diagnostique pour analyser pourquoi save() n'est pas appele,
    et retourne False — l'orchestrateur enchaine sur scope.save() puis remoting.

    @param tab - Onglet nodriver.
    @param log - Journal stderr.
    @param signature - Signature electronique.
    @return - True si la soumission Angular a ete confirmee, False sinon.
    """
    if not await sync_verify_submit_angular_scope(tab, signature):
        return False

    marker: str = VERIFY_SUBMIT_MARKER
    marker_json: str = json.dumps(marker)

    # 1) Localise le bouton VISIBLE (en cas de matches multiples) + tag + reset saving.
    tagged: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        () => {{
            const candidates = Array.from(document.querySelectorAll(
                'input.targetx-button[value*="Verify"], '
                + 'input.targetx-button[value*="Submit"], '
                + '.targetx-card-buttons input.targetx-button:not(.secondary)'
            ));
            const btn = candidates.find((el) => {{
                const r = el.getBoundingClientRect();
                return r.width > 4 && r.height > 4;
            }});
            if (!btn) {{
                return {{ ok: false, reason: 'noVisibleButton', total: candidates.length }};
            }}
            if (btn.disabled || btn.hasAttribute('disabled')) {{
                return {{ ok: false, reason: 'disabledAttr',
                          classes: btn.className, value: btn.value || '' }};
            }}
            btn.setAttribute('data-alyvo-verify-submit', {marker_json});
            btn.scrollIntoView({{ block: 'center', behavior: 'instant' }});
            try {{
                const root = document.querySelector('[ng-controller="submitController"]');
                if (root && window.angular) {{
                    const scope = angular.element(root).scope();
                    if (scope && scope.saving) {{
                        scope.saving = false;
                        if (!scope.$$phase) scope.$apply();
                    }}
                }}
            }} catch (e) {{}}
            return {{ ok: true, value: btn.value || '',
                      visualDisabled: btn.classList.contains('targetx-button-disabled') }};
        }}
        """,
    )
    if not tagged.get("ok"):
        log(f"  Verify & Submit non cliquable: {tagged}.")
        return False

    label: str = str(tagged.get("value") or "Verify & Submit")
    if tagged.get("visualDisabled"):
        log(f"  Note: bouton {label!r} visuellement disabled (targetx-button-disabled) — clic tente quand meme.")

    await tab.bring_to_front()
    await tab.sleep(VERIFY_SUBMIT_PRE_CLICK_DELAY_S)

    # 2) Rect frais APRES settle + hit-test elementFromPoint.
    point: dict[str, Any] = await js_eval_json(
        tab,
        f"""
        () => {{
            const btn = document.querySelector(`input[data-alyvo-verify-submit="{marker}"]`);
            if (!btn) return {{ ready: false, reason: 'lostMarker' }};
            const rect = btn.getBoundingClientRect();
            if (rect.width < 2 || rect.height < 2) {{
                return {{ ready: false, reason: 'zeroSize',
                          width: rect.width, height: rect.height }};
            }}
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;
            const hit = document.elementFromPoint(x, y);
            const covered = !!(hit && hit !== btn && !btn.contains(hit) && !hit.contains(btn));
            return {{
                ready: !covered,
                covered,
                x, y,
                hit: covered && hit ? (hit.tagName + (hit.id ? '#' + hit.id : '')) : '',
            }};
        }}
        """,
    )
    if not point.get("ready"):
        log(f"  Verify & Submit: hit-test KO ({point}).")
        return False

    x: float = float(point["x"])
    y: float = float(point["y"])

    # --- Strategies ---

    async def strategy_cdp_raw() -> str:
        await tab.send(cdp.input_.dispatch_mouse_event("mouseMoved", x=x, y=y, buttons=0))
        await tab.sleep(0.05)
        await tab.send(cdp.input_.dispatch_mouse_event(
            "mousePressed", x=x, y=y,
            button=cdp.input_.MouseButton("left"), buttons=1, click_count=1,
        ))
        await tab.sleep(0.06)
        await tab.send(cdp.input_.dispatch_mouse_event(
            "mouseReleased", x=x, y=y,
            button=cdp.input_.MouseButton("left"), buttons=1, click_count=1,
        ))
        await tab.flash_point(x, y)
        return f"CDP raw mouseMoved+Pressed+Released ({x:.0f},{y:.0f})"

    async def strategy_element_mouse() -> str:
        element: Any = await tab.select(
            f'input[data-alyvo-verify-submit="{marker}"]', timeout=8
        )
        await element.scroll_into_view()
        await tab.sleep(0.2)
        await element.mouse_click()
        return "element.mouse_click (nodriver)"

    async def strategy_focus_enter() -> str:
        await js_eval_bool(
            tab,
            f"""
            () => {{
                const btn = document.querySelector(`input[data-alyvo-verify-submit="{marker}"]`);
                if (btn && typeof btn.focus === 'function') btn.focus();
                return true;
            }}
            """,
        )
        await tab.sleep(0.1)
        await tab.send(cdp.input_.dispatch_key_event(
            type_="keyDown", key="Enter", code="Enter",
            windows_virtual_key_code=13, native_virtual_key_code=13,
        ))
        await tab.sleep(0.05)
        await tab.send(cdp.input_.dispatch_key_event(
            type_="keyUp", key="Enter", code="Enter",
            windows_virtual_key_code=13, native_virtual_key_code=13,
        ))
        return "focus + Enter (CDP key event)"

    async def strategy_angular_trigger() -> str:
        triggered: bool = await js_eval_bool(
            tab,
            f"""
            () => {{
                const btn = document.querySelector(`input[data-alyvo-verify-submit="{marker}"]`);
                if (!btn || !window.angular) return false;
                try {{
                    angular.element(btn).triggerHandler('click');
                    return true;
                }} catch (e) {{
                    return false;
                }}
            }}
            """,
        )
        if not triggered:
            raise RuntimeError("triggerHandler indisponible (angular ou bouton manquant)")
        return "angular.triggerHandler('click')"

    strategies = (
        ("CDP raw", strategy_cdp_raw),
        ("element.mouse_click", strategy_element_mouse),
        ("focus+Enter", strategy_focus_enter),
        ("angular triggerHandler", strategy_angular_trigger),
    )

    for name, strategy in strategies:
        try:
            description: str = await strategy()
            log(f"  Verify & Submit — {name} -> {description}.")
        except Exception as error:  # noqa: BLE001
            log(f"  Verify & Submit — {name} KO ({error}).")
            continue
        if await _wait_verify_submit_save_acknowledged(tab):
            log(f"  Verify & Submit — save() declenche apres {name}.")
            return True
        log(f"  Verify & Submit — {name} envoye, save() pas declenche.")

    log("  Verify & Submit — toutes les strategies de clic ont echoue, dump diagnostique :")
    await _dump_verify_submit_diagnostic(tab, log)
    return False


async def complete_application_submit_verification(
    tab: Any,
    account: BrowardAccountInput,
    log: LogFn,
) -> None:
    """
    Page ApplicationSubmit2 : coche la certification, signe, puis Verify & Submit.
    @param tab - Onglet nodriver.
    @param account - Compte courant.
    @param log - Journal stderr.
    """
    if not await wait_for_page_text(tab, "Verify & Submit", BROWARD_APPLICATION_START_TIMEOUT_S, log):
        raise RuntimeError("Page Verify & Submit introuvable apres Submit Your Application.")

    signature: str = f"{account.first_name} {account.last_name}".strip()
    init_attempts: int = max(1, int(BROWARD_APPLICATION_START_TIMEOUT_S / 1.0))
    for i in range(init_attempts):
        ready: bool = await js_eval_bool(
            tab,
            """
            () => {
                const root = document.querySelector('[ng-controller="submitController"]');
                const checkbox = document.querySelector('#TargetX_SRMb__True_and_Correct__c');
                const signatureInput = document.querySelector('#TargetX_SRMb__Electronic_Signature__c');
                if (!root || !checkbox || !signatureInput || !window.angular) return false;
                const scope = angular.element(root).scope();
                return !!(scope && scope.application && scope.application.Id);
            }
            """,
        )
        if ready:
            break
        await tab.sleep(1.0)
        if i > 0 and i % 10 == 0:
            log(f"  Attente chargement ApplicationSubmit2 ({i}/{init_attempts})...")
    else:
        raise RuntimeError("ApplicationSubmit2 Angular non pret.")

    await tab.sleep(1.5)

    async def fill_verify_submit_form() -> bool:
        return await sync_verify_submit_angular_scope(tab, signature)

    if not await fill_verify_submit_form():
        raise RuntimeError("Certification/signature Verify & Submit introuvables.")

    log("  Certification cochee et signature renseignee.")
    await tab.sleep(0.75)

    async def try_submit_verify() -> str:
        state: dict[str, Any] = await read_verify_submit_dom_state(tab)
        if state.get("jsError"):
            log(f"  Verify & Submit — erreur lecture DOM: {state.get('jsError')}")
        if not state.get("btnFound"):
            return ""
        if await click_verify_submit_button(tab, log, signature):
            return "mouse"
        if await invoke_verify_submit_save(tab, signature):
            log("  Soumission Verify & Submit (scope.save).")
            return "save"
        if await invoke_verify_submit_remoting(tab, signature):
            log("  Soumission Verify & Submit (Visualforce remoting).")
            return "remoting"
        return ""

    attempts: int = max(1, int(BROWARD_APPLICATION_START_TIMEOUT_S / 1.0))
    submit_method: str = await try_submit_verify()

    for i in range(attempts):
        if submit_method:
            break
        if i > 0 and i % 3 == 0:
            await fill_verify_submit_form()
        submit_method = await try_submit_verify()
        await tab.sleep(1.0)
        if i > 0 and i % 10 == 0:
            state = await read_verify_submit_dom_state(tab)
            log(
                "  Attente soumission Verify & Submit "
                f"({i}/{attempts}) — cert={state.get('certChecked')}, "
                f"scopeCert={state.get('scopeCert')}, "
                f"signature={state.get('hasSignature')}, "
                f"btnDisabled={state.get('btnDisabled')}, "
                f"domReady={state.get('domReady')}, "
                f"saving={state.get('saving')}..."
            )

    if not submit_method:
        raise RuntimeError("Bouton Verify & Submit introuvable ou soumission impossible.")

    for i in range(attempts):
        submitted: bool = await js_eval_bool(
            tab,
            """
            () => {
                const body = (document.body?.innerText || '').toLowerCase();
                if (
                    body.includes('thank you for submitting your application')
                    || body.includes('welcome to seahawk nation')
                    || body.includes('return home')
                ) {
                    return true;
                }
                try {
                    const root = document.querySelector('[ng-controller="submitController"]');
                    const scope = root && window.angular ? angular.element(root).scope() : null;
                    return !!(scope && scope.submitted);
                } catch (e) {
                    return false;
                }
            }
            """,
        )
        if submitted:
            log("  Candidature Broward soumise.")
            return
        if i > 0 and i % 8 == 0 and submit_method != "remoting":
            if await invoke_verify_submit_remoting(tab, signature):
                log("  Nouvelle tentative soumission (Visualforce remoting).")
                submit_method = "remoting"
        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente confirmation soumission Broward ({i}/{attempts})...")

    raise RuntimeError("Confirmation finale de soumission Broward introuvable.")


async def click_apply2_save_and_continue(
    tab: Any,
    section_label: str,
    log: LogFn,
) -> None:
    """
    Clique le bouton Continue d'une section Apply2 (affiche par CSS comme Save and Continue).
    @param tab - Onglet nodriver.
    @param section_label - aria-label de la section.
    @param log - Journal stderr.
    """
    label_json: str = json.dumps(section_label.lower())
    attempts: int = max(1, int(BROWARD_APPLICATION_START_TIMEOUT_S / 1.0))
    for i in range(attempts):
        clicked: bool = await js_eval_bool(
            tab,
            f"""
            () => {{
                const wanted = {label_json};
                const sections = Array.from(document.querySelectorAll('section[aria-label]'));
                const section = sections.find((el) =>
                    (el.getAttribute('aria-label') || '').trim().toLowerCase() === wanted
                );
                if (!section) return false;
                const buttons = Array.from(section.querySelectorAll('button.targetx-button'));
                const btn = buttons.find((el) => {{
                    const text = (el.textContent || '').trim().toLowerCase();
                    return !el.disabled && text === 'continue';
                }});
                if (!btn) return false;
                btn.scrollIntoView({{ block: 'center' }});
                btn.click();
                return true;
            }}
            """,
        )
        if clicked:
            log(f"  Save and Continue — {section_label}.")
            await tab.sleep(2.0)
            return
        await tab.sleep(1.0)
        if i > 0 and i % 15 == 0:
            log(f"  Attente Save and Continue « {section_label} » ({i}/{attempts})...")
    raise RuntimeError(f"Bouton Save and Continue introuvable pour la section {section_label}.")


async def complete_apply2_remaining_sections(
    tab: Any,
    account: BrowardAccountInput,
    log: LogFn,
) -> None:
    """
    Remplit les sections Apply2 apres Helpful Tips jusqu'a Review Application.
    @param tab - Onglet nodriver.
    @param account - Donnees compte + valeurs Broward.
    @param log - Journal stderr.
    """
    if not await wait_for_page_text(tab, "Personal Information", BROWARD_APPLICATION_START_TIMEOUT_S, log):
        raise RuntimeError("Sections Apply2 apres Helpful Tips introuvables.")

    async def require_field(success: bool, label: str) -> None:
        if not success:
            raise RuntimeError(f"Champ Apply2 introuvable ou non rempli : {label}.")

    async def require_action(action: Callable[[], Any], label: str, attempts: int = 10) -> None:
        for attempt in range(1, attempts + 1):
            if await action():
                return
            await tab.sleep(1.0)
            if attempt < attempts and attempt % 3 == 0:
                log(f"  Retentative champ Apply2 « {label} » ({attempt}/{attempts})...")
        raise RuntimeError(f"Champ Apply2 introuvable ou non rempli : {label}.")

    log("Etape 13/13 — Remplissage sections Broward Apply2...")

    log("  Personal Information...")
    await require_field(await select_apply2_option(tab, "BC_Different_Name__c", "No"), "different name = No")
    await require_field(
        await select_apply2_option(tab, "TargetX_SRMb__Gender__c", account.gender, partial_match=True),
        "gender",
    )
    await require_field(
        await click_apply2_radio(tab, "BC_Are_you_Hispanic_or_Latino__c", "No"),
        "Hispanic/Latino = No",
    )
    await require_field(
        await click_apply2_multicheckbox_option(tab, "TargetX_SRMb__IPEDS_Ethnicities__c", account.race),
        "race",
    )
    await require_field(
        await select_apply2_option(tab, "BC_Primary_Language__c", account.primary_language),
        "primary language",
    )
    await require_field(
        await select_apply2_option(tab, "BC_2_years_of_HS_in_English__c", "Yes"),
        "2 years high school in English = Yes",
    )
    await require_field(
        await click_apply2_radio(tab, "BC_First_Generation_College_Student__c", "No"),
        "first generation = No",
    )
    await click_apply2_save_and_continue(tab, "Personal Information", log)

    log("  Contact Information...")
    await require_field(await select_apply2_option(tab, "MailingCountry", "US"), "mailing country = US")
    await require_field(await fill_apply2_text_field(tab, "street1-MailingStreet", account.street), "mailing street")
    await fill_apply2_hidden_or_text_field(tab, "MailingStreet", account.street)
    await require_field(await fill_apply2_text_field(tab, "MailingCity", account.city), "mailing city")
    await require_field(
        await select_apply2_option(tab, "MailingState", account.state, partial_match=True),
        "mailing state",
    )
    await require_field(await fill_apply2_text_field(tab, "MailingPostalCode", account.postal_code), "postal code")
    await require_field(await fill_apply2_text_field(tab, "MobilePhone", account.mobile_phone), "mobile phone")
    await fill_apply2_text_field(tab, "HomePhone", account.home_phone)
    await click_apply2_save_and_continue(tab, "Contact Information", log)

    log("  Immigration Information...")
    await require_field(await fill_apply2_text_field(tab, "hed__Social_Security_Number__c", account.ssn), "SSN")
    await click_apply2_save_and_continue(tab, "Immigration Information", log)

    log("  Emergency Contact...")
    await require_field(
        await fill_apply2_text_field(tab, "TargetX_SRMb__First_Name__c", account.emergency_first_name),
        "emergency first name",
    )
    await require_field(
        await fill_apply2_text_field(tab, "TargetX_SRMb__Last_Name__c", account.emergency_last_name),
        "emergency last name",
    )
    await require_field(
        await select_apply2_option(tab, "TargetX_SRMb__Relationship__c", account.emergency_relationship),
        "emergency relationship",
    )
    await require_field(await click_apply2_checkbox(tab, "BC_Same_Address__c", True), "emergency same address")
    await require_field(
        await fill_apply2_text_field(tab, "BC_Mobile_Phone__c", account.emergency_mobile_phone),
        "emergency mobile phone",
    )
    await click_apply2_save_and_continue(tab, "Emergency Contact", log)

    log("  High School Details...")
    await require_action(
        lambda: click_apply2_radio(tab, "BC_US_Education_System__c", "Yes"),
        "US high school/home school = Yes",
    )
    await tab.sleep(3.0)
    await require_action(
        lambda: select_apply2_option(
            tab,
            "TargetX_SRMb__Degree_Earned__c",
            account.high_school_degree,
            partial_match=True,
        ),
        "high school degree",
    )
    await require_action(
        lambda: select_apply2_date_dropdown(
            tab,
            "TargetX_SRMb__End_Date__c",
            account.high_school_graduation_date,
        ),
        "anticipated graduation date",
    )
    await require_action(
        lambda: select_apply2_option(tab, "BC_High_School_State__c", account.high_school_state),
        "high school state",
    )
    await require_action(
        lambda: ensure_apply2_autocomplete_value(
            tab,
            "TargetX_SRMb__Account__c",
            account.high_school_name,
        ),
        "high school name",
        attempts=6,
    )
    await click_apply2_save_and_continue(tab, "High School Information", log)
    await require_action(
        lambda: click_apply2_radio(tab, "BC_Did_you_attend_another_college__c", "No"),
        "dual enrollment at another institution = No",
    )
    await click_apply2_save_and_continue(tab, "Enrollment History", log)

    log("  Additional Information...")
    await require_action(
        lambda: click_apply2_radio(tab, "BC_Registered_sex_offender_or_predator__c", "No"),
        "sex offender/predator = No",
    )
    await require_action(
        lambda: select_apply2_option(tab, "TargetX_SRMb__How_Did_You_Find_Out_About_Us__c", "I visited your school"),
        "how did you find out",
    )
    await click_apply2_save_and_continue(tab, "Additional Information", log)

    await tab.sleep(2.0)
    await click_apply2_review_application(tab, log)
    await tab.sleep(3.0)
    await submit_apply2_review_application(tab, log)
    await complete_application_submit_verification(tab, account, log)


async def start_broward_dual_enrollment_application(
    tab: Any,
    account: BrowardAccountInput,
    log: LogFn,
) -> None:
    """
    Apres connexion : portail → nouvelle candidature → Helpful Tips.
    @param tab - Onglet nodriver.
    @param account - Compte courant.
    @param log - Journal stderr.
    """
    log("Etape 10/12 — Ouverture portail candidatures Broward...")
    await tab.get(BROWARD_PORTAL_URL)
    await tab.sleep(2.0)

    if not await wait_for_page_text(
        tab,
        "Start a New Application",
        BROWARD_APPLICATION_START_TIMEOUT_S,
        log,
    ):
        if not await wait_for_page_text(
            tab,
            "No Applications Started",
            BROWARD_APPLICATION_START_TIMEOUT_S,
            log,
        ):
            raise RuntimeError("Portail applications Broward introuvable.")

    log("Etape 11/12 — Demarrage nouvelle candidature (questions + terme)...")
    await click_portal_start_new_application(tab, log)
    await wait_for_url_contains(tab, "NewApplication", 90.0, log)
    await tab.sleep(2.0)
    await fill_new_application_key_questions(tab, account, log)
    await tab.sleep(3.0)

    if not await wait_for_url_contains(tab, "TargetX_App__Apply2", 60.0, log):
        if not await wait_for_page_text(tab, "Broward College", 30.0, log):
            log("  URL Apply2 non detectee, poursuite si formulaire visible...")

    log("Etape 12/12 — Section Helpful Tips (I'm ready to begin + Continue)...")
    await complete_helpful_tips_section(tab, log)
    await complete_apply2_remaining_sections(tab, account, log)
    log("  Candidature remplie jusqu'a Review Application.")


async def run_broward_signup(
    tab: Any,
    account: BrowardAccountInput,
    capsolver_api_key: str,
    log: LogFn,
) -> None:
    """
    Execute le parcours d'inscription Broward pour un compte.
    @param tab - Onglet nodriver.
    @param account - Donnees compte.
    @param capsolver_api_key - Cle CapSolver.
    @param log - Journal stderr.
    """
    account = replace(account, email=normalize_broward_email(account.email))
    log(f"Email cible (normalise) : {account.email}")
    log("Navigation vers le formulaire Broward...")
    await tab.get(SIGNUP_URL)
    await tab.sleep(STEP_PAUSE_AFTER_NAVIGATION_S)

    log("Etape 1/5 — Prenom")
    log(f"  Saisie : {account.first_name}")
    await fill_input_fast(tab, SELECTOR_FIRST_NAME, account.first_name)

    log("Etape 2/5 — Nom")
    log(f"  Saisie : {account.last_name}")
    await fill_input_fast(tab, SELECTOR_LAST_NAME, account.last_name)

    log("Etape 3/5 — Date de naissance")
    log(f"  Saisie : {account.birthday}")
    await fill_date_input_fast(tab, SELECTOR_BIRTHDATE, account.birthday)

    log("Etape 4/5 — Email")
    log(f"  Saisie : {account.email}")
    await fill_input_fast(tab, SELECTOR_EMAIL, account.email)
    log("  Confirmation email")
    await fill_input_fast(tab, SELECTOR_CONFIRM_EMAIL, account.email)

    await prepare_captcha_section(tab, log)

    log("Etape 5/5 — reCAPTCHA (CapSolver -> callback() TargetX, sans clic sur la case)")
    captcha_ok: bool = await resolve_captcha(tab, capsolver_api_key, log)
    if not captcha_ok:
        raise RuntimeError(
            "reCAPTCHA non valide : le token CapSolver seul ne suffit pas et le delai manuel est depasse. "
            "Cochez « Je ne suis pas un robot » si la case reste vide."
        )

    await click_submit(tab, log)
    await wait_for_post_submit(tab, log)
    log("Preinscription Broward terminee — mot de passe a configurer.")

    await request_broward_password_email(tab, account, log)
    set_password_link: str = await open_outlook_and_extract_password_link(tab, account, log)
    try:
        await save_broward_password_from_link(tab, set_password_link, account, log)
    except RuntimeError as error:
        error_text: str = str(error)
        recoverable_link_error: bool = (
            "expire" in error_text.lower()
            or "url no longer exists" in error_text.lower()
            or "redirige vers le portail sans afficher" in error_text.lower()
        )
        if not recoverable_link_error:
            raise
        log(
            "  Lien Reset Password invalide/expire — nouvelle demande Broward "
            "et recuperation d'un nouveau mail...",
        )
        await submit_broward_forgot_password_pass(
            tab,
            account,
            log,
            pass_index=1,
            pass_total=1,
        )
        set_password_link = await open_outlook_and_extract_password_link(tab, account, log)
        await save_broward_password_from_link(tab, set_password_link, account, log)
    await start_broward_dual_enrollment_application(tab, account, log)
    log(f"Inscription Broward et demarrage candidature termines pour {account.email}")
