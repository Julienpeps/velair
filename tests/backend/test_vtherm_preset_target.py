"""Tests for reading VTherm targets without writing to the thermostat."""

import unittest
from types import SimpleNamespace

from . import helpers  # Install the Home Assistant test stubs before importing.
from custom_components.velair.vtherm_preset_target import vtherm_preset_target


def state(**changes):
    attrs = {
        "configuration": {"type": "over_climate_valve"},
        "preset_temperatures": {"eco_temp": 17, "boost_temp": 21.5},
        "is_ready": True,
        "is_presence_configured": False,
        "is_window_configured": True,
        "is_window_auto_configured": False,
        "window_manager": {"window_state": "off"},
        "is_safety_configured": True,
        "safety_manager": {"safety_state": "off"},
        "is_power_configured": False,
        "min_temp": 10,
        "max_temp": 30,
    }
    attrs.update(changes)
    return SimpleNamespace(state="heat", attributes=attrs)


class PresetTargetTest(unittest.TestCase):
    def test_reads_bathroom_boost_target(self):
        self.assertEqual(vtherm_preset_target(state(), "boost"), 21.5)

    def test_never_selects_hidden_or_unknown_preset(self):
        self.assertIsNone(vtherm_preset_target(state(), "away"))
        self.assertIsNone(vtherm_preset_target(state(), "none"))

    def test_declines_presence_window_and_unready_states(self):
        for attrs in (
            {"is_presence_configured": True},
            {"window_manager": {"window_state": "on"}},
            {"window_manager": {"window_state": "unavailable"}},
            {"is_ready": False},
            {"is_window_auto_configured": True},
            {"is_power_configured": True},
            {"safety_manager": {"safety_state": "on"}},
        ):
            with self.subTest(attrs=attrs):
                self.assertIsNone(vtherm_preset_target(state(**attrs), "boost"))

    def test_declines_invalid_target_and_non_vtherm(self):
        for attrs in (
            {"preset_temperatures": {"boost_temp": float("nan")}},
            {"preset_temperatures": {"boost_temp": 99}},
            {"preset_temperatures": {"boost_temp": True}},
            {"configuration": {"type": "unknown"}},
        ):
            with self.subTest(attrs=attrs):
                self.assertIsNone(vtherm_preset_target(state(**attrs), "boost"))

    def test_never_preheats_off_or_unknown_climate(self):
        entity = state()
        entity.state = "off"
        self.assertIsNone(vtherm_preset_target(entity, "boost"))
        self.assertIsNone(vtherm_preset_target(None, "boost"))
