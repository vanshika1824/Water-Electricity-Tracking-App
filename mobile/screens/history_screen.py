"""
AquaWatt Smart Energy Control Center — Consumption History Screen.
Features:
- Left navigation sidebar with active History highlight
- Top header with search bar and resource filter pills (All, Electricity, Water)
- Professional data table displaying Date, Resource type, Consumption, Est. Cost, and Metadata
- Quick action shortcuts to log new readings
- Full theme switching responsiveness and robust empty states
"""

import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from services.api_client import api_client
from services.theme_manager import theme_manager
from widgets.glass_widgets import (
    GlassButton,
    GlassCard,
    GlassHeader,
    GlassSidebar,
    Icon,
    LiquidGlassLayout,
)


def _format_date(iso_str: Optional[str]) -> str:
    if not iso_str:
        return "Unknown Date"
    try:
        clean = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        return dt.strftime("%d %b %Y")
    except Exception:
        return iso_str[:10] if len(iso_str) >= 10 else iso_str


class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active_filter = "All"
        self.search_query = ""
        self.elec_records: List[Dict[str, Any]] = []
        self.water_records: List[Dict[str, Any]] = []
        self._build_ui()
        theme_manager.register_listener(self._on_theme_changed)

    def _on_theme_changed(self):
        self._build_ui()
        self._render_records()

    def _build_ui(self):
        self.clear_widgets()
        bg_layout = LiquidGlassLayout()

        main_split = BoxLayout(orientation="horizontal")

        # 1. Left Sidebar
        user_info = api_client.current_user or {}
        self.sidebar = GlassSidebar(
            active_screen="history",
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
            title="Consumption Audit Log",
            subtitle="Search, filter, and inspect verified historical utility meter entries",
            on_back=lambda: self._navigate("dashboard")
        )
        self.content_box.add_widget(header)

        # Filter & Search Action Bar
        action_bar = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(38))

        # Search Input
        search_box = BoxLayout(
            orientation="horizontal",
            size_hint_x=0.45,
            padding=[dp(10), 0, dp(10), 0],
            spacing=dp(6)
        )
        search_box.bind(
            pos=lambda inst, *a: self._style_input(inst),
            size=lambda inst, *a: self._style_input(inst)
        )
        s_ic = Icon(icon_name="magnify", font_size="16sp", color=theme_manager.get("text_muted"))
        self.txt_search = TextInput(
            text=self.search_query,
            hint_text="Search logs by note or month...",
            multiline=False,
            font_size="12sp",
            cursor_color=theme_manager.get("brand_primary"),
            foreground_color=theme_manager.get("text_primary"),
            hint_text_color=theme_manager.get("text_muted"),
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            padding=[0, dp(10), 0, dp(10)]
        )
        self.txt_search.bind(text=self._on_search_text)
        search_box.add_widget(s_ic)
        search_box.add_widget(self.txt_search)
        action_bar.add_widget(search_box)

        # Filter Pills: All, Electricity, Water
        pill_row = BoxLayout(orientation="horizontal", spacing=dp(6), size_hint_x=0.55)

        self.btn_f_all = GlassButton(text="All Records", style="primary" if self.active_filter == "All" else "secondary", radius=8, height=dp(36))
        self.btn_f_elec = GlassButton(text="Electricity", style="elec" if self.active_filter == "Electricity" else "secondary", radius=8, height=dp(36))
        self.btn_f_water = GlassButton(text="Water", style="water" if self.active_filter == "Water" else "secondary", radius=8, height=dp(36))

        self.btn_f_all.bind(on_release=lambda *a: self._set_filter("All"))
        self.btn_f_elec.bind(on_release=lambda *a: self._set_filter("Electricity"))
        self.btn_f_water.bind(on_release=lambda *a: self._set_filter("Water"))

        pill_row.add_widget(self.btn_f_all)
        pill_row.add_widget(self.btn_f_elec)
        pill_row.add_widget(self.btn_f_water)
        action_bar.add_widget(pill_row)

        self.content_box.add_widget(action_bar)

        # Table Container
        self.table_card = GlassCard(orientation="vertical", padding=dp(16), spacing=dp(8), size_hint_y=None)
        self.table_card.bind(minimum_height=self.table_card.setter("height"))
        self.content_box.add_widget(self.table_card)

        scroll.add_widget(self.content_box)
        main_split.add_widget(scroll)
        bg_layout.add_widget(main_split)
        self.add_widget(bg_layout)

    def _style_input(self, inst):
        inst.canvas.before.clear()
        with inst.canvas.before:
            Color(*theme_manager.get("input_bg"))
            RoundedRectangle(pos=inst.pos, size=inst.size, radius=[(dp(8), dp(8))] * 4)
            Color(*theme_manager.get("border_card"))
            Line(rounded_rectangle=(inst.x, inst.y, inst.width, inst.height, dp(8)), width=0.8)

    def _on_search_text(self, inst, val):
        self.search_query = val.strip().lower()
        self._render_records()

    def on_pre_enter(self, *args):
        self.refresh_history()

    def refresh_history(self):
        def _bg():
            ok_e, data_e = api_client.get_electricity_history()
            ok_w, data_w = api_client.get_water_history()

            def _apply(dt):
                if ok_e and isinstance(data_e, list):
                    self.elec_records = data_e
                if ok_w and isinstance(data_w, list):
                    self.water_records = data_w
                self._render_records()

            Clock.schedule_once(_apply, 0)

        threading.Thread(target=_bg, daemon=True).start()

    def _set_filter(self, filter_name: str):
        self.active_filter = filter_name
        self.btn_f_all.style = "primary" if filter_name == "All" else "secondary"
        self.btn_f_all._update_bg()
        self.btn_f_elec.style = "elec" if filter_name == "Electricity" else "secondary"
        self.btn_f_elec._update_bg()
        self.btn_f_water.style = "water" if filter_name == "Water" else "secondary"
        self.btn_f_water._update_bg()
        self._render_records()

    def _render_records(self):
        self.table_card.clear_widgets()

        # Table Header
        th = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26), padding=[dp(8), 0, dp(8), 0])
        th.bind(
            pos=lambda inst, *a: self._style_th(inst),
            size=lambda inst, *a: self._style_th(inst)
        )
        h1 = Label(text="Date Logged", font_size="11sp", bold=True, color=theme_manager.get("text_secondary"), size_hint_x=0.25, halign="left")
        h2 = Label(text="Resource", font_size="11sp", bold=True, color=theme_manager.get("text_secondary"), size_hint_x=0.20, halign="left")
        h3 = Label(text="Consumption", font_size="11sp", bold=True, color=theme_manager.get("text_secondary"), size_hint_x=0.22, halign="left")
        h4 = Label(text="Est. Cost (₹)", font_size="11sp", bold=True, color=theme_manager.get("text_secondary"), size_hint_x=0.18, halign="left")
        h5 = Label(text="Notes / Details", font_size="11sp", bold=True, color=theme_manager.get("text_secondary"), size_hint_x=0.15, halign="left")
        for h in [h1, h2, h3, h4, h5]:
            h.bind(size=h.setter("text_size"))
            th.add_widget(h)
        self.table_card.add_widget(th)

        # Merge rows
        rows = []
        if self.active_filter in ("All", "Electricity"):
            for rec in self.elec_records:
                notes = rec.get("usage_notes") or ""
                date_str = _format_date(rec.get("created_at"))
                if self.search_query and (self.search_query not in notes.lower() and self.search_query not in date_str.lower()):
                    continue
                kwh = rec.get("monthly_consumption_kwh", 0)
                rows.append({
                    "date": date_str,
                    "created_at": rec.get("created_at", ""),
                    "type": "Electricity",
                    "val_str": f"{kwh:,.1f} kWh",
                    "cost_str": f"₹{round(kwh * 10.0):,.0f}",
                    "notes": notes or f"ACs: {rec.get('ac_count', 0)}, Fans: {rec.get('fan_count', 0)}",
                    "color": theme_manager.get("accent_elec"),
                    "icon": "flash"
                })

        if self.active_filter in ("All", "Water"):
            for rec in self.water_records:
                notes = rec.get("washing_machine_usage") or ""
                date_str = _format_date(rec.get("created_at"))
                if self.search_query and (self.search_query not in notes.lower() and self.search_query not in date_str.lower()):
                    continue
                litres = rec.get("monthly_consumption_litres", 0)
                rows.append({
                    "date": date_str,
                    "created_at": rec.get("created_at", ""),
                    "type": "Water",
                    "val_str": f"{litres:,.0f} L",
                    "cost_str": f"₹{round(litres * 0.10):,.0f}",
                    "notes": notes or f"Showers: {rec.get('num_showers', 0)}/day",
                    "color": theme_manager.get("accent_water"),
                    "icon": "water"
                })

        # Sort descending by created_at
        rows.sort(key=lambda r: r["created_at"], reverse=True)

        if not rows:
            empty_box = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None, height=dp(100), padding=dp(16))
            e_lbl = Label(
                text="No consumption logs found matching your filter/search criteria.",
                font_size="12sp",
                color=theme_manager.get("text_muted"),
                halign="center"
            )
            empty_box.add_widget(e_lbl)

            btn_row = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint=(None, None), size=(dp(280), dp(36)), pos_hint={"center_x": 0.5})
            btn_e = GlassButton(text="+ Log Electricity", style="elec", radius=8, height=dp(34), on_release=lambda *a: self._navigate("electricity"))
            btn_w = GlassButton(text="+ Log Water", style="water", radius=8, height=dp(34), on_release=lambda *a: self._navigate("water"))
            btn_row.add_widget(btn_e)
            btn_row.add_widget(btn_w)
            empty_box.add_widget(btn_row)
            self.table_card.add_widget(empty_box)
            return

        for idx, item in enumerate(rows):
            r_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(38), padding=[dp(8), 0, dp(8), 0])
            if idx % 2 == 1:
                r_box.bind(
                    pos=lambda inst, *a: self._style_zebra(inst),
                    size=lambda inst, *a: self._style_zebra(inst)
                )

            d_lbl = Label(text=item["date"], font_size="12sp", color=theme_manager.get("text_primary"), size_hint_x=0.25, halign="left")
            d_lbl.bind(size=d_lbl.setter("text_size"))

            # Type badge with icon
            type_box = BoxLayout(orientation="horizontal", spacing=dp(4), size_hint_x=0.20)
            t_ic = Icon(icon_name=item["icon"], font_size="14sp", color=item["color"])
            t_lbl = Label(text=item["type"], font_size="12sp", bold=True, color=item["color"], halign="left")
            t_lbl.bind(size=t_lbl.setter("text_size"))
            type_box.add_widget(t_ic)
            type_box.add_widget(t_lbl)

            v_lbl = Label(text=item["val_str"], font_size="12sp", bold=True, color=theme_manager.get("text_primary"), size_hint_x=0.22, halign="left")
            v_lbl.bind(size=v_lbl.setter("text_size"))

            c_lbl = Label(text=item["cost_str"], font_size="12sp", color=theme_manager.get("brand_primary"), size_hint_x=0.18, halign="left")
            c_lbl.bind(size=c_lbl.setter("text_size"))

            n_lbl = Label(text=item["notes"][:28], font_size="10.5sp", color=theme_manager.get("text_muted"), size_hint_x=0.15, halign="left")
            n_lbl.bind(size=n_lbl.setter("text_size"))

            r_box.add_widget(d_lbl)
            r_box.add_widget(type_box)
            r_box.add_widget(v_lbl)
            r_box.add_widget(c_lbl)
            r_box.add_widget(n_lbl)
            self.table_card.add_widget(r_box)

    def _style_th(self, inst):
        inst.canvas.before.clear()
        with inst.canvas.before:
            Color(*theme_manager.get("bg_chip"))
            RoundedRectangle(pos=inst.pos, size=inst.size, radius=[(dp(6), dp(6))] * 4)

    def _style_zebra(self, inst):
        inst.canvas.before.clear()
        with inst.canvas.before:
            Color(*theme_manager.get("bg_screen"))
            Rectangle(pos=inst.pos, size=inst.size)

    def _handle_sign_out(self):
        api_client.logout()
        self.manager.current = "welcome"

    def _navigate(self, screen_name: str):
        self.manager.current = screen_name
