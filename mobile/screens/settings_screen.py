"""
AquaWatt Settings & System Preferences Screen.
Smart Energy Control Center design featuring:
- Theme selection (Light Mode / Dark Mode) with instant reactive updates.
- Utility tariff configuration (Electricity ₹/kWh, Water ₹/L) affecting KPI cost calculations.
- Resident account information and household profile shortcuts.
- System diagnostics, backend API connection health monitoring, and version info.
"""

import threading
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from services.api_client import api_client
from services.theme_manager import theme_manager
from widgets.glass_widgets import (
    GlassButton,
    GlassCard,
    GlassHeader,
    GlassInput,
    GlassSidebar,
    Icon,
    LiquidGlassLayout,
    show_success_popup,
)


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()
        theme_manager.register_listener(self._on_theme_changed)

    def _on_theme_changed(self):
        saved_elec = self.input_elec_rate.text if hasattr(self, "input_elec_rate") else ""
        saved_water = self.input_water_rate.text if hasattr(self, "input_water_rate") else ""
        self._build_ui()
        if hasattr(self, "input_elec_rate") and saved_elec:
            self.input_elec_rate.text = saved_elec
        if hasattr(self, "input_water_rate") and saved_water:
            self.input_water_rate.text = saved_water
        self._check_backend_health()

    def _build_ui(self):
        self.clear_widgets()
        bg_layout = LiquidGlassLayout()

        # Main horizontal split: Sidebar on left + Content on right
        main_split = BoxLayout(orientation="horizontal")

        user_info = api_client.current_user or {}
        self.sidebar = GlassSidebar(
            active_screen="settings",
            on_navigate=self._navigate,
            on_sign_out=self._handle_sign_out,
            user_info=user_info
        )
        main_split.add_widget(self.sidebar)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.content_box = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(18), dp(22), dp(20)],
            spacing=dp(16),
            size_hint_y=None
        )
        self.content_box.bind(minimum_height=self.content_box.setter("height"))

        # 1. Header
        header = GlassHeader(
            title="Settings & Preferences",
            subtitle="Configure theme appearance, utility billing tariffs, and system diagnostics",
            on_back=lambda: self._navigate("dashboard")
        )
        self.content_box.add_widget(header)

        # 2. Section: Theme & Appearance Card
        theme_card = GlassCard(
            variant="default",
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint_y=None,
            radius=14
        )
        theme_card.bind(minimum_height=theme_card.setter("height"))

        h_theme = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26), spacing=dp(8))
        h_theme.add_widget(Icon(icon_name="palette-outline", font_size="18sp", color=theme_manager.get("brand_primary")))
        t_lbl = Label(
            text="Theme & Visual Appearance",
            bold=True,
            font_size="15sp",
            color=theme_manager.get("text_primary"),
            halign="left",
            valign="middle"
        )
        t_lbl.bind(size=t_lbl.setter("text_size"))
        h_theme.add_widget(t_lbl)
        theme_card.add_widget(h_theme)

        # Theme explanation text
        mode_str = "Dark Mode (Smart Energy Control Center High Contrast)" if theme_manager.is_dark else "Light Mode (Clean Modern SaaS)"
        lbl_current_mode = Label(
            text=f"Current theme: {mode_str}\nAquaWatt features complete dual-theme support with synchronized charts and control widgets.",
            font_size="12sp",
            color=theme_manager.get("text_secondary"),
            size_hint_y=None,
            height=dp(36),
            halign="left",
            valign="middle"
        )
        lbl_current_mode.bind(size=lbl_current_mode.setter("text_size"))
        theme_card.add_widget(lbl_current_mode)

        # Theme Switcher Action
        theme_action_box = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(42))
        tgl_btn = GlassButton(
            text="Switch to Light Mode" if theme_manager.is_dark else "Switch to Dark Mode",
            style="primary",
            radius=12
        )
        tgl_btn.bind(on_release=lambda *a: theme_manager.toggle_theme())
        theme_action_box.add_widget(tgl_btn)
        theme_card.add_widget(theme_action_box)

        self.content_box.add_widget(theme_card)

        # 3. Section: Utility Billing Tariffs
        tariff_card = GlassCard(
            variant="default",
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint_y=None,
            radius=14
        )
        tariff_card.bind(minimum_height=tariff_card.setter("height"))

        h_tariff = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26), spacing=dp(8))
        h_tariff.add_widget(Icon(icon_name="currency-inr", font_size="18sp", color=theme_manager.get("accent_amber")))
        t_tariff_lbl = Label(
            text="Utility Tariff Rates",
            bold=True,
            font_size="15sp",
            color=theme_manager.get("text_primary"),
            halign="left",
            valign="middle"
        )
        t_tariff_lbl.bind(size=t_tariff_lbl.setter("text_size"))
        h_tariff.add_widget(t_tariff_lbl)
        tariff_card.add_widget(h_tariff)

        lbl_tariff_info = Label(
            text="These utility rates are used to calculate the Estimated Electricity and Water Costs across all dashboard KPI cards.",
            font_size="12sp",
            color=theme_manager.get("text_secondary"),
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle"
        )
        lbl_tariff_info.bind(size=lbl_tariff_info.setter("text_size"))
        tariff_card.add_widget(lbl_tariff_info)

        # Tariff Input Row
        tariffs_row = BoxLayout(orientation="horizontal", spacing=dp(14), size_hint_y=None, height=dp(72))
        
        self.input_elec_rate = GlassInput(
            label_text="Electricity Tariff (₹ per kWh)",
            hint_text="10.00",
            icon_name="flash",
            default_val=str(theme_manager.electricity_tariff)
        )
        tariffs_row.add_widget(self.input_elec_rate)

        self.input_water_rate = GlassInput(
            label_text="Water Tariff (₹ per Litre)",
            hint_text="0.10",
            icon_name="water",
            default_val=str(theme_manager.water_tariff)
        )
        tariffs_row.add_widget(self.input_water_rate)
        tariff_card.add_widget(tariffs_row)

        # Tariff Save Button & Status Label
        save_tariff_box = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(42))
        self.btn_save_tariffs = GlassButton(
            text="Save Tariff Rates",
            style="elec",
            radius=12,
            size_hint_x=0.4
        )
        self.btn_save_tariffs.bind(on_release=self._handle_save_tariffs)
        save_tariff_box.add_widget(self.btn_save_tariffs)

        self.lbl_tariff_status = Label(
            text="",
            font_size="12sp",
            color=theme_manager.get("brand_primary"),
            size_hint_x=0.6,
            halign="left",
            valign="middle"
        )
        self.lbl_tariff_status.bind(size=self.lbl_tariff_status.setter("text_size"))
        save_tariff_box.add_widget(self.lbl_tariff_status)

        tariff_card.add_widget(save_tariff_box)
        self.content_box.add_widget(tariff_card)

        # 4. Section: Resident Account & Household Profile
        account_card = GlassCard(
            variant="default",
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint_y=None,
            radius=14
        )
        account_card.bind(minimum_height=account_card.setter("height"))

        h_acc = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26), spacing=dp(8))
        h_acc.add_widget(Icon(icon_name="account-circle-outline", font_size="18sp", color=theme_manager.get("accent_elec")))
        t_acc = Label(
            text="Resident Account & Household Context",
            bold=True,
            font_size="15sp",
            color=theme_manager.get("text_primary"),
            halign="left",
            valign="middle"
        )
        t_acc.bind(size=t_acc.setter("text_size"))
        h_acc.add_widget(t_acc)
        account_card.add_widget(h_acc)

        user_name = user_info.get("full_name") or user_info.get("email", "Resident")
        user_email = user_info.get("email", "user@example.com")
        self.lbl_user_details = Label(
            text=f"Logged in as: {user_name} ({user_email})\nJWT session authenticated against FastAPI PostgreSQL backend.",
            font_size="12sp",
            color=theme_manager.get("text_secondary"),
            size_hint_y=None,
            height=dp(36),
            halign="left",
            valign="middle"
        )
        self.lbl_user_details.bind(size=self.lbl_user_details.setter("text_size"))
        account_card.add_widget(self.lbl_user_details)

        acc_btn_box = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(42))
        btn_view_profile = GlassButton(
            text="Manage Household Profile",
            style="secondary",
            radius=12,
            size_hint_x=0.5
        )
        btn_view_profile.bind(on_release=lambda *a: self._navigate("profile"))
        acc_btn_box.add_widget(btn_view_profile)

        btn_sign_out = GlassButton(
            text="Sign Out",
            style="danger",
            radius=12,
            size_hint_x=0.5
        )
        btn_sign_out.bind(on_release=lambda *a: self._handle_sign_out())
        acc_btn_box.add_widget(btn_sign_out)

        account_card.add_widget(acc_btn_box)
        self.content_box.add_widget(account_card)

        # 5. Section: System Diagnostics & Health Status
        diag_card = GlassCard(
            variant="default",
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint_y=None,
            radius=14
        )
        diag_card.bind(minimum_height=diag_card.setter("height"))

        h_diag = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26), spacing=dp(8))
        h_diag.add_widget(Icon(icon_name="server-network", font_size="18sp", color=theme_manager.get("accent_water")))
        t_diag = Label(
            text="System Diagnostics & API Status",
            bold=True,
            font_size="15sp",
            color=theme_manager.get("text_primary"),
            halign="left",
            valign="middle"
        )
        t_diag.bind(size=t_diag.setter("text_size"))
        h_diag.add_widget(t_diag)
        diag_card.add_widget(h_diag)

        # Diagnostic items
        status_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(28))
        self.diag_dot = Icon(icon_name="circle", font_size="13sp", color=(0.85, 0.70, 0.20, 1), pos_hint={"center_y": 0.5})
        status_row.add_widget(self.diag_dot)
        self.diag_status_lbl = Label(
            text="Backend API (http://127.0.0.1:8000) • Checking...",
            font_size="12sp",
            color=theme_manager.get("text_secondary"),
            halign="left",
            valign="middle"
        )
        self.diag_status_lbl.bind(size=self.diag_status_lbl.setter("text_size"))
        status_row.add_widget(self.diag_status_lbl)
        diag_card.add_widget(status_row)

        info_lbl = Label(
            text="AquaWatt v2.4 (Option A — Smart Energy Control Center)\nFramework: Python 3.13 • Kivy 2.3.1 • KivyMD 2.0.0 • PostgreSQL • SQLAlchemy 2.0",
            font_size="11sp",
            color=theme_manager.get("text_muted"),
            size_hint_y=None,
            height=dp(34),
            halign="left",
            valign="middle"
        )
        info_lbl.bind(size=info_lbl.setter("text_size"))
        diag_card.add_widget(info_lbl)

        self.content_box.add_widget(diag_card)

        scroll.add_widget(self.content_box)
        main_split.add_widget(scroll)
        bg_layout.add_widget(main_split)
        self.add_widget(bg_layout)

    def on_pre_enter(self, *args):
        if hasattr(self, "sidebar"):
            self.sidebar.user_info = api_client.current_user or {}
            self.sidebar._build_sidebar()
        if hasattr(self, "lbl_user_details") and api_client.current_user:
            u = api_client.current_user
            name = u.get("full_name") or u.get("email", "Resident")
            email = u.get("email", "")
            self.lbl_user_details.text = f"Logged in as: {name} ({email})\nJWT session authenticated against FastAPI PostgreSQL backend."
        if hasattr(self, "input_elec_rate"):
            self.input_elec_rate.text = str(theme_manager.electricity_tariff)
        if hasattr(self, "input_water_rate"):
            self.input_water_rate.text = str(theme_manager.water_tariff)
        self._check_backend_health()

    def _handle_save_tariffs(self, *args):
        try:
            elec = float(self.input_elec_rate.text.strip())
            water = float(self.input_water_rate.text.strip())
            theme_manager.set_tariffs(elec, water)
            self.lbl_tariff_status.text = "✓ Tariffs saved and active!"
            Clock.schedule_once(lambda dt: setattr(self.lbl_tariff_status, "text", ""), 3.0)
            show_success_popup(
                title="Tariffs Updated",
                message=f"New utility tariff rates:\nElectricity: ₹{elec:.2f} / kWh\nWater: ₹{water:.2f} / L\nDashboard cost estimates updated.",
                on_continue=None
            )
        except ValueError:
            self.lbl_tariff_status.text = "Please enter valid numbers."

    def _check_backend_health(self):
        def _ping():
            healthy, msg = api_client.check_health()

            def _update_ui(dt):
                if hasattr(self, "diag_dot") and hasattr(self, "diag_status_lbl"):
                    if healthy:
                        self.diag_dot.color = (16 / 255, 185 / 255, 129 / 255, 1)  # Emerald green
                        self.diag_status_lbl.text = "Backend API (http://127.0.0.1:8000) • Connected & Operational"
                    else:
                        self.diag_dot.color = (239 / 255, 68 / 255, 68 / 255, 1)   # Red
                        self.diag_status_lbl.text = "Backend API (http://127.0.0.1:8000) • Offline or Unreachable"

            Clock.schedule_once(_update_ui)

        t = threading.Thread(target=_ping, daemon=True)
        t.start()

    def _handle_sign_out(self):
        api_client.logout()
        self.manager.current = "welcome"

    def _navigate(self, screen_name: str):
        self.manager.current = screen_name

