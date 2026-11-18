"""
AquaWatt Household Profile Form Screen.
Modern Professional (Option A) design featuring:
- Theme-reactive LiquidGlassLayout with in-app Light/Dark mode support.
- Collapsible/expanded sidebar navigation with active indicator.
- Polished household demographics card with modern steppers and selector pills.
- Dynamic pre-fill from PostgreSQL backend on screen entry.
- Clean validation, error display, and success modal.
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
    CounterWidget,
    GlassButton,
    GlassCard,
    GlassHeader,
    GlassInput,
    GlassSidebar,
    Icon,
    LiquidGlassLayout,
    show_success_popup,
)


class ProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_house_type = "Apartment"
        self.selected_unusual_occ = "None"
        self._build_ui()
        theme_manager.register_listener(self._on_theme_changed)

    def _on_theme_changed(self):
        saved_loc = self.input_location.text if hasattr(self, "input_location") else ""
        saved_members = self.cnt_members.value if hasattr(self, "cnt_members") else 4
        saved_baths = self.cnt_bathrooms.value if hasattr(self, "cnt_bathrooms") else 2
        saved_home = self.cnt_at_home.value if hasattr(self, "cnt_at_home") else 2
        saved_type = self.selected_house_type
        saved_occ = self.selected_unusual_occ

        self._build_ui()

        if hasattr(self, "input_location"):
            self.input_location.text = saved_loc
            self.cnt_members.value = saved_members
            self.cnt_bathrooms.value = saved_baths
            self.cnt_at_home.value = saved_home
            self._select_house_type(saved_type)
            self._select_unusual_occ(saved_occ)

    def _build_ui(self):
        self.clear_widgets()
        bg_layout = LiquidGlassLayout()

        # Main horizontal split: Sidebar on left + Content on right
        main_split = BoxLayout(orientation="horizontal")

        user_info = api_client.current_user or {}
        self.sidebar = GlassSidebar(
            active_screen="profile",
            on_navigate=self._navigate,
            on_sign_out=self._handle_sign_out,
            user_info=user_info
        )
        main_split.add_widget(self.sidebar)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.form_layout = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(18), dp(22), dp(20)],
            spacing=dp(14),
            size_hint_y=None
        )
        self.form_layout.bind(minimum_height=self.form_layout.setter("height"))

        # Header
        header = GlassHeader(
            title="Household Profile",
            subtitle="Configure your residence profile and baseline occupancy parameters",
            on_back=lambda: self._navigate("dashboard")
        )
        self.form_layout.add_widget(header)

        # Card: Household Details
        card = GlassCard(
            variant="default",
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint_y=None,
            radius=14
        )
        card.bind(minimum_height=card.setter("height"))

        h_details = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26), spacing=dp(8))
        ic = Icon(
            icon_name="home-outline",
            font_size="18sp",
            color=theme_manager.get("brand_primary")
        )
        t = Label(
            text="Household Specifications",
            bold=True,
            font_size="15sp",
            color=theme_manager.get("text_primary"),
            halign="left",
            valign="middle"
        )
        t.bind(size=t.setter("text_size"))
        h_details.add_widget(ic)
        h_details.add_widget(t)
        card.add_widget(h_details)

        # Household members stepper
        self.cnt_members = CounterWidget(label_text="Household Members *", default_val=4, min_val=1)
        card.add_widget(self.cnt_members)

        # House Type Selector
        lbl_type = Label(
            text="House Type *",
            font_size="13sp",
            bold=True,
            color=theme_manager.get("text_primary"),
            size_hint_y=None,
            height=dp(20),
            halign="left"
        )
        lbl_type.bind(size=lbl_type.setter("text_size"))
        card.add_widget(lbl_type)

        self.house_type_box = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(36))
        self.house_types = ["Apartment", "Independent House", "Other"]
        self.type_buttons = {}

        for htype in self.house_types:
            btn = GlassButton(
                text=htype,
                style="primary" if htype == self.selected_house_type else "secondary",
                radius=12
            )
            btn.font_size = "12sp"
            btn.bind(on_release=lambda instance, t=htype: self._select_house_type(t))
            self.type_buttons[htype] = btn
            self.house_type_box.add_widget(btn)

        card.add_widget(self.house_type_box)

        # Location Input
        self.input_location = GlassInput(
            label_text="City / Neighborhood *",
            hint_text="e.g. Indirapuram, Ghaziabad or HSR Layout, Bengaluru",
            icon_name="map-marker-outline",
            default_val=""
        )
        card.add_widget(self.input_location)

        # Bathrooms count
        self.cnt_bathrooms = CounterWidget(label_text="Number of Bathrooms *", default_val=2, min_val=1)
        card.add_widget(self.cnt_bathrooms)

        # People usually at home during the day
        self.cnt_at_home = CounterWidget(label_text="People usually at home during day", default_val=2, min_val=0)
        card.add_widget(self.cnt_at_home)

        # Unusual Occupancy Notes / Status
        lbl_occ = Label(
            text="Occupancy Status / Anomalies",
            font_size="13sp",
            bold=True,
            color=theme_manager.get("text_primary"),
            size_hint_y=None,
            height=dp(20),
            halign="left"
        )
        lbl_occ.bind(size=lbl_occ.setter("text_size"))
        card.add_widget(lbl_occ)

        self.occ_box = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(36))
        self.occ_types = ["None", "Guests", "Vacation", "Other"]
        self.occ_buttons = {}

        for occ in self.occ_types:
            btn = GlassButton(
                text=occ,
                style="primary" if occ == self.selected_unusual_occ else "secondary",
                radius=12
            )
            btn.font_size = "12sp"
            btn.bind(on_release=lambda instance, o=occ: self._select_unusual_occ(o))
            self.occ_buttons[occ] = btn
            self.occ_box.add_widget(btn)

        card.add_widget(self.occ_box)
        self.form_layout.add_widget(card)

        # Error label
        self.lbl_error = Label(
            text="",
            font_size="12sp",
            color=(239 / 255, 68 / 255, 68 / 255, 1),
            size_hint_y=None,
            height=dp(18),
            halign="center",
            valign="middle"
        )
        self.lbl_error.bind(size=self.lbl_error.setter("text_size"))
        self.form_layout.add_widget(self.lbl_error)

        # Submit button
        self.btn_submit = GlassButton(
            text="Save Profile Changes",
            style="primary",
            height=dp(46),
            radius=14
        )
        self.btn_submit.bind(on_release=self._handle_save_profile)
        self.form_layout.add_widget(self.btn_submit)

        scroll.add_widget(self.form_layout)
        main_split.add_widget(scroll)
        bg_layout.add_widget(main_split)
        self.add_widget(bg_layout)

    def _select_house_type(self, house_type: str):
        self.selected_house_type = house_type
        for t, btn in self.type_buttons.items():
            btn.style = "primary" if t == house_type else "secondary"
            btn._update_bg()

    def _select_unusual_occ(self, occ: str):
        self.selected_unusual_occ = occ
        for o, btn in self.occ_buttons.items():
            btn.style = "primary" if o == occ else "secondary"
            btn._update_bg()

    def on_pre_enter(self, *args):
        self.lbl_error.text = ""
        if hasattr(self, "sidebar"):
            self.sidebar.user_info = api_client.current_user or {}
            self.sidebar._build_sidebar()
        # If user has an existing profile, prefill it in background thread
        if api_client.token:
            def _bg():
                success, data = api_client.get_profile()
                def _apply(dt):
                    if success and isinstance(data, dict):
                        self.cnt_members.value = data.get("household_members", 4)
                        self.cnt_bathrooms.value = data.get("num_bathrooms", 2)
                        self.input_location.text = data.get("location", "")
                        self._select_house_type(data.get("house_type", "Apartment"))
                        if data.get("people_usually_at_home") is not None:
                            self.cnt_at_home.value = data.get("people_usually_at_home")
                        self._select_unusual_occ(data.get("unusual_occupancy", "None"))
                Clock.schedule_once(_apply, 0)
            threading.Thread(target=_bg, daemon=True).start()

    def _handle_save_profile(self, *args):
        location = self.input_location.text.strip()
        if not location:
            self.lbl_error.text = "Please enter your city/location."
            return

        self.btn_submit.disabled = True
        self.btn_submit.text = "Saving to PostgreSQL..."

        def _bg_save():
            success, res = api_client.save_profile(
                household_members=self.cnt_members.value,
                house_type=self.selected_house_type,
                location=location,
                num_bathrooms=self.cnt_bathrooms.value,
                people_usually_at_home=self.cnt_at_home.value,
                unusual_occupancy=self.selected_unusual_occ
            )
            def _done(dt):
                self.btn_submit.disabled = False
                self.btn_submit.text = "Save Profile Changes"

                if not success:
                    self.lbl_error.text = str(res)
                    return

                show_success_popup(
                    title="Profile Updated",
                    message="Household profile stored securely in PostgreSQL.\nReturning to dashboard.",
                    on_continue=lambda: self._navigate("dashboard")
                )
            Clock.schedule_once(_done, 0)
        threading.Thread(target=_bg_save, daemon=True).start()

    def _handle_sign_out(self):
        api_client.logout()
        self.manager.current = "welcome"

    def _navigate(self, screen_name: str):
        self.manager.current = screen_name
