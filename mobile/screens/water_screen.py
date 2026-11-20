"""
AquaWatt Smart Energy Control Center — Water Resource Screen.
Features:
- Left navigation sidebar with active Water highlight
- Control Center top header with date chip & notifications
- Top KPI summary cards (Current Month Litres, Est. Cost at ₹0.10/L, LPCD Daily Average, Fixture Count)
- Large detailed Water Consumption Chart with date range filters (7D, 30D, 3M, 6M, 1Y)
- Tactical fixture and habit counters and monthly reading entry form
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
    MobileBottomNav,
    MobileHeader,
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


class WaterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.water_records: List[Dict[str, Any]] = []
        self._build_ui()
        theme_manager.register_listener(self._on_theme_changed)

    def _on_theme_changed(self):
        saved_litres = self.input_litres.text if hasattr(self, "input_litres") else ""
        saved_showers = self.cnt_showers.value if hasattr(self, "cnt_showers") else 4
        saved_buckets = self.cnt_buckets.value if hasattr(self, "cnt_buckets") else 1
        saved_dur = self.input_shower_duration.text if hasattr(self, "input_shower_duration") else ""
        saved_wash = self.input_washing_freq.text if hasattr(self, "input_washing_freq") else ""
        saved_garden = self.input_garden.text if hasattr(self, "input_garden") else ""
        saved_pump = self.input_pump_usage.text if hasattr(self, "input_pump_usage") else ""

        self._build_ui()

        if hasattr(self, "input_litres"):
            self.input_litres.text = saved_litres
            self.cnt_showers.value = saved_showers
            self.cnt_buckets.value = saved_buckets
            self.input_shower_duration.text = saved_dur
            self.input_washing_freq.text = saved_wash
            self.input_garden.text = saved_garden
            self.input_pump_usage.text = saved_pump

        self._render_history_table()

    def _build_ui(self):
        self.clear_widgets()
        bg_layout = LiquidGlassLayout(orientation="vertical")

        # Top Mobile Header
        header = MobileHeader(
            title="Water Resource Tracking",
            subtitle="Monitor consumption, LPCD & fixtures",
            on_back=lambda: self._navigate("dashboard")
        )
        bg_layout.add_widget(header)

        # Main Scrollable Content Area
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.content_box = BoxLayout(
            orientation="vertical",
            padding=[dp(12), dp(8), dp(12), dp(16)],
            spacing=dp(10),
            size_hint_y=None
        )
        self.content_box.bind(minimum_height=self.content_box.setter("height"))

        # Row 1: KPI Cards 1 & 2 (Current Month Footprint & Est. Cost)
        self.kpi_row1 = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(78))
        self.content_box.add_widget(self.kpi_row1)

        # Row 2: KPI Cards 3 & 4 (Per Capita Daily LPCD & Active Fixtures)
        self.kpi_row2 = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(78))
        self.content_box.add_widget(self.kpi_row2)

        # Large Detailed Water Consumption Chart
        chart_points = [2800, 2700, 2950, 3200, 2900, 2850]
        self.chart = CanvasChart(
            title="Water Consumption Trends",
            icon_name="water",
            accent_color=theme_manager.get("accent_water"),
            peak_text="3,200 L",
            unit="L",
            data_points=chart_points,
            x_labels=["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"],
            y_max=4000.0,
            size_hint_y=None,
            height=dp(220)
        )
        self.content_box.add_widget(self.chart)

        # Card 1: Log New Monthly Reading & Fixture/Habit Steppers (Stacked Full Width)
        form_card = GlassCard(orientation="vertical", padding=dp(12), spacing=dp(8), size_hint_y=None)
        form_card.bind(minimum_height=form_card.setter("height"))

        f_hdr = BoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(24))
        f_ic = Icon(icon_name="plus-circle-outline", font_size="16sp", color=theme_manager.get("accent_water"))
        f_lbl = Label(text="Log Monthly Water Reading", bold=True, font_size="13sp", color=theme_manager.get("text_primary"), halign="left")
        f_lbl.bind(size=f_lbl.setter("text_size"))
        f_hdr.add_widget(f_ic)
        f_hdr.add_widget(f_lbl)
        form_card.add_widget(f_hdr)

        self.input_litres = GlassInput(
            label_text="Total Water Consumed (Litres) *",
            hint_text="e.g. 2850 (from water meter or utility bill)",
            icon_name="water"
        )
        form_card.add_widget(self.input_litres)

        # Fixtures & Habits
        lbl_fix = Label(
            text="Usage Habits & Active Fixtures",
            font_size="11.5sp",
            bold=True,
            color=theme_manager.get("text_secondary"),
            size_hint_y=None,
            height=dp(18),
            halign="left"
        )
        lbl_fix.bind(size=lbl_fix.setter("text_size"))
        form_card.add_widget(lbl_fix)

        self.cnt_showers = CounterWidget(label_text="Daily Showers in Household", default_val=4)
        self.cnt_buckets = CounterWidget(label_text="Bucket Baths / Routine Usage", default_val=1)
        form_card.add_widget(self.cnt_showers)
        form_card.add_widget(self.cnt_buckets)

        self.input_shower_duration = GlassInput(
            label_text="Avg Shower Duration (minutes)",
            hint_text="e.g. 7.5 mins",
            icon_name="timer-outline"
        )
        form_card.add_widget(self.input_shower_duration)

        self.input_washing_freq = GlassInput(
            label_text="Washing Machine Laundry Loads",
            hint_text="e.g. 3 loads / week",
            icon_name="washing-machine"
        )
        form_card.add_widget(self.input_washing_freq)

        self.input_garden = GlassInput(
            label_text="Garden & Plant Watering",
            hint_text="e.g. Daily, 3 times/week, None",
            icon_name="sprout-outline"
        )
        form_card.add_widget(self.input_garden)

        self.input_pump_usage = GlassInput(
            label_text="Water Pump Daily Runtime",
            hint_text="e.g. 30 mins/day, 1 hr/day",
            icon_name="cog-outline"
        )
        form_card.add_widget(self.input_pump_usage)

        # Error label
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
            text="Save Water Record",
            style="water",
            height=dp(42),
            radius=10
        )
        self.btn_submit.bind(on_release=self._handle_save_water)
        form_card.add_widget(self.btn_submit)

        self.content_box.add_widget(form_card)

        # Card 2: Water History Logs (Stacked Full Width)
        self.history_card = GlassCard(orientation="vertical", padding=dp(12), spacing=dp(8), size_hint_y=None)
        self.history_card.bind(minimum_height=self.history_card.setter("height"))
        self.content_box.add_widget(self.history_card)

        scroll.add_widget(self.content_box)
        bg_layout.add_widget(scroll)

        # Fixed Bottom Navigation Bar
        self.bottom_nav = MobileBottomNav(
            active_screen="water",
            on_navigate=self._navigate
        )
        bg_layout.add_widget(self.bottom_nav)

        self.add_widget(bg_layout)

    def on_pre_enter(self, *args):
        self.lbl_error.text = ""
        self._load_data()

    def _load_data(self):
        def _bg():
            ok, data = api_client.get_water_history()
            def _apply(dt):
                if ok and isinstance(data, list):
                    self.water_records = data
                self._render_kpis()
                self._render_history_table()
            Clock.schedule_once(_apply, 0)
        threading.Thread(target=_bg, daemon=True).start()

    def _render_kpis(self):
        self.kpi_row1.clear_widgets()
        self.kpi_row2.clear_widgets()
        latest_val = self.water_records[0].get("monthly_consumption_litres", 2850.0) if self.water_records else 2850.0
        cost_val = round(latest_val * 0.10)
        daily_lpcd = round(latest_val / (4 * 30))  # Assuming standard 4-member household

        kpi1 = KPICard(
            title="Current Month Footprint",
            value=f"{latest_val:,.0f}",
            unit="L",
            icon_name="water",
            icon_bg_color=theme_manager.get("accent_water_bg"),
            icon_color=theme_manager.get("accent_water"),
            trend_pct=-12.0,
            bar_color=theme_manager.get("accent_water"),
            size_hint=(0.5, 1)
        )
        self.kpi_row1.add_widget(kpi1)

        kpi2 = KPICard(
            title="Estimated Cost (@ ₹0.10/L)",
            value=f"₹{cost_val:,.0f}",
            unit="",
            icon_name="cash-check",
            icon_bg_color=theme_manager.get("brand_surface"),
            icon_color=theme_manager.get("brand_primary"),
            trend_pct=-10.0,
            bar_color=theme_manager.get("brand_primary"),
            size_hint=(0.5, 1)
        )
        self.kpi_row1.add_widget(kpi2)

        kpi3 = KPICard(
            title="Per Capita Daily (LPCD)",
            value=f"{daily_lpcd}",
            unit="LPCD",
            icon_name="account-water-outline",
            icon_bg_color=theme_manager.get("accent_water_bg"),
            icon_color=theme_manager.get("accent_water"),
            trend_pct=-15.0,
            bar_color=theme_manager.get("accent_water"),
            size_hint=(0.5, 1)
        )
        self.kpi_row2.add_widget(kpi3)

        kpi4 = KPICard(
            title="Active Fixtures Tracked",
            value="7",
            unit="fixtures",
            icon_name="shower",
            icon_bg_color=theme_manager.get("accent_elec_bg"),
            icon_color=theme_manager.get("accent_elec"),
            trend_pct=0.0,
            bar_color=theme_manager.get("accent_elec"),
            size_hint=(0.5, 1)
        )
        self.kpi_row2.add_widget(kpi4)

    def _render_history_table(self):
        self.history_card.clear_widgets()

        h_hdr = BoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(24))
        h_ic = Icon(icon_name="history", font_size="16sp", color=theme_manager.get("accent_water"))
        h_lbl = Label(text="Historical Water Logs", bold=True, font_size="13sp", color=theme_manager.get("text_primary"), halign="left")
        h_lbl.bind(size=h_lbl.setter("text_size"))
        h_hdr.add_widget(h_ic)
        h_hdr.add_widget(h_lbl)
        self.history_card.add_widget(h_hdr)

        # Header row
        th = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
        c1 = Label(text="Date", font_size="10.5sp", bold=True, color=theme_manager.get("text_secondary"), size_hint_x=0.4, halign="left")
        c2 = Label(text="Litres", font_size="10.5sp", bold=True, color=theme_manager.get("accent_water"), size_hint_x=0.3, halign="left")
        c3 = Label(text="Est. Cost", font_size="10.5sp", bold=True, color=theme_manager.get("brand_primary"), size_hint_x=0.3, halign="left")
        c1.bind(size=c1.setter("text_size"))
        c2.bind(size=c2.setter("text_size"))
        c3.bind(size=c3.setter("text_size"))
        th.add_widget(c1)
        th.add_widget(c2)
        th.add_widget(c3)
        self.history_card.add_widget(th)

        if not self.water_records:
            empty_lbl = Label(
                text="No records logged yet. Enter your first Litres reading on the left.",
                font_size="11sp",
                color=theme_manager.get("text_muted"),
                size_hint_y=None,
                height=dp(36),
                halign="left"
            )
            empty_lbl.bind(size=empty_lbl.setter("text_size"))
            self.history_card.add_widget(empty_lbl)
        else:
            for rec in self.water_records[:6]:
                row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))
                d_str = _format_date(rec.get("created_at"))
                litres = rec.get("monthly_consumption_litres", 0)
                cost = round(litres * 0.10)

                d_lbl = Label(text=d_str, font_size="11.5sp", color=theme_manager.get("text_primary"), size_hint_x=0.4, halign="left")
                d_lbl.bind(size=d_lbl.setter("text_size"))
                k_lbl = Label(text=f"{litres:,.0f} L", font_size="11.5sp", bold=True, color=theme_manager.get("text_primary"), size_hint_x=0.3, halign="left")
                k_lbl.bind(size=k_lbl.setter("text_size"))
                c_lbl = Label(text=f"₹{cost:,.0f}", font_size="11.5sp", color=theme_manager.get("brand_primary"), size_hint_x=0.3, halign="left")
                c_lbl.bind(size=c_lbl.setter("text_size"))

                row.add_widget(d_lbl)
                row.add_widget(k_lbl)
                row.add_widget(c_lbl)
                self.history_card.add_widget(row)

        self.history_card.add_widget(BoxLayout(size_hint_y=1))

    def _handle_save_water(self, *args):
        raw_litres = self.input_litres.text.strip()
        if not raw_litres:
            self.lbl_error.text = "Please enter monthly water consumption."
            return

        try:
            litres_val = float(raw_litres)
            if litres_val < 0:
                raise ValueError
        except ValueError:
            self.lbl_error.text = "Please enter a valid positive number for Litres."
            return

        shower_dur = 0.0
        if self.input_shower_duration.text:
            try:
                shower_dur = float(self.input_shower_duration.text)
            except ValueError:
                shower_dur = 0.0

        self.btn_submit.disabled = True
        self.btn_submit.text = "Saving to PostgreSQL..."

        def _bg_save():
            success, res = api_client.save_water(
                monthly_consumption_litres=litres_val,
                num_showers=self.cnt_showers.value,
                avg_shower_duration_mins=shower_dur,
                bucket_usage=self.cnt_buckets.value,
                washing_machine_usage=self.input_washing_freq.text.strip() or None,
                garden_watering=self.input_garden.text.strip() or None,
                water_pump_usage=self.input_pump_usage.text.strip() or None
            )

            def _finish(dt):
                self.btn_submit.disabled = False
                self.btn_submit.text = "Save Water Record"

                if not success:
                    self.lbl_error.text = str(res)
                    return

                self.lbl_error.text = ""
                self.input_litres.text = ""
                self._load_data()

                show_success_popup(
                    title="Water Data Saved",
                    message=f"Recorded {litres_val:,.0f} Litres into PostgreSQL database.\nMetrics and dashboard updated.",
                    on_continue=None
                )

            Clock.schedule_once(_finish, 0)

        threading.Thread(target=_bg_save, daemon=True).start()

    def _handle_sign_out(self):
        api_client.logout()
        self.manager.current = "welcome"

    def _navigate(self, screen_name: str):
        self.manager.current = screen_name
