"""
AquaWatt Resident Registration Screen.
Modern Professional (Option A) design featuring:
- Elevated card container adapting to Light and Dark mode.
- Clear input fields with integrated password visibility toggles (👁️).
- Real-time client validation and server error display.
- Seamless registration flow connecting to the FastAPI backend.
"""

import os
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from services.api_client import api_client
from services.theme_manager import theme_manager
from widgets.glass_widgets import (
    BackButton,
    LOGO_DROPLET_PATH,
    GlassButton,
    GlassCard,
    GlassInput,
    Icon,
    LiquidGlassLayout,
    show_success_popup,
)


class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()
        theme_manager.register_listener(self._on_theme_changed)

    def _build_ui(self):
        self.clear_widgets()
        bg_layout = LiquidGlassLayout()

        # Top Bar with Back and Theme Toggle
        top_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            padding=[dp(20), dp(8), dp(20), dp(4)]
        )

        btn_back = BackButton(on_back=lambda: self._navigate("welcome"), label="Back")
        top_bar.add_widget(btn_back)

        top_bar.add_widget(BoxLayout(size_hint_x=1))  # Spacer

        is_dark = theme_manager.is_dark
        self.theme_chip = BoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            size_hint=(None, None),
            size=(dp(124), dp(34)),
            padding=[dp(10), 0, dp(10), 0]
        )
        self.theme_chip.bind(pos=self._update_theme_chip_bg, size=self._update_theme_chip_bg)
        t_icon_name = "weather-sunny" if not is_dark else "weather-night"
        self.theme_ic = Icon(icon_name=t_icon_name, font_size="16sp", color=theme_manager.get("text_primary"))
        self.theme_lbl = Label(
            text="Light Mode" if not is_dark else "Dark Mode",
            font_size="12sp",
            bold=True,
            color=theme_manager.get("text_primary"),
            valign="middle"
        )
        self.theme_lbl.bind(size=self.theme_lbl.setter("text_size"))
        self.theme_chip.add_widget(self.theme_ic)
        self.theme_chip.add_widget(self.theme_lbl)

        btn_tgl_click = Button(background_normal="", background_color=(0, 0, 0, 0), size_hint=(1, 1))
        btn_tgl_click.bind(on_release=lambda *a: theme_manager.toggle_theme())
        self.theme_chip.add_widget(btn_tgl_click)
        top_bar.add_widget(self.theme_chip)

        main_col = BoxLayout(orientation="vertical")
        main_col.add_widget(top_bar)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        center_container = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(10), dp(20), dp(24)],
            spacing=dp(14),
            size_hint=(None, None),
            width=dp(400)
        )
        center_container.bind(minimum_height=center_container.setter("height"))

        # Floating Elevated Card
        card = GlassCard(
            variant="default",
            orientation="vertical",
            padding=[dp(24), dp(22), dp(24), dp(22)],
            spacing=dp(12),
            radius=18,
            size_hint_y=None
        )
        card.bind(minimum_height=card.setter("height"))

        # 1. Brand Logo & Name
        brand_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(88), spacing=dp(3))

        if os.path.exists(LOGO_DROPLET_PATH):
            logo_img = KivyImage(
                source=LOGO_DROPLET_PATH,
                size_hint=(None, None),
                size=(dp(42), dp(42)),
                pos_hint={"center_x": 0.5}
            )
            brand_box.add_widget(logo_img)

        title_lbl = Label(
            text="AquaWatt",
            font_size="22sp",
            bold=True,
            color=theme_manager.get("text_primary"),
            size_hint_y=None,
            height=dp(26),
            halign="center",
            valign="middle"
        )
        title_lbl.bind(size=title_lbl.setter("text_size"))
        brand_box.add_widget(title_lbl)

        sub_lbl = Label(
            text="Track smarter. Save every drop and watt.",
            font_size="11sp",
            color=theme_manager.get("text_secondary"),
            size_hint_y=None,
            height=dp(18),
            halign="center",
            valign="middle"
        )
        sub_lbl.bind(size=sub_lbl.setter("text_size"))
        brand_box.add_widget(sub_lbl)
        card.add_widget(brand_box)

        # 2. Section Title
        title_section = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(44), spacing=dp(2))
        lbl_create = Label(
            text="Create Your Account",
            font_size="17sp",
            bold=True,
            color=theme_manager.get("text_primary"),
            halign="center",
            valign="middle"
        )
        lbl_create.bind(size=lbl_create.setter("text_size"))
        title_section.add_widget(lbl_create)

        lbl_instruct = Label(
            text="Join AquaWatt and start tracking",
            font_size="12sp",
            color=theme_manager.get("text_secondary"),
            halign="center",
            valign="middle"
        )
        lbl_instruct.bind(size=lbl_instruct.setter("text_size"))
        title_section.add_widget(lbl_instruct)
        card.add_widget(title_section)

        # 3. Form Inputs
        self.input_name = GlassInput(
            label_text="Full name",
            hint_text="Resident Name",
            icon_name="account-outline"
        )
        card.add_widget(self.input_name)

        self.input_email = GlassInput(
            label_text="Email address",
            hint_text="resident@example.com",
            icon_name="email-outline"
        )
        card.add_widget(self.input_email)

        self.input_password = GlassInput(
            label_text="Password",
            hint_text="••••••••",
            password=True,
            icon_name="lock-outline"
        )
        card.add_widget(self.input_password)

        self.input_confirm_password = GlassInput(
            label_text="Confirm password",
            hint_text="••••••••",
            password=True,
            icon_name="lock-check-outline"
        )
        card.add_widget(self.input_confirm_password)

        # 4. Error Message Banner
        self.lbl_error = Label(
            text="",
            font_size="12sp",
            color=(239 / 255, 68 / 255, 68 / 255, 1.0),  # Rose red
            size_hint_y=None,
            height=dp(18),
            halign="center",
            valign="middle"
        )
        self.lbl_error.bind(size=self.lbl_error.setter("text_size"))
        card.add_widget(self.lbl_error)

        # 5. Submit Button
        self.btn_submit = GlassButton(
            text="Register",
            style="primary",
            height=dp(46),
            radius=23
        )
        self.btn_submit.bind(on_release=self._handle_register)
        card.add_widget(self.btn_submit)

        # 6. Switch to Login Link
        login_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(34), spacing=dp(4))
        lbl_have = Label(
            text="Already have an account?",
            font_size="12sp",
            color=theme_manager.get("text_secondary"),
            size_hint_x=0.64,
            halign="right",
            valign="middle"
        )
        lbl_have.bind(size=lbl_have.setter("text_size"))

        btn_go_login = GlassButton(
            text="Sign In",
            style="secondary",
            size_hint_x=0.36,
            height=dp(30),
            radius=15
        )
        btn_go_login.font_size = "12sp"
        btn_go_login.bind(on_release=lambda *a: self._navigate("login"))

        login_box.add_widget(lbl_have)
        login_box.add_widget(btn_go_login)
        card.add_widget(login_box)

        center_container.add_widget(card)

        # Centering wrappers
        outer = BoxLayout(orientation="horizontal")
        outer.add_widget(BoxLayout(size_hint_x=1))
        outer.add_widget(center_container)
        outer.add_widget(BoxLayout(size_hint_x=1))

        scroll.add_widget(outer)
        main_col.add_widget(scroll)
        bg_layout.add_widget(main_col)
        self.add_widget(bg_layout)

    def _update_theme_chip_bg(self, inst, *args):
        inst.canvas.before.clear()
        with inst.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(*theme_manager.get("bg_card_elevated"))
            RoundedRectangle(pos=inst.pos, size=inst.size, radius=[(dp(17), dp(17))] * 4)
            Color(*theme_manager.get("border_card"))
            Line(rounded_rectangle=(inst.x, inst.y, inst.width, inst.height, dp(17)), width=1.0)

    def _on_theme_changed(self):
        saved_name = self.input_name.text if hasattr(self, "input_name") else ""
        saved_email = self.input_email.text if hasattr(self, "input_email") else ""
        self._build_ui()
        if hasattr(self, "input_name") and saved_name:
            self.input_name.text = saved_name
        if hasattr(self, "input_email") and saved_email:
            self.input_email.text = saved_email

    def on_pre_enter(self, *args):
        self.lbl_error.text = ""

    def _handle_register(self, *args):
        name = self.input_name.text
        email = self.input_email.text
        password = self.input_password.text
        confirm_password = self.input_confirm_password.text

        if not name or not email or not password or not confirm_password:
            self.lbl_error.text = "All fields are required."
            return

        if password != confirm_password:
            self.lbl_error.text = "Passwords do not match."
            return

        if len(password) < 6:
            self.lbl_error.text = "Password must be at least 6 characters."
            return

        self.btn_submit.disabled = True
        self.btn_submit.text = "Registering..."

        success, res = api_client.register(
            full_name=name,
            email=email,
            password=password,
            confirm_password=confirm_password
        )
        self.btn_submit.disabled = False
        self.btn_submit.text = "Register"

        if not success:
            self.lbl_error.text = str(res)
            return

        show_success_popup(
            title="Registration Successful",
            message=f"Welcome to AquaWatt, {name}!\nLet's configure your household context next.",
            on_continue=lambda: self._navigate("profile")
        )

    def _navigate(self, screen_name: str):
        self.manager.current = screen_name
