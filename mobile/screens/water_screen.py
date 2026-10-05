"""Water Consumption Screen for tracking monthly litres and household water usage habits."""

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


class WaterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=[dp(20), dp(16), dp(20), dp(20)], spacing=dp(12))

        # Header with Water Cyan/Blue identity
        header = GlassHeader(
            title="Water Tracker",
            subtitle="Step 3 of 3: Monthly Volume & Fixture Usage",
            accent_color=(0.02, 0.85, 0.95, 1),
            on_back=self._handle_back
        )
        root.add_widget(header)

        # Scrollable form container
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        form_layout = BoxLayout(orientation="vertical", spacing=dp(16), size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter("height"))

        # Section 1: Monthly Total Water (Hero Card)
        card_hero = GlassCard(
            orientation="vertical",
            bg_color=(0.08, 0.16, 0.26, 0.88),  # subtle aqua-blue hue
            border_color=(0.02, 0.85, 0.95, 0.35),
            padding=dp(18),
            spacing=dp(12),
            size_hint_y=None
        )
        card_hero.bind(minimum_height=card_hero.setter("height"))

        hero_badge = Label(
            text="💧 Monthly Water Meter / Supply",
            font_size="15sp",
            bold=True,
            color=(0.02, 0.85, 0.95, 1),
            size_hint_y=None,
            height=dp(24),
            halign="left"
        )
        hero_badge.bind(size=hero_badge.setter("text_size"))
        card_hero.add_widget(hero_badge)

        self.input_litres = GlassInput(
            label_text="Monthly Water Consumption (Litres) *",
            hint_text="e.g. 12000 (or ~400 L/day × 30)",
            input_filter="float"
        )
        card_hero.add_widget(self.input_litres)

        helper_hint = Label(
            text="From municipal water meter, tanker delivery, or daily estimation",
            font_size="11sp",
            color=(0.75, 0.85, 0.95, 0.9),
            size_hint_y=None,
            height=dp(18),
            halign="left"
        )
        helper_hint.bind(size=helper_hint.setter("text_size"))
        card_hero.add_widget(helper_hint)

        form_layout.add_widget(card_hero)

        # Section 2: Bathing & Daily Fixtures
        card_fixtures = GlassCard(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint_y=None
        )
        card_fixtures.bind(minimum_height=card_fixtures.setter("height"))

        sec2_title = Label(
            text="🚿 Bathing & Domestic Habits",
            font_size="15sp",
            bold=True,
            color=(0.02, 0.85, 0.95, 1),
            size_hint_y=None,
            height=dp(24),
            halign="left"
        )
        sec2_title.bind(size=sec2_title.setter("text_size"))
        card_fixtures.add_widget(sec2_title)

        self.cnt_showers = CounterWidget(label_text="Daily Showers (Total in house)", default_val=3, min_val=0)
        card_fixtures.add_widget(self.cnt_showers)

        self.input_shower_duration = GlassInput(
            label_text="Average Shower Duration (Minutes)",
            hint_text="e.g. 8.5",
            input_filter="float",
            default_val="8"
        )
        card_fixtures.add_widget(self.input_shower_duration)

        self.cnt_buckets = CounterWidget(label_text="Daily Bucket Baths / Usage", default_val=2, min_val=0)
        card_fixtures.add_widget(self.cnt_buckets)

        form_layout.add_widget(card_fixtures)

        # Section 3: Outdoor & Utility Usage
        card_utility = GlassCard(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint_y=None
        )
        card_utility.bind(minimum_height=card_utility.setter("height"))

        sec3_title = Label(
            text="🌿 Utility & Outdoor Operations",
            font_size="15sp",
            bold=True,
            color=(0.20, 0.90, 0.70, 1),
            size_hint_y=None,
            height=dp(24),
            halign="left"
        )
        sec3_title.bind(size=sec3_title.setter("text_size"))
        card_utility.add_widget(sec3_title)

        self.input_washing_freq = GlassInput(
            label_text="Washing Machine Frequency",
            hint_text="e.g. 3 cycles per week"
        )
        card_utility.add_widget(self.input_washing_freq)

        self.input_garden = GlassInput(
            label_text="Garden / Plants Watering",
            hint_text="e.g. Daily, Alternate days, None"
        )
        card_utility.add_widget(self.input_garden)

        self.input_vehicle = GlassInput(
            label_text="Vehicle Washing Frequency",
            hint_text="e.g. Once a week, Bi-weekly, None"
        )
        card_utility.add_widget(self.input_vehicle)

        self.input_pump_usage = GlassInput(
            label_text="Water Motor / Pump Runtime",
            hint_text="e.g. 30 mins per day"
        )
        card_utility.add_widget(self.input_pump_usage)

        self.input_other_water = GlassInput(
            label_text="Other Water Demands",
            hint_text="e.g. Air cooler filling, balcony wash"
        )
        card_utility.add_widget(self.input_other_water)

        form_layout.add_widget(card_utility)

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
            text="Save Water Data  ✓",
            style="primary",
            size_hint_x=0.65,
            radius=12
        )
        self.btn_submit.bind(on_release=self._handle_save_water)
        nav_buttons.add_widget(self.btn_submit)

        form_layout.add_widget(nav_buttons)

        scroll.add_widget(form_layout)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.lbl_error.text = ""

    def _handle_save_water(self, *args):
        litres_str = self.input_litres.text
        if not litres_str:
            self.lbl_error.text = "Please enter your monthly water consumption (Litres)."
            return

        try:
            litres_val = float(litres_str)
            if litres_val < 0:
                raise ValueError()
        except ValueError:
            self.lbl_error.text = "Please enter a valid non-negative number for litres."
            return

        shower_dur = 0.0
        if self.input_shower_duration.text:
            try:
                shower_dur = float(self.input_shower_duration.text)
            except ValueError:
                shower_dur = 0.0

        self.btn_submit.disabled = True
        self.btn_submit.text = "Saving to PostgreSQL..."

        success, res = api_client.save_water(
            monthly_consumption_litres=litres_val,
            num_showers=self.cnt_showers.value,
            avg_shower_duration_mins=shower_dur,
            bucket_usage=self.cnt_buckets.value,
            washing_machine_usage=self.input_washing_freq.text or None,
            garden_watering=self.input_garden.text or None,
            vehicle_washing=self.input_vehicle.text or None,
            water_pump_usage=self.input_pump_usage.text or None,
            other_water_usage=self.input_other_water.text or None
        )

        self.btn_submit.disabled = False
        self.btn_submit.text = "Save Water Data  ✓"

        if not success:
            self.lbl_error.text = str(res)
            return

        # Final Success Feedback
        show_success_popup(
            title="All Data Successfully Saved!",
            message=(
                f"Recorded {litres_val:,.0f} Litres of water consumption into PostgreSQL!\n\n"
                "✓ Household Profile Saved\n"
                "✓ Electricity Inventory Saved\n"
                "✓ Water Footprint Saved\n\n"
                "Phase 1 MVP data collection complete."
            ),
            on_continue=self._on_flow_complete
        )

    def _on_flow_complete(self):
        # Reset and return to welcome or profile
        self.manager.current = "welcome"

    def _handle_back(self):
        self.manager.current = "electricity"
