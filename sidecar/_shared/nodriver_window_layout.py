"""Placement des fenetres Chrome nodriver (multi-instance, max 2 par ecran)."""
from __future__ import annotations

import platform
from collections.abc import Callable
from typing import Any

WINDOW_LAYOUT_MARGIN_PX: int = 12
WINDOW_LAYOUT_GAP_PX: int = 8
MAX_INSTANCES_PER_MONITOR: int = 2
WINDOW_LAYOUT_SETTLE_SECONDS: float = 0.35


def _set_process_dpi_aware() -> None:
    if platform.system() != "Windows":
        return

    try:
        import ctypes

        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:  # noqa: BLE001
        pass


def _enumerate_monitors_windows() -> list[dict[str, int]]:
    import ctypes
    from ctypes import wintypes

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    monitors: list[dict[str, int]] = []

    def _callback(
        _hmon: int,
        _hdc: int,
        lprc_monitor: ctypes.POINTER(RECT),
        _data: wintypes.LPARAM,
    ) -> int:
        rect = lprc_monitor.contents
        width: int = int(rect.right - rect.left)
        height: int = int(rect.bottom - rect.top)
        if width > 0 and height > 0:
            monitors.append(
                {
                    "left": int(rect.left),
                    "top": int(rect.top),
                    "width": width,
                    "height": height,
                }
            )
        return 1

    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(RECT),
        wintypes.LPARAM,
    )

    ctypes.windll.user32.EnumDisplayMonitors(0, 0, MONITORENUMPROC(_callback), 0)
    return monitors


def compute_window_bounds(slot: int, slots: int) -> tuple[int, int, int, int] | None:
    """
    Calcule left, top, width, height pour un slot (0-based).
    Max 2 instances par ecran : gauche / droite avec marge.
    """
    if slots <= 1 or slot < 0 or slot >= slots:
        return None

    if platform.system() != "Windows":
        return None

    _set_process_dpi_aware()
    monitors: list[dict[str, int]] = _enumerate_monitors_windows()
    if not monitors:
        monitors = [{"left": 0, "top": 0, "width": 1920, "height": 1080}]

    screen_index: int = slot // MAX_INSTANCES_PER_MONITOR
    pos_on_screen: int = slot % MAX_INSTANCES_PER_MONITOR

    if screen_index >= len(monitors):
        screen_index %= len(monitors)

    monitor: dict[str, int] = monitors[screen_index]
    margin: int = WINDOW_LAYOUT_MARGIN_PX
    gap: int = WINDOW_LAYOUT_GAP_PX
    usable_width: int = monitor["width"] - (2 * margin) - gap
    half_width: int = max(320, usable_width // 2)
    height: int = max(240, monitor["height"] - (2 * margin))
    top: int = monitor["top"] + margin

    if pos_on_screen == 0:
        left: int = monitor["left"] + margin
        width: int = half_width
    else:
        left = monitor["left"] + margin + half_width + gap
        width = half_width

    return left, top, width, height


async def apply_nodriver_window_layout(
    tab: Any,
    *,
    slot: int,
    slots: int,
    log_fn: Callable[[str], None] | None = None,
) -> bool:
    """Positionne la fenetre Chrome via CDP nodriver."""
    bounds: tuple[int, int, int, int] | None = compute_window_bounds(slot, slots)
    if bounds is None:
        return False

    left, top, width, height = bounds
    log = log_fn or (lambda _message: None)

    screen_index: int = slot // MAX_INSTANCES_PER_MONITOR
    pos_on_screen: int = slot % MAX_INSTANCES_PER_MONITOR
    side_label: str = "gauche" if pos_on_screen == 0 else "droite"
    log(
        f"Fenetre Chrome : ecran {screen_index + 1}, moitie {side_label} "
        f"({width}x{height} @ {left},{top})"
    )

    try:
        await tab.set_window_state(left, top, width, height, state="normal")
        await tab.activate()
        await tab.sleep(WINDOW_LAYOUT_SETTLE_SECONDS)
    except Exception as error:  # noqa: BLE001
        log(f"  Placement fenetre ignore : {error}")
        return False

    return True
