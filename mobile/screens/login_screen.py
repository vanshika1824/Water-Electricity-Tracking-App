"""Login Screen for authenticating existing residents against PostgreSQL."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from services.api_client import api_client
from widgets.glass_widgets import GlassCard, GlassHeader, GlassInput, ModernButton


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=[dp(20), dp(18), dp(20), dp(24)], spacing=dp(14))

        # Header
        header = GlassHeader(
            title="Resident Sign In",
            subtitle="Access your household tracking dashboard",
            on_back=lambda: self._navigate("welcome")
        )
        root.add_widget(header)

        # Scrollable form container
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        form_layout = BoxLayout(orientation="vertical", spacing=dp(16), size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter("height"))

        # Glass Form Card
        card = GlassCard(orientation="vertical", padding=dp(20), spacing=dp(14), size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))

        # Inputs
        self.input_email = GlassInput(
            label_text="Email Address *",
            hint_text="e.g. resident@example.com"
        )
        card.add_widget(self.input_email)

        self.input_password = GlassInput(
            label_text="Password *",
            hint_text="Enter your password",
            is_password=True
        )
        card.add_widget(self.input_password)

        # Error notification label
        self.lbl_error = Label(
            text="",
            color=(0.95, 0.35, 0.42, 1),
            font_size="13sp",
            size_hint_y=None,
            height=dp(26),
            halign="center"
        )
        self.lbl_error.bind(size=self.lbl_error.setter("text_size"))
        card.add_widget(self.lbl_error)

        # Sign In Action
        self.btn_submit = ModernButton(
            text="Sign In  →",
            style="primary",
            radius=12
        )
        self.btn_submit.bind(on_release=self._handle_login)
        card.add_widget(self.btn_submit)

        form_layout.add_widget(card)

        # Quick navigation to Register
        reg_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(6))
        reg_prompt = Label(
            text="Don't have an account yet?",
            font_size="13sp",
            color=(0.65, 0.72, 0.85, 1),
            size_hint_x=0.6,
            halign="right"
        )
        reg_prompt.bind(size=reg_prompt.setter("text_size"))

        btn_go_reg = ModernButton(
            text="Register Now",
            style="secondary",
            size_hint_x=0.4,
            height=dp(38),
            radius=8
        )
        btn_go_reg.font_size = "13sp"
        btn_go_reg.bind(on_release=lambda *a: self._navigate("register"))

        reg_box.add_widget(reg_prompt)
        reg_box.add_widget(btn_go_reg)
        form_layout.add_widget(reg_box)

        scroll.add_widget(form_layout)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.lbl_error.text = ""

    def _handle_login(self, *args):
        email = self.input_email.text
        password = self.input_password.text

        if not email or not password:
            self.lbl_error.text = "Please enter both email and password."
            return

        self.btn_submit.disabled = True
        self.btn_submit.text = "Authenticating..."

        success, res = api_client.login(email, password)
        self.btn_submit.disabled = False
        self.btn_submit.text = "Sign In  →"

        if not success:
            self.lbl_error.text = str(res)
            return

        # Check if user already has a profile
        user_info = res.get("user", {})
        has_profile = user_info.get("has_profile", False)

        # Clear inputs
        self.input_password.text = ""
        self.lbl_error.text = ""

        # Navigate to household profile
        self.manager.current = "profile"

    def _navigate(self, screen_name: str):
        self.manager.current = screen_name
