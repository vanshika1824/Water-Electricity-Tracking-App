"""Electricity Consumption Screen for recording monthly kWh and appliance inventory."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from services.api_client import api_client
from widgets.glass_widgets import (
    CounterWidget,
    GlassCard,
    GlassHeader,
    GlassInput,
    ModernButton,
    show_success_popup,
)


class ElectricityScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=[dp(20), dp(16), dp(20), dp(20)], spacing=dp(12))

        # Header with Electricity amber/purple identity
        header = GlassHeader(
            title="Electricity Tracker",
            subtitle="Step 2 of 3: Monthly Power & Appliance Inventory",
            accent_color=(0.98, 0.70, 0.10, 1),
            on_back=self._handle_back
        )
        root.add_widget(header)

        # Scrollable form container
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        form_layout = BoxLayout(orientation="vertical", spacing=dp(16), size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter("height"))

        # Section 1: Monthly Total Consumption (Hero Card)
        card_hero = GlassCard(
            orientation="vertical",
            bg_color=(0.14, 0.11, 0.24, 0.88),  # subtle electric purple hue
            border_color=(0.98, 0.70, 0.10, 0.35),
            padding=dp(18),
            spacing=dp(12),
            size_hint_y=None
        )
        card_hero.bind(minimum_height=card_hero.setter("height"))

        hero_badge = Label(
            text="⚡ Monthly Power Billing",
            font_size="15sp",
            bold=True,
            color=(0.98, 0.72, 0.12, 1),
            size_hint_y=None,
            height=dp(24),
            halign="left"
        )
        hero_badge.bind(size=hero_badge.setter("text_size"))
        card_hero.add_widget(hero_badge)

        self.input_kwh = GlassInput(
            label_text="Monthly Electricity Consumption (kWh) *",
            hint_text="e.g. 280.5",
            input_filter="float"
        )
        card_hero.add_widget(self.input_kwh)

        helper_hint = Label(
            text="Found on your electricity bill (Units consumed in the latest month)",
            font_size="11sp",
            color=(0.75, 0.75, 0.85, 0.9),
            size_hint_y=None,
            height=dp(18),
            halign="left"
        )
        helper_hint.bind(size=helper_hint.setter("text_size"))
        card_hero.add_widget(helper_hint)

        form_layout.add_widget(card_hero)

        # Section 2: Appliance Inventory
        card_appliances = GlassCard(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint_y=None
        )
        card_appliances.bind(minimum_height=card_appliances.setter("height"))

        app_title = Label(
            text="🔌 Appliance Inventory & Context",
            font_size="15sp",
            bold=True,
            color=(0.85, 0.70, 0.98, 1),
            size_hint_y=None,
            height=dp(24),
            halign="left"
        )
        app_title.bind(size=app_title.setter("text_size"))
        card_appliances.add_widget(app_title)

        # Counters for standard household appliances
        self.cnt_ac = CounterWidget(label_text="Air Conditioners (AC)", default_val=1, min_val=0)
        self.cnt_fan = CounterWidget(label_text="Fans (Ceiling / Table)", default_val=4, min_val=0)
        self.cnt_fridge = CounterWidget(label_text="Refrigerators", default_val=1, min_val=0)
        self.cnt_tv = CounterWidget(label_text="Televisions", default_val=1, min_val=0)
        self.cnt_geyser = CounterWidget(label_text="Water Geysers / Heaters", default_val=1, min_val=0)
        self.cnt_washing = CounterWidget(label_text="Washing Machine", default_val=1, min_val=0)
        self.cnt_pump = CounterWidget(label_text="Electric Water Pump", default_val=1, min_val=0)

        card_appliances.add_widget(self.cnt_ac)
        card_appliances.add_widget(self.cnt_fan)
        card_appliances.add_widget(self.cnt_fridge)
        card_appliances.add_widget(self.cnt_tv)
        card_appliances.add_widget(self.cnt_geyser)
        card_appliances.add_widget(self.cnt_washing)
        card_appliances.add_widget(self.cnt_pump)

        # Other appliances & Usage notes
        self.input_other_app = GlassInput(
            label_text="Other High-Load Appliances",
            hint_text="e.g. Microwave, Induction, Desktop PC"
        )
        card_appliances.add_widget(self.input_other_app)

        self.input_usage_notes = GlassInput(
            label_text="Approximate Usage Notes (Optional)",
            hint_text="e.g. AC used ~6 hrs/night in summers"
        )
        card_appliances.add_widget(self.input_usage_notes)

        form_layout.add_widget(card_appliances)

        # Error notification
        self.lbl_error = Label(
            text="",
            color=(0.95, 0.35, 0.42, 1),
            font_size="13sp",
            size_hint_y=None,
            height=dp(26),
            halign="center"
        )
        self.lbl_error.bind(size=self.lbl_error.setter("text_size"))
        form_layout.add_widget(self.lbl_error)

        # Action Buttons
        nav_buttons = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(48))

        btn_back = ModernButton(
            text="← Back",
            style="secondary",
            size_hint_x=0.35,
            radius=12
        )
        btn_back.bind(on_release=lambda *a: self._handle_back())
        nav_buttons.add_widget(btn_back)

        self.btn_submit = ModernButton(
            text="Save & Proceed to Water Form  →",
            style="electric",
            size_hint_x=0.65,
            radius=12
        )
        self.btn_submit.bind(on_release=self._handle_save_electricity)
        nav_buttons.add_widget(self.btn_submit)

        form_layout.add_widget(nav_buttons)

        scroll.add_widget(form_layout)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.lbl_error.text = ""

    def _handle_save_electricity(self, *args):
        kwh_str = self.input_kwh.text
        if not kwh_str:
            self.lbl_error.text = "Please enter your monthly electricity consumption (kWh)."
            return

        try:
            kwh_val = float(kwh_str)
            if kwh_val < 0:
                raise ValueError()
        except ValueError:
            self.lbl_error.text = "Please enter a valid non-negative number for kWh."
            return

        self.btn_submit.disabled = True
        self.btn_submit.text = "Saving to PostgreSQL..."

        success, res = api_client.save_electricity(
            monthly_consumption_kwh=kwh_val,
            ac_count=self.cnt_ac.value,
            fan_count=self.cnt_fan.value,
            refrigerator_count=self.cnt_fridge.value,
            tv_count=self.cnt_tv.value,
            geyser_count=self.cnt_geyser.value,
            washing_machine_count=self.cnt_washing.value,
            water_pump_count=self.cnt_pump.value,
            other_appliances=self.input_other_app.text or None,
            usage_notes=self.input_usage_notes.text or None
        )

        self.btn_submit.disabled = False
        self.btn_submit.text = "Save & Proceed to Water Form  →"

        if not success:
            self.lbl_error.text = str(res)
            return

        # Show success modal then navigate to Water screen
        show_success_popup(
            title="Electricity Data Saved",
            message=f"Recorded {kwh_val:.1f} kWh into PostgreSQL.\nProceeding to Water Consumption.",
            on_continue=lambda: self._navigate("water")
        )

    def _handle_back(self):
        self.manager.current = "profile"

    def _navigate(self, screen_name: str):
        self.manager.current = screen_name
