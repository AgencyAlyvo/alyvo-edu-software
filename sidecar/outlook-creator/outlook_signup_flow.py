"""
Automatisation du flux d'inscription Microsoft Outlook (signup.live.com).
"""
from __future__ import annotations

import asyncio
import ctypes
import platform
import time
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from email_builder import build_outlook_email
from nodriver import cdp

SIGNUP_URL: str = "https://signup.live.com/?lic=1"
CAPTCHA_HOLD_SECONDS: float = 13.0
CAPTCHA_IFRAME_SELECTOR: str = 'iframe[data-testid="humanCaptchaIframe"]'
# Texte d'aide hors iframe (ne pas cliquer) : data-testid="humanCaptchaDescription"
CAPTCHA_HOLD_SELECTORS: tuple[str, ...] = (
    "#px-captcha",
    "#px-captcha-wrapper",
    "button",
    '[role="button"]',
)
# Barre basse de l'iframe : icone accessibilite a gauche, pilule « Appuyer et maintenir » a droite.
CAPTCHA_IFRAME_CLICK_X_RATIO: float = 0.72
# Centre vertical de la pilule dans la barre basse (~90px de haut d'iframe).
CAPTCHA_IFRAME_CLICK_Y_FROM_BOTTOM_RATIO: float = 0.25
CAPTCHA_HOLD_PHRASES: tuple[str, ...] = (
    "Appuyer et maintenir",
    "Press and hold",
)

# Delais de saisie « humaine » avant le CAPTCHA (secondes).
TYPING_DELAY_BEFORE_FIELD_S: float = 0.35
TYPING_DELAY_PER_CHAR_S: float = 0.09
TYPING_DELAY_AFTER_FIELD_S: float = 0.5
TYPING_DELAY_BEFORE_PRIMARY_BUTTON_S: float = 1.6
DROPDOWN_OPEN_DELAY_S: float = 1.0
DROPDOWN_RETRY_OPEN_DELAY_S: float = 0.9
DROPDOWN_AFTER_SELECT_S: float = 0.55
STEP_PAUSE_AFTER_NAVIGATION_S: float = 2.0
# Ralentissement global anti-blocage Outlook (+2 s repartis entre les etapes du formulaire).
OUTLOOK_SIGNUP_EXTRA_DELAY_S: float = 2.0
OUTLOOK_SIGNUP_STEP_PAUSE_S: float = OUTLOOK_SIGNUP_EXTRA_DELAY_S / 4

MONTH_LABELS_EN: tuple[str, ...] = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

MONTH_LABELS_FR: tuple[str, ...] = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)

MONTH_LABELS_FR_ASCII: tuple[str, ...] = (
    "janvier",
    "fevrier",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "aout",
    "septembre",
    "octobre",
    "novembre",
    "decembre",
)

MONTH_SHORT_FR: tuple[str, ...] = (
    "janv.",
    "févr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juil.",
    "août",
    "sept.",
    "oct.",
    "nov.",
    "déc.",
)


@dataclass(frozen=True)
class SignupCredentials:
    email: str
    password: str
    first_name: str
    last_name: str
    birthday: str


LogFn = Callable[[str], None]


async def pause_outlook_signup_step(tab: Any) -> None:
    """Pause entre deux etapes du formulaire (limite les blocages anti-bot)."""
    if OUTLOOK_SIGNUP_STEP_PAUSE_S > 0:
        await tab.sleep(OUTLOOK_SIGNUP_STEP_PAUSE_S)


def normalize_text(value: str) -> str:
    """Retire les accents pour comparaison de titres."""
    decomposed: str = unicodedata.normalize("NFD", value)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn").lower()


def month_dropdown_labels(month: int) -> tuple[str, ...]:
    """
    Libelles possibles pour un mois (1-12) dans le combobox Fluent Microsoft.
    L'UI signup.live.com est en general en francais : janvier, Janvier, janv., etc.
    """
    index: int = month - 1
    fr: str = MONTH_LABELS_FR[index]
    fr_ascii: str = MONTH_LABELS_FR_ASCII[index]
    en: str = MONTH_LABELS_EN[index]
    short_fr: str = MONTH_SHORT_FR[index]

    seen: set[str] = set()
    labels: list[str] = []

    def add(label: str) -> None:
        key: str = normalize_text(label)
        if key not in seen:
            seen.add(key)
            labels.append(label)

    for candidate in (
        fr,
        fr.capitalize(),
        fr_ascii,
        fr_ascii.capitalize(),
        short_fr,
        short_fr.capitalize(),
        en,
        en[:3],
    ):
        add(candidate)

    return tuple(labels)


async def run_outlook_signup(
    tab: Any,
    password: str,
    birthday_iso: str,
    first_name: str,
    last_name: str,
    log: LogFn,
) -> SignupCredentials:
    """
    Execute le parcours complet signup.live.com jusqu'a la fin ou echec.
    @param tab
    @param password
    @param birthday_iso
    @param first_name
    @param last_name
    @param log
    """
    email: str = build_outlook_email(first_name, last_name)
    birth: date = date.fromisoformat(birthday_iso)

    log(f"Email cible : {email}")
    log("Navigation vers signup.live.com/?lic=1 ...")
    await tab.get(SIGNUP_URL)
    await tab.sleep(STEP_PAUSE_AFTER_NAVIGATION_S)

    log("Etape 1/5 — Adresse e-mail")
    await wait_for_title_contains(tab, "créez votre compte", timeout=60)
    log(f"  Saisie de l'email : {email}")
    await fill_input(tab, 'input[name="email"]', email)
    log("  Clic sur Suivant (email)")
    await click_primary_button(tab)
    await pause_outlook_signup_step(tab)

    log("Etape 2/5 — Mot de passe")
    await wait_for_title_contains(tab, "mot de passe", timeout=45)
    log("  Saisie du mot de passe")
    await fill_input(tab, 'input[type="password"]', password)
    log("  Clic sur Suivant (mot de passe)")
    await click_primary_button(tab)
    await pause_outlook_signup_step(tab)

    banner_email: str | None = await read_identity_email(tab)
    if banner_email:
        email = banner_email
        log(f"Email confirme (bandeau) : {email}")

    log("Etape 3/5 — Date de naissance")
    await wait_for_title_contains(tab, "ajouter des détails", timeout=45)
    await fill_birthdate(tab, birth, log)
    log("  Clic sur Suivant (date de naissance)")
    await click_primary_button(tab)
    await pause_outlook_signup_step(tab)

    log("Etape 4/5 — Prenom et nom")
    await wait_for_title_contains(tab, "ajouter votre nom", timeout=45)
    log(f"  Saisie prenom : {first_name}")
    await fill_input(tab, "#firstNameInput", first_name)
    log(f"  Saisie nom : {last_name}")
    await fill_input(tab, "#lastNameInput", last_name)
    log("  Clic sur Suivant (nom)")
    await click_primary_button(tab)
    await pause_outlook_signup_step(tab)

    log("Etape 5/5 — Verification humaine (CAPTCHA)")
    await wait_for_title_contains(tab, "humain", timeout=60)
    await solve_press_and_hold_captcha(tab, log, hold_seconds=CAPTCHA_HOLD_SECONDS)

    log("Attente de la fin de l'inscription...")
    completed: bool = await wait_signup_complete(tab, timeout=120)
    if not completed:
        raise TimeoutError(
            "Inscription non terminee dans le delai imparti (CAPTCHA ou etape finale). "
            "Completez manuellement si la fenetre est encore ouverte."
        )

    await click_post_signup_ok(tab, log)

    final_email: str | None = await read_identity_email(tab)
    if final_email:
        email = final_email

    return SignupCredentials(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        birthday=birthday_iso,
    )


async def get_title_text(tab: Any, timeout: float = 5) -> str:
    """Lit le texte du titre principal de la page."""
    try:
        element: Any = await tab.select('[data-testid="title"]', timeout=timeout)
        return (element.text or "").strip()
    except Exception:  # noqa: BLE001
        return ""


async def wait_for_title_contains(tab: Any, needle: str, timeout: float = 45) -> None:
    """Attend que le titre de page contienne une sous-chaine."""
    needle_normalized: str = normalize_text(needle)
    deadline: float = time.monotonic() + timeout

    while time.monotonic() < deadline:
        title: str = await get_title_text(tab, timeout=3)
        if needle_normalized in normalize_text(title):
            return
        await tab.sleep(0.5)

    raise TimeoutError(f"Titre attendu contenant {needle!r} (dernier titre : {await get_title_text(tab)!r})")


async def type_text_human(tab: Any, element: Any, text: str) -> None:
    """Saisie caractere par caractere pour limiter les signaux « bot »."""
    for char in text:
        await element.send_keys(char)
        await tab.sleep(TYPING_DELAY_PER_CHAR_S)


async def fill_input(tab: Any, selector: str, value: str, timeout: float = 20) -> None:
    """Remplit un champ input Fluent avec delais entre les frappes."""
    element: Any = await tab.select(selector, timeout=timeout)
    await element.scroll_into_view()
    await tab.sleep(TYPING_DELAY_BEFORE_FIELD_S)
    await element.click()
    await tab.sleep(TYPING_DELAY_BEFORE_FIELD_S)
    await type_text_human(tab, element, value)
    await tab.sleep(TYPING_DELAY_AFTER_FIELD_S)


async def click_primary_button(tab: Any, timeout: float = 20) -> None:
    """Clique sur le bouton Suivant principal."""
    button: Any = await tab.select('button[data-testid="primaryButton"]', timeout=timeout)
    await button.scroll_into_view()
    await tab.sleep(TYPING_DELAY_BEFORE_PRIMARY_BUTTON_S)
    await button.click()
    await tab.sleep(TYPING_DELAY_BEFORE_PRIMARY_BUTTON_S)


async def fill_birthdate(tab: Any, birth: date, log: LogFn) -> None:
    """Remplit jour, mois et annee sur l'ecran Ajouter des details."""
    day: str = str(birth.day)
    year: str = str(birth.year)
    month_labels: tuple[str, ...] = month_dropdown_labels(birth.month)

    log(f"  Date ISO {birth.isoformat()} → jour {day}, mois {month_labels[0]!r} (+ variantes)")

    await fill_fluent_dropdown(
        tab,
        "#BirthDayDropdown",
        (day,),
        log,
        f"Jour {day}",
        exact_match=True,
    )
    await fill_fluent_dropdown(
        tab,
        "#BirthMonthDropdown",
        month_labels,
        log,
        f"Mois ({birth.month:02d})",
        exact_match=False,
    )

    year_input: Any = await tab.select('input[name="BirthYear"]', timeout=15)
    await year_input.scroll_into_view()
    await tab.sleep(TYPING_DELAY_BEFORE_FIELD_S)
    await year_input.click()
    await tab.sleep(TYPING_DELAY_BEFORE_FIELD_S)
    await type_text_human(tab, year_input, year)
    await tab.sleep(TYPING_DELAY_AFTER_FIELD_S)


def _option_matches(option_norm: str, target_norm: str, *, exact_match: bool) -> bool:
    if option_norm == target_norm:
        return True
    if exact_match:
        return False
    return target_norm in option_norm


async def fill_fluent_dropdown(
    tab: Any,
    combobox_selector: str,
    option_labels: tuple[str, ...],
    log: LogFn,
    label: str,
    *,
    exact_match: bool = False,
) -> None:
    """Ouvre un combobox Fluent et selectionne une option par texte (plusieurs variantes)."""
    if not option_labels:
        raise ValueError(f"Aucun libelle pour {label!r}")

    combobox: Any = await tab.select(combobox_selector, timeout=15)
    await combobox.scroll_into_view()
    await tab.sleep(TYPING_DELAY_BEFORE_FIELD_S)
    await combobox.click()
    await tab.sleep(DROPDOWN_OPEN_DELAY_S)

    selected: bool = await _click_listbox_option(tab, option_labels, log, exact_match=exact_match)
    if not selected:
        await tab.sleep(0.4)
        await combobox.click()
        await tab.sleep(DROPDOWN_RETRY_OPEN_DELAY_S)
        selected = await _click_listbox_option(tab, option_labels, log, exact_match=exact_match)

    if not selected:
        raise TimeoutError(
            f"Option introuvable pour {label!r} (essais : {', '.join(option_labels[:6])}...)"
        )

    await tab.sleep(DROPDOWN_AFTER_SELECT_S)
    log(f"  {label} selectionne")


async def _click_listbox_option(
    tab: Any,
    option_labels: tuple[str, ...],
    log: LogFn,
    *,
    exact_match: bool,
) -> bool:
    """Selectionne une option dans le listbox Fluent ouvert."""
    normalized_targets: tuple[str, ...] = tuple(normalize_text(text) for text in option_labels)

    for candidate in option_labels:
        try:
            option: Any = await tab.find(
                candidate,
                best_match=not exact_match,
                timeout=2,
            )
            if option is not None:
                option_text: str = (option.text or "").strip()
                if _option_matches(normalize_text(option_text), normalize_text(candidate), exact_match=exact_match):
                    await option.click()
                    log(f"    option via find : {option_text!r}")
                    return True
        except Exception:  # noqa: BLE001
            continue

    try:
        options: list[Any] = await tab.select_all('[role="option"]', timeout=4)
    except Exception:  # noqa: BLE001
        options = []

    for option in options:
        option_text = (option.text or "").strip()
        if not option_text:
            continue
        normalized_option: str = normalize_text(option_text)
        for target in normalized_targets:
            if _option_matches(normalized_option, target, exact_match=exact_match):
                await option.click()
                log(f"    option via role=option : {option_text!r}")
                return True

    return False


async def read_identity_email(tab: Any) -> str | None:
    """Lit l'email affiche dans le bandeau d'identite."""
    try:
        banner: Any = await tab.select('[data-testid="identityBanner"]', timeout=5)
        aria_label: str = (banner.attrs.get("aria-label") or "").strip()
        if "@" in aria_label:
            return aria_label
        text: str = (banner.text or "").strip()
        if "@" in text:
            return text
    except Exception:  # noqa: BLE001
        return None
    return None


async def _element_area(element: Any) -> float:
    try:
        result: Any = await element.apply(
            "(el) => { const r = el.getBoundingClientRect(); return r.width * r.height; }",
            return_by_value=True,
        )
        if isinstance(result, (int, float)):
            return float(result)
    except Exception:  # noqa: BLE001
        return 0.0
    return 0.0


async def _pick_largest_element(elements: list[Any], min_area: float = 1200.0) -> Any | None:
    best: Any | None = None
    best_area: float = min_area
    for element in elements:
        area: float = await _element_area(element)
        if area >= best_area:
            best_area = area
            best = element
    return best


async def _get_captcha_iframe(tab: Any, log: LogFn) -> Any | None:
    try:
        iframe: Any = await tab.select(CAPTCHA_IFRAME_SELECTOR, timeout=10)
        await iframe.scroll_into_view()
        await tab.sleep(0.3)
        return iframe
    except Exception as error:  # noqa: BLE001
        log(f"  Iframe CAPTCHA introuvable : {error}")
        return None


async def _promote_to_hold_button(tab: Any, element: Any, log: LogFn, phrase: str) -> Any | None:
    """Remonte vers un conteneur cliquable large (pilule « Appuyer et maintenir »)."""
    try:
        parent: Any | None = element
        for _ in range(10):
            if parent is None:
                break
            area: float = await _element_area(parent)
            size: Any = await parent.apply(
                "(el) => { const r = el.getBoundingClientRect(); return { width: r.width, height: r.height }; }",
                return_by_value=True,
            )
            width: float = 0.0
            height: float = 0.0
            if isinstance(size, dict):
                width = float(size.get("width", 0))
                height = float(size.get("height", 0))

            if area >= 1200 and width >= 80 and width >= height * 1.2:
                log(f"  Bouton CAPTCHA via texte {phrase!r} ({width:.0f}x{height:.0f})")
                return parent
            parent = parent.parent
    except Exception:  # noqa: BLE001
        return None
    return None


async def _find_captcha_hold_button(tab: Any, log: LogFn) -> Any | None:
    """
    Cherche le bouton dans l'iframe PerimeterX uniquement
    (pas le span « Appuyez longuement… » dans humanCaptchaDescription).
    """
    iframe: Any | None = await _get_captcha_iframe(tab, log)
    if iframe is None:
        return None

    for phrase in CAPTCHA_HOLD_PHRASES:
        try:
            found: Any = await iframe.find(phrase, best_match=True, timeout=5)
        except Exception:  # noqa: BLE001
            continue
        if found is None:
            continue
        target: Any | None = await _promote_to_hold_button(tab, found, log, phrase)
        if target is not None:
            return target

    for selector in CAPTCHA_HOLD_SELECTORS:
        try:
            matches: list[Any] = await iframe.select_all(selector, timeout=4)
        except Exception:  # noqa: BLE001
            try:
                matches = await tab.select_all(selector, timeout=3, include_frames=True)
            except Exception:  # noqa: BLE001
                continue
        target = await _pick_largest_element(matches, min_area=800.0)
        if target is not None:
            log(f"  Bouton CAPTCHA dans iframe : {selector}")
            return target

    return None


async def _captcha_click_point_from_iframe(tab: Any, log: LogFn) -> tuple[float, float] | None:
    """
    Point de clic viewport pour la pilule « Appuyer et maintenir »
    (centre-droit de l'iframe, pres du bas).
    """
    iframe: Any | None = await _get_captcha_iframe(tab, log)
    if iframe is None:
        return None

    x_ratio: float = CAPTCHA_IFRAME_CLICK_X_RATIO
    y_from_bottom: float = CAPTCHA_IFRAME_CLICK_Y_FROM_BOTTOM_RATIO

    try:
        result: Any = await iframe.apply(
            f"""(el) => {{
                const r = el.getBoundingClientRect();
                const yInset = Math.max(10, r.height * {y_from_bottom});
                return {{
                    x: r.left + r.width * {x_ratio},
                    y: r.bottom - yInset,
                    width: r.width,
                    height: r.height,
                    left: r.left,
                    top: r.top,
                    bottom: r.bottom,
                }};
            }}""",
            return_by_value=True,
        )
    except Exception as error:  # noqa: BLE001
        log(f"  Position iframe indisponible : {error}")
        return None

    if not isinstance(result, dict):
        return None

    x_raw: Any = result.get("x")
    y_raw: Any = result.get("y")
    if x_raw is None or y_raw is None:
        return None

    x: float = float(x_raw)
    y: float = float(y_raw)
    width: float = float(result.get("width", 0))
    height: float = float(result.get("height", 0))

    if width < 40 or height < 24:
        log("  Iframe CAPTCHA trop petite pour un clic fiable")
        return None

    log(
        f"  Iframe CAPTCHA {width:.0f}x{height:.0f}px "
        f"(viewport left={float(result.get('left', 0)):.0f} top={float(result.get('top', 0)):.0f})"
    )
    log(
        f"  Clic pilule « Appuyer et maintenir » → ({x:.0f}, {y:.0f}) "
        f"[x={x_ratio:.0%} largeur, y=bas-{y_from_bottom:.0%} hauteur]"
    )
    return x, y


async def _viewport_to_screen(tab: Any, viewport_x: float, viewport_y: float) -> tuple[int, int] | None:
    """Convertit des coordonnees viewport Chrome en position ecran (Windows)."""
    try:
        result: Any = await tab.evaluate(
            f"""() => {{
                const chromeYOffset = window.outerHeight - window.innerHeight;
                return {{
                    screenX: Math.round(window.screenX + {viewport_x}),
                    screenY: Math.round(window.screenY + chromeYOffset + {viewport_y}),
                }};
            }}"""
        )
        if isinstance(result, dict) and result.get("screenX") is not None and result.get("screenY") is not None:
            return int(result["screenX"]), int(result["screenY"])
    except Exception:  # noqa: BLE001
        return None
    return None


def _mouse_hold_screen_windows_sync(screen_x: int, screen_y: int, hold_seconds: float) -> None:
    """Appui gauche prolonge via l'API Windows (evenements souris « reels »)."""
    user32 = ctypes.windll.user32
    try:
        user32.SetProcessDPIAware()
    except Exception:  # noqa: BLE001
        pass

    user32.SetCursorPos(screen_x, screen_y)
    time.sleep(0.25)
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
    time.sleep(hold_seconds)
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP


async def _mouse_hold_at_point_windows_os(
    tab: Any,
    viewport_x: float,
    viewport_y: float,
    hold_seconds: float,
    log: LogFn,
) -> bool:
    screen: tuple[int, int] | None = await _viewport_to_screen(tab, viewport_x, viewport_y)
    if screen is None:
        return False

    screen_x, screen_y = screen
    log(
        f"  Appui OS Windows (souris reelle) viewport ({viewport_x:.0f}, {viewport_y:.0f}) "
        f"→ ecran ({screen_x}, {screen_y}) pendant {hold_seconds}s"
    )
    await asyncio.to_thread(_mouse_hold_screen_windows_sync, screen_x, screen_y, hold_seconds)
    return True


async def mouse_hold_at_point(
    tab: Any,
    x: float,
    y: float,
    hold_seconds: float,
    log: LogFn,
) -> None:
    """Appui prolonge : souris OS sur Windows, sinon CDP."""
    if platform.system() == "Windows":
        if await _mouse_hold_at_point_windows_os(tab, x, y, hold_seconds, log):
            return

    log(f"  Appui CDP a ({x:.0f}, {y:.0f}) pendant {hold_seconds}s (peut etre ignore par PerimeterX)")

    await tab.send(cdp.input_.dispatch_mouse_event("mouseMoved", x=x, y=y))
    await tab.send(
        cdp.input_.dispatch_mouse_event(
            "mousePressed",
            x=x,
            y=y,
            button=cdp.input_.MouseButton("left"),
            buttons=1,
            click_count=1,
        )
    )
    await tab.sleep(hold_seconds)
    await tab.send(
        cdp.input_.dispatch_mouse_event(
            "mouseReleased",
            x=x,
            y=y,
            button=cdp.input_.MouseButton("left"),
            buttons=1,
            click_count=1,
        )
    )


async def solve_press_and_hold_captcha(tab: Any, log: LogFn, hold_seconds: float = CAPTCHA_HOLD_SECONDS) -> None:
    """Maintien prolonge sur le bouton PerimeterX (DOM iframe, sinon position calculee)."""
    log("  Recherche du bouton dans l'iframe CAPTCHA (PerimeterX)...")

    try:
        await tab.select(CAPTCHA_IFRAME_SELECTOR, timeout=60)
    except Exception:  # noqa: BLE001
        log("  Iframe CAPTCHA absente — poursuite (saisie manuelle possible)")
        return

    await tab.sleep(2)

    target: Any | None = await _find_captcha_hold_button(tab, log)
    if target is not None:
        await mouse_hold_element(tab, target, hold_seconds, log)
        log(f"  Maintien du bouton ~{hold_seconds}s effectue (via DOM)")
        await tab.sleep(1.5)
        return

    click_point: tuple[float, float] | None = await _captcha_click_point_from_iframe(tab, log)
    if click_point is not None:
        log("  Repli : position pilule dans l'iframe (DOM PerimeterX inaccessible)")
        await mouse_hold_at_point(tab, click_point[0], click_point[1], hold_seconds, log)
        log(f"  Maintien ~{hold_seconds}s termine — si echec, PerimeterX bloque peut-etre l'automatisation")
        await tab.sleep(1.5)
        return

    log("  Bouton CAPTCHA introuvable — 15 s pour intervention manuelle")


async def mouse_hold_element(tab: Any, element: Any, hold_seconds: float, log: LogFn) -> None:
    """Appui souris prolonge au centre de l'element (CDP, coordonnees viewport)."""
    await element.scroll_into_view()
    await tab.sleep(0.5)

    position: Any = await element.get_position()
    if position is None or not getattr(position, "center", None):
        log("  Centre du bouton introuvable — repli element.click()")
        await element.click()
        await tab.sleep(hold_seconds)
        return

    center: tuple[float, float] = position.center
    await mouse_hold_at_point(tab, float(center[0]), float(center[1]), hold_seconds, log)


POST_SIGNUP_OK_SELECTORS: tuple[str, ...] = (
    "#StickyFooter button.ms-Button--primary",
    "#StickyFooter button[type='button']",
    "#StickyFooter button",
)


async def _button_visible_label(button: Any) -> str:
    """Lit le libelle visible d'un bouton Fluent UI."""
    try:
        result: Any = await button.apply(
            """(el) => {
                const label = el.querySelector('.ms-Button-label');
                return (label?.textContent || el.textContent || '').trim();
            }"""
        )
        if isinstance(result, str):
            return result.strip()
    except Exception:  # noqa: BLE001
        pass
    return (getattr(button, "text", None) or "").strip()


def _is_post_signup_ok_label(label: str) -> bool:
    normalized: str = normalize_text(label)
    return normalized in ("ok", "daccord", "done", "termine", "continuer")


async def click_post_signup_ok(tab: Any, log: LogFn, timeout: float = 60) -> None:
    """
    Clique le bouton OK du pied de page (#StickyFooter) apres creation du compte.
    @param tab
    @param log
    @param timeout
    """
    log("Ecran de confirmation — recherche du bouton OK...")
    deadline: float = time.monotonic() + timeout

    while time.monotonic() < deadline:
        for selector in POST_SIGNUP_OK_SELECTORS:
            try:
                button: Any = await tab.select(selector, timeout=2)
                label: str = await _button_visible_label(button)
                if label and not _is_post_signup_ok_label(label):
                    continue
                await button.scroll_into_view()
                await button.click()
                log(f"  Bouton OK clique ({label or 'StickyFooter'}).")
                await tab.sleep(1.5)
                return
            except Exception:  # noqa: BLE001
                continue

        try:
            footer: Any = await tab.select("#StickyFooter", timeout=2)
            await footer.scroll_into_view()
            matches: list[Any] = await footer.select_all("button", timeout=2)
            for button in matches:
                label = await _button_visible_label(button)
                if _is_post_signup_ok_label(label):
                    await button.click()
                    log(f"  Bouton OK clique via pied de page ({label!r}).")
                    await tab.sleep(1.5)
                    return
        except Exception:  # noqa: BLE001
            pass

        try:
            found: Any = await tab.find("OK", best_match=True, timeout=2)
            label = await _button_visible_label(found)
            if _is_post_signup_ok_label(label):
                await found.scroll_into_view()
                await found.click()
                log("  Bouton OK clique (recherche texte).")
                await tab.sleep(1.5)
                return
        except Exception:  # noqa: BLE001
            pass

        await tab.sleep(0.5)

    log("  Bouton OK non trouve dans le delai imparti (deja valide ou autre ecran).")


async def wait_signup_complete(tab: Any, timeout: float = 120) -> bool:
    """
    Attend que le wizard d'inscription soit termine (apres CAPTCHA).
    @param tab
    @param timeout
    """
    wizard_markers: tuple[str, ...] = (
        "creez votre compte",
        "creer votre mot de passe",
        "ajouter des details",
        "ajouter votre nom",
        "humain",
        "human",
    )

    deadline: float = time.monotonic() + timeout
    stable_count: int = 0

    while time.monotonic() < deadline:
        title: str = normalize_text(await get_title_text(tab, timeout=2))
        url: str = (getattr(tab, "url", None) or "").lower()

        in_wizard: bool = any(marker in title for marker in wizard_markers)
        on_signup: bool = "signup.live.com" in url

        if not in_wizard and not on_signup:
            return True

        if not in_wizard and on_signup:
            stable_count += 1
            if stable_count >= 4:
                return True
        else:
            stable_count = 0

        await tab.sleep(1)

    return False
