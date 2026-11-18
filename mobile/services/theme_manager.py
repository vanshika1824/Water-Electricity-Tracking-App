"""
AquaWatt Theme Manager.
Implements the Modern Professional Smart Energy Control Center design system
with complete Light Mode and Dark Mode palettes, immediate reactive switching, and persistence.
"""

import json
import os
import weakref
from typing import Any, Callable, Dict, List, Optional

# Ensure KIVY_HOME points to workspace .kivy before importing kivy modules
if "KIVY_HOME" not in os.environ:
    os.environ["KIVY_HOME"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".kivy"))

from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, StringProperty

PREF_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".theme_pref.json"))


class ThemeTokens:
    """Color token definitions for Smart Energy Control Center."""

    # -------------------------------------------------------------------------
    # DARK MODE (Primary Reference)
    # - Main background: #0B1220
    # - Sidebar: #111C2E
    # - Cards: #172438
    # - Card border: #1E2D44
    # - Electricity accent: #3B82F6 (Blue)
    # - Water accent: #14B8A6 (Teal)
    # - Green accent: #34D399 (Emerald)
    # - Purple accent: #8B5CF6 (Purple for electricity cost)
    # - Amber accent: #F59E0B (Amber for electricity usage icon)
    # - Main text: #F1F5F9
    # - Secondary text: #94A3B8
    # - Muted text: #64748B
    # -------------------------------------------------------------------------
    DARK: Dict[str, Any] = {
        # Surfaces & Backgrounds
        "bg_screen": (11 / 255, 18 / 255, 32 / 255, 1.0),            # #0B1220 Deep Space Navy
        "bg_screen_alt": (8 / 255, 14 / 26 / 255, 1.0),             # #080E1A
        "bg_sidebar": (17 / 255, 28 / 255, 46 / 255, 1.0),           # #111C2E Deep Sidebar Navy
        "bg_card": (23 / 255, 36 / 255, 56 / 255, 1.0),              # #172438 Card Panel
        "bg_card_elevated": (30 / 255, 47 / 255, 74 / 255, 1.0),     # #1E2F4A
        "bg_card_translucent": (23 / 255, 36 / 255, 56 / 255, 0.85),
        "bg_chip": (30 / 255, 45 / 255, 68 / 255, 0.80),
        
        # Borders & Dividers
        "border_card": (30 / 255, 45 / 255, 68 / 255, 1.0),          # #1E2D44 Subtle Slate Border
        "border_sidebar": (30 / 255, 45 / 255, 68 / 255, 1.0),       # #1E2D44
        "border_subtle": (25 / 255, 38 / 255, 58 / 255, 1.0),
        "border_focused": (52 / 255, 211 / 255, 153 / 255, 1.0),     # Emerald Focus #34D399

        # Typography
        "text_primary": (241 / 255, 245 / 255, 249 / 255, 1.0),      # #F1F5F9 Crisp Pure White
        "text_secondary": (148 / 255, 163 / 255, 184 / 255, 1.0),   # #94A3B8 Slate 400
        "text_muted": (100 / 255, 116 / 255, 139 / 255, 1.0),       # #64748B Slate 500
        "text_inverted": (15 / 255, 23 / 255, 42 / 255, 1.0),

        # Primary Brand Colors (Emerald Green)
        "brand_primary": (52 / 255, 211 / 255, 153 / 255, 1.0),      # #34D399 Emerald
        "brand_hover": (16 / 255, 185 / 255, 129 / 255, 1.0),
        "brand_surface": (16 / 255, 185 / 255, 129 / 255, 0.20),
        "brand_border": (52 / 255, 211 / 255, 153 / 255, 0.40),

        # Resource Domain Accents
        "accent_elec": (59 / 255, 130 / 255, 246 / 255, 1.0),        # #3B82F6 Blue
        "accent_elec_bg": (59 / 255, 130 / 255, 246 / 255, 0.20),
        "accent_elec_border": (59 / 255, 130 / 255, 246 / 255, 0.40),
        
        "accent_water": (20 / 255, 184 / 255, 166 / 255, 1.0),       # #14B8A6 Teal
        "accent_water_bg": (20 / 255, 184 / 255, 166 / 255, 0.20),
        "accent_water_border": (20 / 255, 184 / 255, 166 / 255, 0.40),

        "accent_cost_elec": (139 / 255, 92 / 255, 246 / 255, 1.0),   # #8B5CF6 Purple
        "accent_cost_elec_bg": (139 / 255, 92 / 255, 246 / 255, 0.20),

        "accent_amber": (245 / 255, 158 / 255, 11 / 255, 1.0),       # #F59E0B Amber
        "accent_amber_bg": (245 / 255, 158 / 255, 11 / 255, 0.20),

        "accent_danger": (239 / 255, 68 / 255, 68 / 255, 1.0),      # #EF4444 Red
        "accent_danger_bg": (239 / 255, 68 / 255, 68 / 255, 0.20),

        # Navigation & Sidebar
        "nav_active_pill": (16 / 255, 185 / 255, 129 / 255, 0.85),  # Emerald Pill
        "nav_active_text": (255 / 255, 255 / 255, 255 / 255, 1.0),
        "nav_inactive_text": (148 / 255, 163 / 255, 184 / 255, 1.0),
        "nav_hover_bg": (30 / 255, 45 / 255, 68 / 255, 0.60),

        # Form Controls
        "input_bg": (17 / 255, 28 / 255, 46 / 255, 1.0),             # #111C2E
        "input_border": (30 / 255, 45 / 255, 68 / 255, 1.0),
        "input_text": (241 / 255, 245 / 255, 249 / 255, 1.0),
        "input_hint": (100 / 255, 116 / 255, 139 / 255, 1.0),

        # Secondary & Utility Buttons
        "btn_secondary_bg": (30 / 255, 45 / 255, 68 / 255, 1.0),
        "btn_secondary_border": (45 / 255, 65 / 255, 95 / 255, 1.0),
        "btn_secondary_text": (241 / 255, 245 / 255, 249 / 255, 1.0),
        "shadow_color": (0, 0, 0, 0.35),
        "badge_bg": (30 / 255, 45 / 255, 68 / 255, 0.90),
    }

    # -------------------------------------------------------------------------
    # LIGHT MODE
    # - Main background: #F5F8FC
    # - Sidebar: #FFFFFF
    # - Cards: #FFFFFF
    # - Card border: #E2E8F0
    # - Electricity accent: #2563EB (Blue)
    # - Water accent: #0D9488 (Teal)
    # - Green accent: #059669 (Emerald)
    # - Purple accent: #7C3AED (Purple)
    # - Amber accent: #D97706 (Amber)
    # - Main text: #172033
    # - Secondary text: #64748B
    # - Muted text: #94A3B8
    # -------------------------------------------------------------------------
    LIGHT: Dict[str, Any] = {
        # Surfaces & Backgrounds
        "bg_screen": (245 / 255, 248 / 255, 252 / 255, 1.0),         # #F5F8FC Soft Light Canvas
        "bg_screen_alt": (238 / 255, 242 / 255, 248 / 255, 1.0),
        "bg_sidebar": (1.0, 1.0, 1.0, 1.0),                          # #FFFFFF Pure White
        "bg_card": (1.0, 1.0, 1.0, 1.0),                             # #FFFFFF Pure White
        "bg_card_elevated": (248 / 255, 250 / 255, 252 / 255, 1.0),  # #F8FAFC
        "bg_card_translucent": (1.0, 1.0, 1.0, 0.92),
        "bg_chip": (241 / 255, 245 / 255, 249 / 255, 1.0),
        
        # Borders & Dividers
        "border_card": (226 / 255, 232 / 255, 240 / 255, 1.0),       # #E2E8F0 Subtle Slate Border
        "border_sidebar": (226 / 255, 232 / 255, 240 / 255, 1.0),
        "border_subtle": (241 / 255, 245 / 255, 249 / 255, 1.0),
        "border_focused": (5 / 255, 150 / 255, 105 / 255, 1.0),      # #059669

        # Typography
        "text_primary": (23 / 255, 32 / 255, 51 / 255, 1.0),         # #172033 Dark Navy Text
        "text_secondary": (100 / 255, 116 / 255, 139 / 255, 1.0),   # #64748B Slate 500
        "text_muted": (148 / 255, 163 / 255, 184 / 255, 1.0),       # #94A3B8 Slate 400
        "text_inverted": (255 / 255, 255 / 255, 255 / 255, 1.0),

        # Primary Brand Colors (Emerald Green)
        "brand_primary": (5 / 255, 150 / 255, 105 / 255, 1.0),       # #059669 Emerald
        "brand_hover": (4 / 255, 120 / 255, 87 / 255, 1.0),
        "brand_surface": (209 / 255, 250 / 255, 229 / 255, 0.60),   # Light mint surface
        "brand_border": (110 / 255, 231 / 255, 183 / 255, 1.0),

        # Resource Domain Accents
        "accent_elec": (37 / 255, 99 / 255, 235 / 255, 1.0),         # #2563EB Blue
        "accent_elec_bg": (219 / 255, 234 / 255, 254 / 255, 0.70),  # Blue 100
        "accent_elec_border": (147 / 255, 197 / 255, 253 / 255, 0.80),

        "accent_water": (13 / 255, 148 / 255, 136 / 255, 1.0),       # #0D9488 Teal
        "accent_water_bg": (204 / 255, 251 / 255, 241 / 255, 0.70), # Teal 100
        "accent_water_border": (94 / 255, 234 / 255, 212 / 255, 0.80),

        "accent_cost_elec": (124 / 255, 58 / 255, 237 / 255, 1.0),   # #7C3AED Purple
        "accent_cost_elec_bg": (237 / 255, 233 / 255, 254 / 255, 0.70),

        "accent_amber": (217 / 255, 119 / 255, 6 / 255, 1.0),        # #D97706 Amber
        "accent_amber_bg": (254 / 255, 243 / 255, 199 / 255, 0.70),

        "accent_danger": (220 / 255, 38 / 255, 38 / 255, 1.0),      # #DC2626 Red
        "accent_danger_bg": (254 / 255, 226 / 255, 226 / 255, 0.70),

        # Navigation & Sidebar
        "nav_active_pill": (5 / 255, 150 / 255, 105 / 255, 1.0),     # Emerald Active Pill
        "nav_active_text": (255 / 255, 255 / 255, 255 / 255, 1.0),
        "nav_inactive_text": (71 / 255, 85 / 255, 105 / 255, 1.0),   # Slate 700
        "nav_hover_bg": (241 / 255, 245 / 255, 249 / 255, 1.0),

        # Form Controls
        "input_bg": (255 / 255, 255 / 255, 255 / 255, 1.0),
        "input_border": (203 / 255, 213 / 255, 225 / 255, 1.0),     # #CBD5E1
        "input_text": (23 / 255, 32 / 255, 51 / 255, 1.0),
        "input_hint": (148 / 255, 163 / 255, 184 / 255, 1.0),

        # Secondary & Utility Buttons
        "btn_secondary_bg": (241 / 255, 245 / 255, 249 / 255, 1.0),
        "btn_secondary_border": (226 / 255, 232 / 255, 240 / 255, 1.0),
        "btn_secondary_text": (23 / 255, 32 / 255, 51 / 255, 1.0),
        "shadow_color": (15 / 255, 23 / 255, 42 / 255, 0.05),
        "badge_bg": (241 / 255, 245 / 255, 249 / 255, 1.0),
    }


class ThemeManager(EventDispatcher):
    """
    Central Reactive Theme Manager.
    Coordinates color token resolution, in-app theme toggle, persistence,
    and instantaneous screen re-rendering.
    """
    theme_name = StringProperty("dark")
    is_dark = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._listeners: List[Callable[[], None]] = []
        self._weak_listeners: List[weakref.WeakMethod] = []
        self.electricity_tariff: float = 10.0  # ₹ / kWh
        self.water_tariff: float = 0.10        # ₹ / Litre
        self._load_preference()

    def _load_preference(self):
        """Load user's theme choice from persistent JSON, defaulting to 'dark' for the Control Center."""
        initial_theme = "dark"
        if os.path.exists(PREF_FILE):
            try:
                with open(PREF_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("theme") in ["light", "dark"]:
                        initial_theme = data.get("theme")
                    if "electricity_tariff" in data:
                        self.electricity_tariff = float(data["electricity_tariff"])
                    if "water_tariff" in data:
                        self.water_tariff = float(data["water_tariff"])
            except Exception:
                pass
        self.set_theme(initial_theme, save=False)

    def _save_preference(self):
        """Save theme preference and utility tariff rates to file."""
        try:
            with open(PREF_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "theme": self.theme_name,
                    "electricity_tariff": self.electricity_tariff,
                    "water_tariff": self.water_tariff,
                }, f, indent=2)
        except Exception:
            pass

    def set_tariffs(self, electricity_tariff: float, water_tariff: float):
        """Update utility tariff rates and persist preferences."""
        self.electricity_tariff = max(0.1, float(electricity_tariff))
        self.water_tariff = max(0.01, float(water_tariff))
        self._save_preference()
        self._notify_listeners()

    def set_theme(self, name: str, save: bool = True):
        """Set active theme to 'light' or 'dark'."""
        if name not in ["light", "dark"]:
            name = "dark"
        self.theme_name = name
        self.is_dark = (name == "dark")

        # Update Window clear color
        try:
            Window.clearcolor = self.get("bg_screen")
        except Exception:
            pass

        if save:
            self._save_preference()

        # Notify all registered screen listeners
        self._notify_listeners()

    def set_mode(self, name: str, save: bool = True):
        """Alias for set_theme."""
        self.set_theme(name, save=save)

    @property
    def mode(self) -> str:
        """Alias for theme_name."""
        return self.theme_name

    def toggle_theme(self):
        """Toggle between Light and Dark mode."""
        new_theme = "light" if self.is_dark else "dark"
        self.set_theme(new_theme)

    def register_listener(self, callback: Callable[[], None]):
        """Register a screen or component callback to be executed on theme switch."""
        if hasattr(callback, "__self__") and callback.__self__ is not None:
            # Bound method - store weakly so destroyed widgets are automatically garbage collected
            try:
                for existing in self._weak_listeners:
                    if existing() == callback:
                        return
                self._weak_listeners.append(weakref.WeakMethod(callback))
                return
            except TypeError:
                pass
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[], None]):
        """Remove a previously registered listener."""
        if hasattr(callback, "__self__"):
            self._weak_listeners = [wm for wm in self._weak_listeners if wm() is not None and wm() != callback]
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self):
        alive_weak = []
        for wm in self._weak_listeners:
            cb = wm()
            if cb is not None:
                alive_weak.append(wm)
                try:
                    cb()
                except Exception:
                    pass
        self._weak_listeners = alive_weak

        for cb in list(self._listeners):
            try:
                cb()
            except Exception:
                pass

    def get(self, token_name: str, fallback=(1, 1, 1, 1)) -> Any:
        """Retrieve color token for the currently active theme."""
        palette = ThemeTokens.DARK if self.is_dark else ThemeTokens.LIGHT
        return palette.get(token_name, fallback)

    # -------------------------------------------------------------------------
    # Convenience properties for common tokens
    # -------------------------------------------------------------------------
    @property
    def bg_screen(self): return self.get("bg_screen")
    @property
    def bg_card(self): return self.get("bg_card")
    @property
    def bg_card_elevated(self): return self.get("bg_card_elevated")
    @property
    def border_card(self): return self.get("border_card")
    @property
    def text_primary(self): return self.get("text_primary")
    @property
    def text_secondary(self): return self.get("text_secondary")
    @property
    def text_muted(self): return self.get("text_muted")
    @property
    def brand_primary(self): return self.get("brand_primary")
    @property
    def brand_hover(self): return self.get("brand_hover")
    @property
    def brand_surface(self): return self.get("brand_surface")
    @property
    def accent_water(self): return self.get("accent_water")
    @property
    def accent_water_bg(self): return self.get("accent_water_bg")
    @property
    def accent_elec(self): return self.get("accent_elec")
    @property
    def accent_elec_bg(self): return self.get("accent_elec_bg")
    @property
    def bg_sidebar(self): return self.get("bg_sidebar")
    @property
    def nav_active_pill(self): return self.get("nav_active_pill")
    @property
    def nav_active_text(self): return self.get("nav_active_text")
    @property
    def nav_inactive_text(self): return self.get("nav_inactive_text")
    @property
    def input_bg(self): return self.get("input_bg")
    @property
    def input_border(self): return self.get("input_border")
    @property
    def input_text(self): return self.get("input_text")
    @property
    def input_hint(self): return self.get("input_hint")
    @property
    def shadow_color(self): return self.get("shadow_color")
    @property
    def btn_secondary_bg(self): return self.get("btn_secondary_bg")
    @property
    def btn_secondary_text(self): return self.get("btn_secondary_text")


# Singleton instance shared across the entire mobile application
theme_manager = ThemeManager()
