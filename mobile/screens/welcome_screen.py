"""Welcome / Splash screen with glassmorphic aesthetics and backend health indicator."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from services.api_client import api_client
from widgets.glass_widgets import GlassCard, ModernButton


class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=[dp(20), dp(36), dp(20), dp(28)], spacing=dp(20))

        # Header with Logo & Brand
        brand_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(140), spacing=dp(8))

        logo_lbl = Label(
            text="💧  ⚡",
            font_size="44sp",
            size_hint_y=None,
            height=dp(52)
        )
        brand_box.add_widget(logo_lbl)

        title_lbl = Label(
            text="AquaWatt Tracker",
            font_size="26sp",
            bold=True,
            color=(0.96, 0.98, 1, 1),
            size_hint_y=None,
            height=dp(34)
        )
        brand_box.add_widget(title_lbl)

        tagline_lbl = Label(
            text="Urban Household Resource Tracking & Intelligence",
            font_size="13sp",
            color=(0.60, 0.72, 0.88, 1),
            size_hint_y=None,
            height=dp(20)
        )
        brand_box.add_widget(tagline_lbl)
        root.add_widget(brand_box)

        # Feature highlights inside GlassCard
        card = GlassCard(orientation="vertical", padding=dp(18), spacing=dp(14))

        info_title = Label(
            text="Phase 1: Consumption Foundations",
            font_size="15sp",
            bold=True,
            color=(0.02, 0.85, 0.95, 1),
            size_hint_y=None,
            height=dp(24),
            halign="left"
        )
        info_title.bind(size=info_title.setter("text_size"))
        card.add_widget(info_title)

        features = [
            ("⚡", "Electricity Tracking", "Log monthly kWh with granular appliance breakdown"),
            ("💧", "Water Footprint", "Record monthly litres with fixture & duration context"),
            ("🏠", "Household Profiling", "Normalize data by occupancy, house type & location"),
            ("🔒", "Secure Storage", "PostgreSQL persistence with encrypted authentication")
        ]

        for icon, feat_title, feat_desc in features:
            row = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(42))
            ic = Label(text=icon, font_size="18sp", size_hint_x=None, width=dp(28))
            desc_box = BoxLayout(orientation="vertical", spacing=dp(1))
            t = Label(text=feat_title, bold=True, font_size="13sp", color=(0.92, 0.95, 1, 1), halign="left")
            t.bind(size=t.setter("text_size"))
            d = Label(text=feat_desc, font_size="11sp", color=(0.58, 0.66, 0.78, 1), halign="left")
            d.bind(size=d.setter("text_size"))
            desc_box.add_widget(t)
            desc_box.add_widget(d)
            row.add_widget(ic)
            row.add_widget(desc_box)
            card.add_widget(row)

        root.add_widget(card)

        # Health status indicator
        self.health_lbl = Label(
            text="Checking backend status...",
            font_size="12sp",
            color=(0.7, 0.75, 0.85, 1),
            size_hint_y=None,
            height=dp(24)
        )
        root.add_widget(self.health_lbl)

        # Action Buttons
        btn_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(110), spacing=dp(12))

        btn_get_started = ModernButton(
            text="Get Started  →",
            style="primary",
            radius=14
        )
        btn_get_started.bind(on_release=lambda *a: self._go_register())
        btn_box.add_widget(btn_get_started)

        btn_login = ModernButton(
            text="Already have an account? Sign In",
            style="secondary",
            radius=14
        )
        btn_login.bind(on_release=lambda *a: self._go_login())
        btn_box.add_widget(btn_login)

        root.add_widget(btn_box)
        self.add_widget(root)

    def on_enter(self, *args):
        # Refresh health status when entering welcome screen
        healthy, msg = api_client.check_health()
        if healthy:
            self.health_lbl.text = "● Backend API: Online (PostgreSQL Connected)"
            self.health_lbl.color = (0.2, 0.85, 0.5, 1)
        else:
            self.health_lbl.text = "▲ Backend API: Offline (Run FastAPI backend)"
            self.health_lbl.color = (0.95, 0.6, 0.2, 1)

    def _go_register(self):
        self.manager.current = "register"

    def _go_login(self):
        self.manager.current = "login"
