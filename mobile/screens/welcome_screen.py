"""
AquaWatt Welcome / Splash Screen.
Modern Professional (Option A) design featuring:
- Responsive Emerald branding and droplet logo.
- Feature highlight cards adapting seamlessly to Light and Dark mode.
- Live backend connection diagnostic badge.
- High-contrast 'Sign In' and 'Create Account' action buttons.
- Header with direct Theme Toggle control.
"""

import os
import threading
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from services.api_client import api_client
from services.theme_manager import theme_manager
from widgets.glass_widgets import (
    LOGO_DROPLET_PATH,
    GlassButton,
    GlassCard,
    Icon,
    LiquidGlassLayout,
)


class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()
        theme_manager.register_listener(self._on_theme_changed)

    def _build_ui(self):
        self.clear_widgets()
        self.bg_layout = LiquidGlassLayout()

        # Top Bar with Theme Toggle
        top_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            padding=[dp(20), dp(8), dp(20), dp(4)]
        )
        top_bar.add_widget(BoxLayout(size_hint_x=1))  # Spacer

        is_dark = theme_manager.is_dark
        self.theme_chip = BoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            size_hint=(None, None),
            size=(dp(124), dp(34)),
            padding=[dp(10), 0, dp(10), 0]
        )
        self.theme_chip.bind(pos=self._update_theme_chip_bg, size=self._update_theme_chip_bg)
        t_icon_name = "weather-sunny" if not is_dark else "weather-night"
        self.theme_ic = Icon(icon_name=t_icon_name, font_size="16sp", color=theme_manager.get("text_primary"))
        self.theme_lbl = Label(
            text="Light Mode" if not is_dark else "Dark Mode",
            font_size="12sp",
            bold=True,
            color=theme_manager.get("text_primary"),
            valign="middle"
        )
        self.theme_lbl.bind(size=self.theme_lbl.setter("text_size"))
        self.theme_chip.add_widget(self.theme_ic)
        self.theme_chip.add_widget(self.theme_lbl)

        btn_tgl_click = Button(background_normal="", background_color=(0, 0, 0, 0), size_hint=(1, 1))
        btn_tgl_click.bind(on_release=lambda *a: theme_manager.toggle_theme())
        self.theme_chip.add_widget(btn_tgl_click)
        top_bar.add_widget(self.theme_chip)

        main_col = BoxLayout(orientation="vertical")
        main_col.add_widget(top_bar)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        center_box = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(10), dp(20), dp(24)],
            spacing=dp(14),
            size_hint=(None, None),
            width=dp(430)
        )
        center_box.bind(minimum_height=center_box.setter("height"))

        # 1. Header with Logo & Brand
        brand_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(135), spacing=dp(4))

        if os.path.exists(LOGO_DROPLET_PATH):
            logo_img = KivyImage(
                source=LOGO_DROPLET_PATH,
                size_hint=(None, None),
                size=(dp(58), dp(58)),
                pos_hint={"center_x": 0.5}
            )
            brand_box.add_widget(logo_img)

        self.title_lbl = Label(
            text="AquaWatt",
            font_size="27sp",
            bold=True,
            color=theme_manager.get("text_primary"),
            size_hint_y=None,
            height=dp(34),
            halign="center",
            valign="middle"
        )
        self.title_lbl.bind(size=self.title_lbl.setter("text_size"))
        brand_box.add_widget(self.title_lbl)

        self.tagline_lbl = Label(
            text="Track smarter. Save every drop and watt.",
            font_size="13sp",
            color=theme_manager.get("text_secondary"),
            size_hint_y=None,
            height=dp(20),
            halign="center",
            valign="middle"
        )
        self.tagline_lbl.bind(size=self.tagline_lbl.setter("text_size"))
        brand_box.add_widget(self.tagline_lbl)
        center_box.add_widget(brand_box)

        # 2. Four Feature Cards
        features = [
            ("flash", "Track Electricity", "Monitor your monthly kWh and appliance usage patterns.", "elec"),
            ("water", "Track Water", "Log consumption and understand daily per-person litres.", "water"),
            ("home-outline", "Household Management", "Keep your household profile and demographics up to date.", "default"),
            ("shield-check-outline", "Secure & Private", "Protected with industry-standard bcrypt and JWT tokens.", "default"),
        ]

        self.feature_cards = []
        for icon, feat_title, feat_desc, variant in features:
            pill = GlassCard(
                variant="elevated",
                orientation="horizontal",
                padding=[dp(14), dp(10), dp(14), dp(10)],
                spacing=dp(12),
                size_hint_y=None,
                height=dp(56),
                radius=14
            )

            # Icon circle badge
            badge_color = (
                theme_manager.get("accent_elec") if variant == "elec"
                else (theme_manager.get("accent_water") if variant == "water" else theme_manager.get("brand_primary"))
            )
            badge = Icon(
                icon_name=icon,
                font_size="20sp",
                color=badge_color,
                pos_hint={"center_y": 0.5}
            )
            pill.add_widget(badge)

            # Text block
            text_box = BoxLayout(orientation="vertical", spacing=dp(1))
            h_lbl = Label(
                text=feat_title,
                bold=True,
                font_size="13sp",
                color=theme_manager.get("text_primary"),
                halign="left",
                valign="middle"
            )
            h_lbl.bind(size=h_lbl.setter("text_size"))
            text_box.add_widget(h_lbl)

            d_lbl = Label(
                text=feat_desc,
                font_size="11sp",
                color=theme_manager.get("text_secondary"),
                halign="left",
                valign="middle"
            )
            d_lbl.bind(size=d_lbl.setter("text_size"))
            text_box.add_widget(d_lbl)
            pill.add_widget(text_box)

            center_box.add_widget(pill)
            self.feature_cards.append((pill, h_lbl, d_lbl, badge, variant))

        # 3. Backend Health Status Badge
        self.health_card = GlassCard(
            variant="default",
            orientation="horizontal",
            padding=[dp(14), dp(8), dp(14), dp(8)],
            spacing=dp(10),
            size_hint_y=None,
            height=dp(42),
            radius=12
        )
        self.health_dot = Icon(
            icon_name="circle",
            font_size="13sp",
            color=(0.85, 0.70, 0.20, 1),
            pos_hint={"center_y": 0.5}
        )
        self.health_lbl = Label(
            text="Checking backend connection...",
            font_size="12sp",
            color=theme_manager.get("text_secondary"),
            halign="left",
            valign="middle"
        )
        self.health_lbl.bind(size=self.health_lbl.setter("text_size"))
        self.health_card.add_widget(self.health_dot)
        self.health_card.add_widget(self.health_lbl)
        center_box.add_widget(self.health_card)

        # 4. Action Buttons
        btn_box = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, height=dp(98))

        btn_signin = GlassButton(
            text="Sign In",
            style="primary",
            height=dp(44),
            radius=22
        )
        btn_signin.bind(on_release=lambda *a: self._navigate("login"))
        btn_box.add_widget(btn_signin)

        btn_register = GlassButton(
            text="Create Account",
            style="secondary",
            height=dp(42),
            radius=21
        )
        btn_register.bind(on_release=lambda *a: self._navigate("register"))
        btn_box.add_widget(btn_register)

        center_box.add_widget(btn_box)

        # Outer centering container
        outer = BoxLayout(orientation="horizontal")
        outer.add_widget(BoxLayout(size_hint_x=1))
        outer.add_widget(center_box)
        outer.add_widget(BoxLayout(size_hint_x=1))

        scroll.add_widget(outer)
        main_col.add_widget(scroll)
        self.bg_layout.add_widget(main_col)
        self.add_widget(self.bg_layout)

    def _update_theme_chip_bg(self, inst, *args):
        inst.canvas.before.clear()
        with inst.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(*theme_manager.get("bg_card_elevated"))
            RoundedRectangle(pos=inst.pos, size=inst.size, radius=[(dp(17), dp(17))] * 4)
            Color(*theme_manager.get("border_card"))
            Line(rounded_rectangle=(inst.x, inst.y, inst.width, inst.height, dp(17)), width=1.0)

    def _on_theme_changed(self):
        self._build_ui()
        self._check_backend_health()

    def on_enter(self, *args):
        self._check_backend_health()

    def _check_backend_health(self):
        def _ping():
            healthy, msg = api_client.check_health()

            def _update_ui(dt):
                if hasattr(self, "health_dot") and hasattr(self, "health_lbl"):
                    if healthy:
                        self.health_dot.color = (16 / 255, 185 / 255, 129 / 255, 1)  # Emerald green
                        self.health_lbl.text = "Backend Connected • All systems operational"
                    else:
                        self.health_dot.color = (239 / 255, 68 / 255, 68 / 255, 1)   # Rose red
                        self.health_lbl.text = "Backend Offline • Verify port 8000 is active"

            Clock.schedule_once(_update_ui)

        t = threading.Thread(target=_ping, daemon=True)
        t.start()

    def _navigate(self, screen_name: str):
        self.manager.current = screen_name
