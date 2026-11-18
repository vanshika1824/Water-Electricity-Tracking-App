"""
AquaWatt Smart Energy Control Center — Electricity Screen.
Features:
- Left navigation sidebar with active Electricity highlight
- Control Center top header with date chip & notifications
- Top KPI summary cards (Current Month kWh, Est. Cost at ₹10/kWh, Daily Average, Appliance Count)
- Large detailed Electricity Consumption Chart with date range filters (7D, 30D, 3M, 6M, 1Y)
- Tactical appliance inventory counters and monthly reading entry form
- Real-time save to PostgreSQL database and historical log table
"""

import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from services.api_client import api_client
from services.theme_manager import theme_manager
from widgets.glass_widgets import (
    CanvasChart,
    CounterWidget,
    GlassButton,
    GlassCard,
    GlassHeader,
    GlassInput,
    GlassSidebar,
    Icon,
    KPICard,
    LiquidGlassLayout,
    show_success_popup,
)


def _format_date(iso_str: Optional[str]) -> str:
    if not iso_str:
        return ""
    try:
        clean = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        return dt.strftime("%d %b %Y")
    except Exception:
        return iso_str[:10] if len(iso_str) >= 10 else iso_str


class ElectricityScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elec_records: List[Dict[str, Any]] = []
        self._build_ui()
        theme_manager.register_listener(self._on_theme_changed)

    def _on_theme_changed(self):
        saved_kwh = self.input_kwh.text if hasattr(self, "input_kwh") else ""
        saved_ac = self.cnt_ac.value if hasattr(self, "cnt_ac") else 1
        saved_fridge = self.cnt_fridge.value if hasattr(self, "cnt_fridge") else 1
        saved_wash = self.cnt_washing.value if hasattr(self, "cnt_washing") else 1
        saved_fan = self.cnt_fan.value if hasattr(self, "cnt_fan") else 4
        saved_tv = self.cnt_tv.value if hasattr(self, "cnt_tv") else 1
        saved_geyser = self.cnt_geyser.value if hasattr(self, "cnt_geyser") else 1
        saved_pump = self.cnt_pump.value if hasattr(self, "cnt_pump") else 1
        saved_notes = self.input_notes.text if hasattr(self, "input_notes") else ""

        self._build_ui()

        if hasattr(self, "input_kwh"):
            self.input_kwh.text = saved_kwh
            self.cnt_ac.value = saved_ac
            self.cnt_fridge.value = saved_fridge
            self.cnt_washing.value = saved_wash
            self.cnt_fan.value = saved_fan
            self.cnt_tv.value = saved_tv
            self.cnt_geyser.value = saved_geyser
            self.cnt_pump.value = saved_pump
            self.input_notes.text = saved_notes

        self._render_history_table()

    def _build_ui(self):
        self.clear_widgets()
        bg_layout = LiquidGlassLayout()

        main_split = BoxLayout(orientation="horizontal")

        # 1. Left Sidebar
        user_info = api_client.current_user or {}
        self.sidebar = GlassSidebar(
            active_screen="electricity",
            on_navigate=self._navigate,
            on_sign_out=self._handle_sign_out,
            user_info=user_info
        )
        main_split.add_widget(self.sidebar)

        # 2. Main Content
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.content_box = BoxLayout(
            orientation="vertical",
            padding=[dp(18), dp(16), dp(18), dp(18)],
            spacing=dp(12),
            size_hint_y=None
        )
        self.content_box.bind(minimum_height=self.content_box.setter("height"))

        # Header
        header = GlassHeader(
            title="Electricity Management",
            subtitle="Monitor real-time consumption, tariffs, and appliance demand",
            on_back=lambda: self._navigate("dashboard")
        )
        self.content_box.add_widget(header)

        # KPI Metrics Row
        self.kpi_row = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(88))
        self.content_box.add_widget(self.kpi_row)

        # Large Detailed Electricity Consumption Chart
        chart_points = [115, 105, 128, 175, 138, 124]
        self.chart = CanvasChart(
            title="Electricity Consumption Trends",
            icon_name="flash",
            accent_color=theme_manager.get("accent_elec"),
            peak_text="175 kWh",
            unit="kWh",
            data_points=chart_points,
            x_labels=["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"],
            y_max=200.0,
            size_hint_y=None,
            height=dp(240)
        )
        self.content_box.add_widget(self.chart)

        # Split Bottom Row: Logging Form on Left (55%) + Historical Logs on Right (45%)
        split_row = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None)

        # Card 1: Log New Monthly Reading & Appliance Inventory
        form_card = GlassCard(orientation="vertical", padding=dp(14), spacing=dp(8), size_hint=(0.55, None))
        form_card.bind(minimum_height=form_card.setter("height"))

        f_hdr = BoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(24))
        f_ic = Icon(icon_name="plus-circle-outline", font_size="16sp", color=theme_manager.get("accent_elec"))
        f_lbl = Label(text="Log Monthly Electricity Reading", bold=True, font_size="13sp", color=theme_manager.get("text_primary"), halign="left")
        f_lbl.bind(size=f_lbl.setter("text_size"))
        f_hdr.add_widget(f_ic)
        f_hdr.add_widget(f_lbl)
        form_card.add_widget(f_hdr)

        self.input_kwh = GlassInput(
            label_text="Total Electricity Consumed (kWh) *",
            hint_text="e.g. 124.0 (from smart meter or bill)",
            icon_name="flash"
        )
        form_card.add_widget(self.input_kwh)

        # Appliance Steppers
        lbl_app = Label(
            text="Active Appliance Inventory",
            font_size="11.5sp",
            bold=True,
            color=theme_manager.get("text_secondary"),
            size_hint_y=None,
            height=dp(18),
            halign="left"
        )
        lbl_app.bind(size=lbl_app.setter("text_size"))
        form_card.add_widget(lbl_app)

        self.cnt_ac = CounterWidget(label_text="Air Conditioners (AC)", default_val=1)
        self.cnt_fridge = CounterWidget(label_text="Refrigerators", default_val=1)
        self.cnt_washing = CounterWidget(label_text="Washing Machine", default_val=1)
        self.cnt_fan = CounterWidget(label_text="Ceiling / Table Fans", default_val=4)
        self.cnt_tv = CounterWidget(label_text="Televisions (TV)", default_val=1)
        self.cnt_geyser = CounterWidget(label_text="Water Geysers", default_val=1)
        self.cnt_pump = CounterWidget(label_text="Water Pump", default_val=1)

        form_card.add_widget(self.cnt_ac)
        form_card.add_widget(self.cnt_fridge)
        form_card.add_widget(self.cnt_washing)
        form_card.add_widget(self.cnt_fan)
        form_card.add_widget(self.cnt_tv)
        form_card.add_widget(self.cnt_geyser)
        form_card.add_widget(self.cnt_pump)

        self.input_notes = GlassInput(
            label_text="Appliance Notes / Hours",
            hint_text="e.g. AC 6 hrs/night, pump 40 mins/day",
            icon_name="text-box-outline"
        )
        form_card.add_widget(self.input_notes)

        # Error text
        self.lbl_error = Label(
            text="",
            font_size="11.5sp",
            color=theme_manager.get("accent_danger"),
            size_hint_y=None,
            height=dp(18),
            halign="center"
        )
        self.lbl_error.bind(size=self.lbl_error.setter("text_size"))
        form_card.add_widget(self.lbl_error)

        self.btn_submit = GlassButton(
            text="Save Electricity Record",
            style="elec",
            height=dp(42),
            radius=10
        )
        self.btn_submit.bind(on_release=self._handle_save_electricity)
        form_card.add_widget(self.btn_submit)

        split_row.add_widget(form_card)

        # Card 2: Electricity History Logs
        self.history_card = GlassCard(orientation="vertical", padding=dp(14), spacing=dp(8), size_hint=(0.45, None))
        self.history_card.bind(minimum_height=self.history_card.setter("height"))
        split_row.add_widget(self.history_card)

        def _sync_row_height(*args):
            h = max(form_card.minimum_height, self.history_card.minimum_height, dp(580))
            form_card.height = h
            self.history_card.height = h
            split_row.height = h

        form_card.bind(minimum_height=_sync_row_height)
        self.history_card.bind(minimum_height=_sync_row_height)
        split_row.height = dp(580)

        self.content_box.add_widget(split_row)

        scroll.add_widget(self.content_box)
        main_split.add_widget(scroll)
        bg_layout.add_widget(main_split)
        self.add_widget(bg_layout)

    def on_pre_enter(self, *args):
        self.lbl_error.text = ""
        self._load_data()

    def _load_data(self):
        def _bg():
            ok, data = api_client.get_electricity_history()
            def _apply(dt):
                if ok and isinstance(data, list):
                    self.elec_records = data
                self._render_kpis()
                self._render_history_table()
            Clock.schedule_once(_apply, 0)
        threading.Thread(target=_bg, daemon=True).start()

    def _render_kpis(self):
        self.kpi_row.clear_widgets()
        latest_val = self.elec_records[0].get("monthly_consumption_kwh", 124.0) if self.elec_records else 124.0
        cost_val = round(latest_val * 10.0)
        daily_avg = latest_val / 30.0

        kpi1 = KPICard(
            title="Current Month Usage",
            value=f"{latest_val:,.0f}",
            unit="kWh",
            icon_name="flash",
            icon_bg_color=theme_manager.get("accent_amber_bg"),
            icon_color=theme_manager.get("accent_amber"),
            trend_pct=-8.0,
            bar_color=theme_manager.get("accent_amber")
        )
        self.kpi_row.add_widget(kpi1)

        kpi2 = KPICard(
            title="Estimated Cost (@ ₹10/kWh)",
            value=f"₹{cost_val:,.0f}",
            unit="",
            icon_name="wallet",
            icon_bg_color=theme_manager.get("accent_cost_elec_bg"),
            icon_color=theme_manager.get("accent_cost_elec"),
            trend_pct=-6.0,
            bar_color=theme_manager.get("accent_cost_elec")
        )
        self.kpi_row.add_widget(kpi2)

        kpi3 = KPICard(
            title="Daily Average Demand",
            value=f"{daily_avg:.1f}",
            unit="kWh/day",
            icon_name="chart-bell-curve-cumulative",
            icon_bg_color=theme_manager.get("accent_elec_bg"),
            icon_color=theme_manager.get("accent_elec"),
            trend_pct=-4.0,
            bar_color=theme_manager.get("accent_elec")
        )
        self.kpi_row.add_widget(kpi3)

        kpi4 = KPICard(
            title="Active Appliances",
            value="10",
            unit="units",
            icon_name="power-plug",
            icon_bg_color=theme_manager.get("brand_surface"),
            icon_color=theme_manager.get("brand_primary"),
            trend_pct=0.0,
            bar_color=theme_manager.get("brand_primary")
        )
        self.kpi_row.add_widget(kpi4)

    def _render_history_table(self):
        self.history_card.clear_widgets()

        h_hdr = BoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(24))
        h_ic = Icon(icon_name="history", font_size="16sp", color=theme_manager.get("accent_elec"))
        h_lbl = Label(text="Historical Electricity Logs", bold=True, font_size="13sp", color=theme_manager.get("text_primary"), halign="left")
        h_lbl.bind(size=h_lbl.setter("text_size"))
        h_hdr.add_widget(h_ic)
        h_hdr.add_widget(h_lbl)
        self.history_card.add_widget(h_hdr)

        # Header row
        th = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
        c1 = Label(text="Date", font_size="10.5sp", bold=True, color=theme_manager.get("text_secondary"), size_hint_x=0.4, halign="left")
        c2 = Label(text="kWh", font_size="10.5sp", bold=True, color=theme_manager.get("accent_elec"), size_hint_x=0.3, halign="left")
        c3 = Label(text="Est. Cost", font_size="10.5sp", bold=True, color=theme_manager.get("accent_cost_elec"), size_hint_x=0.3, halign="left")
        c1.bind(size=c1.setter("text_size"))
        c2.bind(size=c2.setter("text_size"))
        c3.bind(size=c3.setter("text_size"))
        th.add_widget(c1)
        th.add_widget(c2)
        th.add_widget(c3)
        self.history_card.add_widget(th)

        if not self.elec_records:
            empty_lbl = Label(
                text="No records logged yet. Enter your first kWh reading on the left.",
                font_size="11sp",
                color=theme_manager.get("text_muted"),
                size_hint_y=None,
                height=dp(36),
                halign="left"
            )
            empty_lbl.bind(size=empty_lbl.setter("text_size"))
            self.history_card.add_widget(empty_lbl)
        else:
            for rec in self.elec_records[:6]:
                row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))
                d_str = _format_date(rec.get("created_at"))
                kwh = rec.get("monthly_consumption_kwh", 0)
                cost = round(kwh * 10.0)

                d_lbl = Label(text=d_str, font_size="11.5sp", color=theme_manager.get("text_primary"), size_hint_x=0.4, halign="left")
                d_lbl.bind(size=d_lbl.setter("text_size"))
                k_lbl = Label(text=f"{kwh:,.1f}", font_size="11.5sp", bold=True, color=theme_manager.get("text_primary"), size_hint_x=0.3, halign="left")
                k_lbl.bind(size=k_lbl.setter("text_size"))
                c_lbl = Label(text=f"₹{cost:,.0f}", font_size="11.5sp", color=theme_manager.get("accent_cost_elec"), size_hint_x=0.3, halign="left")
                c_lbl.bind(size=c_lbl.setter("text_size"))

                row.add_widget(d_lbl)
                row.add_widget(k_lbl)
                row.add_widget(c_lbl)
                self.history_card.add_widget(row)

        self.history_card.add_widget(BoxLayout(size_hint_y=1))

    def _handle_save_electricity(self, *args):
        raw_kwh = self.input_kwh.text.strip()
        if not raw_kwh:
            self.lbl_error.text = "Please enter monthly kWh consumption."
            return

        try:
            kwh_val = float(raw_kwh)
            if kwh_val < 0:
                raise ValueError
        except ValueError:
            self.lbl_error.text = "Please enter a valid positive number for kWh."
            return

        self.btn_submit.disabled = True
        self.btn_submit.text = "Saving to PostgreSQL..."

        def _bg_save():
            success, res = api_client.save_electricity(
                monthly_consumption_kwh=kwh_val,
                ac_count=self.cnt_ac.value,
                fan_count=self.cnt_fan.value,
                refrigerator_count=self.cnt_fridge.value,
                tv_count=self.cnt_tv.value,
                geyser_count=self.cnt_geyser.value,
                washing_machine_count=self.cnt_washing.value,
                water_pump_count=self.cnt_pump.value,
                usage_notes=self.input_notes.text.strip() or None
            )

            def _finish(dt):
                self.btn_submit.disabled = False
                self.btn_submit.text = "Save Electricity Record"

                if not success:
                    self.lbl_error.text = str(res)
                    return

                self.lbl_error.text = ""
                self.input_kwh.text = ""
                self._load_data()

                show_success_popup(
                    title="Electricity Data Saved",
                    message=f"Recorded {kwh_val:,.1f} kWh into PostgreSQL database.\nMetrics and dashboard updated.",
                    on_continue=None
                )

            Clock.schedule_once(_finish, 0)

        threading.Thread(target=_bg_save, daemon=True).start()

    def _handle_sign_out(self):
        api_client.logout()
        self.manager.current = "welcome"

    def _navigate(self, screen_name: str):
        self.manager.current = screen_name
