"""Read a conservative preconditioning target from a VTherm preset.

This helper only reads an existing climate state. It never changes a preset or
temperature. Presence-dependent presets are intentionally unresolved until a
future-state contract exists; their effective target cannot be inferred from
the current presence alone.
"""

import math

_PRESETS = frozenset({"frost", "eco", "comfort", "boost"})


def vtherm_preset_target(state, preset: str) -> float | None:
    """Return a usable active-heating preset temperature, or no target."""
    if state is None or state.state != "heat" or preset not in _PRESETS:
        return None
    attrs = state.attributes
    config = attrs.get("configuration")
    presets = attrs.get("preset_temperatures")
    if not isinstance(config, dict) or not isinstance(presets, dict):
        return None
    if config.get("type") not in {"over_climate", "over_climate_valve", "over_switch", "over_valve"}:
        return None
    if attrs.get("is_ready") is not True or attrs.get("is_presence_configured") is not False:
        return None
    if attrs.get("is_window_auto_configured") is not False:
        return None
    safety = attrs.get("safety_manager")
    if attrs.get("is_safety_configured") and (
        not isinstance(safety, dict) or safety.get("safety_state") != "off"
    ):
        return None
    if attrs.get("is_power_configured") is not False:
        return None
    window = attrs.get("window_manager")
    if attrs.get("is_window_configured") and (
        not isinstance(window, dict) or window.get("window_state") != "off"
    ):
        return None
    try:
        raw_target = presets[f"{preset}_temp"]
        if isinstance(raw_target, bool):
            return None
        target = float(raw_target)
        low = float(attrs["min_temp"])
        high = float(attrs["max_temp"])
    except (KeyError, TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in (target, low, high)):
        return None
    if not low <= target <= high:
        return None
    return target
