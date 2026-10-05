"""Registration Screen for new households and residents."""

import re
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from services.api_client import api_client
from widgets.glass_widgets import GlassCard, GlassHeader, GlassInput, ModernButton


class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=[dp(20), dp(18), dp(20), dp(24)], spacing=dp(14))

        # Header
        header = GlassHeader(
            title="Create Account",
            subtitle="Register your household for resource tracking",
            on_back=lambda: self._navigate("welcome")
        )
        root.add_widget(header)

        # Scrollable form container
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        form_layout = BoxLayout(orientation="vertical", spacing=dp(14), size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter("height"))

        # Glass Form Card
        card = GlassCard(orientation="vertical", padding=dp(20), spacing=dp(12), size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))

        # Form Fields
        self.input_name = GlassInput(
            label_text="Full Name *",
            hint_text="e.g. Priya Sharma"
        )
        card.add_widget(self.input_name)

        self.input_email = GlassInput(
            label_text="Email Address *",
            hint_text="e.g. priya@example.com"
        )
        card.add_widget(self.input_email)

        self.input_password = GlassInput(
            label_text="Password *",
            hint_text="Min 6 characters",
            is_password=True
        )
        card.add_widget(self.input_password)

        self.input_confirm_password = GlassInput(
            label_text="Confirm Password *",
            hint_text="Re-enter password",
            is_password=True
        )
        card.add_widget(self.input_confirm_password)

        # Error notification label
        self.lbl_error = Label(
            text="",
            color=(0.95, 0.35, 0.42, 1),
            font_size="13sp",
            size_hint_y=None,
            height=dp(28),
            halign="center"
        )
        self.lbl_error.bind(size=self.lbl_error.setter("text_size"))
        card.add_widget(self.lbl_error)

        # Submit Button
        self.btn_submit = ModernButton(
            text="Register & Continue  →",
            style="primary",
            radius=12
        )
        self.btn_submit.bind(on_release=self._handle_register)
        card.add_widget(self.btn_submit)

        form_layout.add_widget(card)

        # Quick navigation to Login
        log_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(6))
        log_prompt = Label(
            text="Already have an account?",
            font_size="13sp",
            color=(0.65, 0.72, 0.85, 1),
            size_hint_x=0.6,
            halign="right"
        )
        log_prompt.bind(size=log_prompt.setter("text_size"))

        btn_go_log = ModernButton(
            text="Sign In",
            style="secondary",
            size_hint_x=0.4,
            height=dp(38),
            radius=8
        )
        btn_go_log.font_size = "13sp"
        btn_go_log.bind(on_release=lambda *a: self._navigate("login"))

        log_box.add_widget(log_prompt)
        log_box.add_widget(btn_go_log)
        form_layout.add_widget(log_box)

        scroll.add_widget(form_layout)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.lbl_error.text = ""

    def _handle_register(self, *args):
        full_name = self.input_name.text
        email = self.input_email.text
        password = self.input_password.text
        confirm_password = self.input_confirm_password.text

        # Client-side validation
        if not full_name or not email or not password or not confirm_password:
            self.lbl_error.text = "All fields are required."
            return

        if len(password) < 6:
            self.lbl_error.text = "Password must be at least 6 characters."
            return

        if password != confirm_password:
            self.lbl_error.text = "Passwords do not match."
            return

        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_pattern, email):
            self.lbl_error.text = "Please enter a valid email address."
            return

        self.btn_submit.disabled = True
        self.btn_submit.text = "Creating Account..."

        success, res = api_client.register(
            full_name=full_name,
            email=email,
            password=password,
            confirm_password=confirm_password
        )

        self.btn_submit.disabled = False
        self.btn_submit.text = "Register & Continue  →"

        if not success:
            self.lbl_error.text = str(res)
            return

        # Clear fields
        self.input_password.text = ""
        self.input_confirm_password.text = ""
        self.lbl_error.text = ""

        # Navigate directly to Household Profile
        self.manager.current = "profile"

    def _navigate(self, screen_name: str):
        self.manager.current = screen_name
