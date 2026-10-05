"""Household Profile screen for collecting household context, size, and occupancy."""

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


class ProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_house_type = "Apartment"
        self.selected_unusual_occ = "None"
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=[dp(20), dp(16), dp(20), dp(20)], spacing=dp(12))

        # Header
        header = GlassHeader(
            title="Household Profile",
            subtitle="Step 1 of 3: Structure & Occupancy Context",
            on_back=self._handle_back
        )
        root.add_widget(header)

        # Scrollable form container
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        form_layout = BoxLayout(orientation="vertical", spacing=dp(16), size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter("height"))

        # Section 1: Household Structure
        card_struct = GlassCard(orientation="vertical", padding=dp(18), spacing=dp(14), size_hint_y=None)
        card_struct.bind(minimum_height=card_struct.setter("height"))

        sec1_title = Label(
            text="🏠 Household Details",
            font_size="15sp",
            bold=True,
            color=(0.02, 0.85, 0.95, 1),
            size_hint_y=None,
            height=dp(24),
            halign="left"
        )
        sec1_title.bind(size=sec1_title.setter("text_size"))
        card_struct.add_widget(sec1_title)

        # Household members stepper
        self.cnt_members = CounterWidget(label_text="Household Members *", default_val=3, min_val=1)
        card_struct.add_widget(self.cnt_members)

        # Bathrooms stepper
        self.cnt_bathrooms = CounterWidget(label_text="Number of Bathrooms *", default_val=2, min_val=1)
        card_struct.add_widget(self.cnt_bathrooms)

        # Location input
        self.input_location = GlassInput(
            label_text="City / Location *",
            hint_text="e.g. Indirapuram, Ghaziabad"
        )
        card_struct.add_widget(self.input_location)

        # House type chips
        ht_box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None, height=dp(74))
        ht_lbl = Label(
            text="House Type *",
            size_hint_y=None,
            height=dp(20),
            font_size="13sp",
            bold=True,
            color=(0.78, 0.85, 0.95, 1),
            halign="left"
        )
        ht_lbl.bind(size=ht_lbl.setter("text_size"))
        ht_box.add_widget(ht_lbl)

        chips_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(42))
        self.house_type_btns = {}
        for h_type in ["Apartment", "Independent House", "Other"]:
            btn = ModernButton(
                text=h_type,
                style="primary" if h_type == self.selected_house_type else "secondary",
                radius=8
            )
            btn.font_size = "12sp"
            btn.bind(on_release=lambda inst, val=h_type: self._select_house_type(val))
            self.house_type_btns[h_type] = btn
            chips_row.add_widget(btn)
        ht_box.add_widget(chips_row)
        card_struct.add_widget(ht_box)

        form_layout.add_widget(card_struct)

        # Section 2: Occupancy Context
        card_occ = GlassCard(orientation="vertical", padding=dp(18), spacing=dp(14), size_hint_y=None)
        card_occ.bind(minimum_height=card_occ.setter("height"))

        sec2_title = Label(
            text="👥 Occupancy Patterns (Optional)",
            font_size="15sp",
            bold=True,
            color=(0.98, 0.70, 0.10, 1),
            size_hint_y=None,
            height=dp(24),
            halign="left"
        )
        sec2_title.bind(size=sec2_title.setter("text_size"))
        card_occ.add_widget(sec2_title)

        # People usually at home during day
        self.cnt_at_home = CounterWidget(label_text="People usually at home during day", default_val=1, min_val=0)
        card_occ.add_widget(self.cnt_at_home)

        # Unusual occupancy chips
        occ_box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None, height=dp(74))
        occ_lbl = Label(
            text="Unusual Occupancy Context",
            size_hint_y=None,
            height=dp(20),
            font_size="13sp",
            bold=True,
            color=(0.78, 0.85, 0.95, 1),
            halign="left"
        )
        occ_lbl.bind(size=occ_lbl.setter("text_size"))
        occ_box.add_widget(occ_lbl)

        occ_chips_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(42))
        self.unusual_occ_btns = {}
        for occ_val in ["None", "Guests", "Vacation", "Other"]:
            btn = ModernButton(
                text=occ_val,
                style="primary" if occ_val == self.selected_unusual_occ else "secondary",
                radius=8
            )
            btn.font_size = "12sp"
            btn.bind(on_release=lambda inst, val=occ_val: self._select_unusual_occ(val))
            self.unusual_occ_btns[occ_val] = btn
            occ_chips_row.add_widget(btn)
        occ_box.add_widget(occ_chips_row)
        card_occ.add_widget(occ_box)

        form_layout.add_widget(card_occ)

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

        # Action Button
        self.btn_submit = ModernButton(
            text="Save & Proceed to Electricity Form  →",
            style="primary",
            radius=12
        )
        self.btn_submit.bind(on_release=self._handle_save_profile)
        form_layout.add_widget(self.btn_submit)

        scroll.add_widget(form_layout)
        root.add_widget(scroll)
        self.add_widget(root)

    def _select_house_type(self, house_type: str):
        self.selected_house_type = house_type
        for k, btn in self.house_type_btns.items():
            btn.style = "primary" if k == house_type else "secondary"
            btn.normal_color = (0.02, 0.72, 0.88, 1) if k == house_type else (0.16, 0.22, 0.35, 0.75)
            btn.color = (0.04, 0.10, 0.18, 1) if k == house_type else (0.85, 0.92, 1, 1)
            btn._update_bg()

    def _select_unusual_occ(self, occ: str):
        self.selected_unusual_occ = occ
        for k, btn in self.unusual_occ_btns.items():
            btn.style = "primary" if k == occ else "secondary"
            btn.normal_color = (0.02, 0.72, 0.88, 1) if k == occ else (0.16, 0.22, 0.35, 0.75)
            btn.color = (0.04, 0.10, 0.18, 1) if k == occ else (0.85, 0.92, 1, 1)
            btn._update_bg()

    def on_pre_enter(self, *args):
        self.lbl_error.text = ""
        # If user has an existing profile, prefill it
        if api_client.token:
            success, data = api_client.get_profile()
            if success and isinstance(data, dict):
                self.cnt_members.value = data.get("household_members", 3)
                self.cnt_bathrooms.value = data.get("num_bathrooms", 2)
                self.input_location.text = data.get("location", "")
                self._select_house_type(data.get("house_type", "Apartment"))
                if data.get("people_usually_at_home") is not None:
                    self.cnt_at_home.value = data.get("people_usually_at_home")
                self._select_unusual_occ(data.get("unusual_occupancy", "None"))

    def _handle_save_profile(self, *args):
        location = self.input_location.text
        if not location:
            self.lbl_error.text = "Please enter your city/location."
            return

        self.btn_submit.disabled = True
        self.btn_submit.text = "Saving to PostgreSQL..."

        success, res = api_client.save_profile(
            household_members=self.cnt_members.value,
            house_type=self.selected_house_type,
            location=location,
            num_bathrooms=self.cnt_bathrooms.value,
            people_usually_at_home=self.cnt_at_home.value,
            unusual_occupancy=self.selected_unusual_occ
        )

        self.btn_submit.disabled = False
        self.btn_submit.text = "Save & Proceed to Electricity Form  →"

        if not success:
            self.lbl_error.text = str(res)
            return

        # Show success confirmation modal, then navigate to Electricity screen
        show_success_popup(
            title="Profile Saved",
            message="Household profile stored securely in PostgreSQL.\nProceeding to Electricity Consumption.",
            on_continue=lambda: self._navigate("electricity")
        )

    def _handle_back(self):
        self.manager.current = "login"

    def _navigate(self, screen_name: str):
        self.manager.current = screen_name
