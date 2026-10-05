"""
Glassmorphic and modern UI widgets for the Water & Electricity Tracking Mobile App.
Provides liquid-glass styling, soft glows, responsive cards, and input controls.
"""

from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp


class GlassCard(BoxLayout):
    """Translucent card container with subtle borders and rounded corners."""

    def __init__(self, bg_color=(0.09, 0.13, 0.22, 0.85), border_color=(1, 1, 1, 0.15), radius=16, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius

        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Translucent background fill
            Color(*self.bg_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[(dp(self.radius), dp(self.radius))] * 4
            )
            # Specular glass edge line
            Color(*self.border_color)
            Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(self.radius)),
                width=1.1
            )


class GlassInput(BoxLayout):
    """Modern input field with label and translucent frosted container."""

    def __init__(
        self,
        label_text: str = "",
        hint_text: str = "",
        is_password: bool = False,
        input_filter=None,
        default_val: str = "",
        **kwargs
    ):
        super().__init__(orientation="vertical", spacing=dp(6), size_hint_y=None, height=dp(76), **kwargs)

        if label_text:
            self.label = Label(
                text=label_text,
                size_hint_y=None,
                height=dp(20),
                font_size="13sp",
                bold=True,
                color=(0.78, 0.85, 0.95, 1),
                halign="left",
                valign="middle"
            )
            self.label.bind(size=self.label.setter("text_size"))
            self.add_widget(self.label)

        self.input_container = BoxLayout(size_hint_y=None, height=dp(48))
        self.input_container.bind(pos=self._update_input_bg, size=self._update_input_bg)

        self.text_input = TextInput(
            text=default_val,
            hint_text=hint_text,
            password=is_password,
            input_filter=input_filter,
            multiline=False,
            font_size="15sp",
            foreground_color=(0.96, 0.98, 1, 1),
            hint_text_color=(0.48, 0.56, 0.68, 1),
            background_color=(0, 0, 0, 0),
            cursor_color=(0.0, 0.85, 0.95, 1),
            padding=[dp(14), dp(13), dp(14), dp(10)]
        )
        self.input_container.add_widget(self.text_input)
        self.add_widget(self.input_container)

    def _update_input_bg(self, instance, *args):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.12, 0.17, 0.28, 0.75)
            RoundedRectangle(
                pos=instance.pos,
                size=instance.size,
                radius=[(dp(10), dp(10))] * 4
            )
            Color(0.25, 0.38, 0.58, 0.45)
            Line(
                rounded_rectangle=(instance.x, instance.y, instance.width, instance.height, dp(10)),
                width=1.0
            )

    @property
    def text(self) -> str:
        return self.text_input.text.strip()

    @text.setter
    def text(self, val: str):
        self.text_input.text = str(val)


class ModernButton(Button):
    """Sleek button with gradient-inspired colors and rounded corners."""

    def __init__(
        self,
        style="primary",  # primary (water cyan), electric (amber/purple), secondary, danger
        radius=12,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.style = style
        self.radius = radius
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.font_size = "15sp"
        self.bold = True
        self.size_hint_y = None
        self.height = dp(48)

        if style == "primary":
            self.normal_color = (0.02, 0.72, 0.88, 1)      # Vibrant Cyan
            self.pressed_color = (0.01, 0.56, 0.70, 1)
            self.color = (0.04, 0.10, 0.18, 1)             # Dark text for cyan
        elif style == "electric":
            self.normal_color = (0.98, 0.70, 0.10, 1)     # Electric Amber
            self.pressed_color = (0.85, 0.58, 0.08, 1)
            self.color = (0.08, 0.08, 0.12, 1)
        elif style == "purple":
            self.normal_color = (0.50, 0.28, 0.88, 1)     # Neon Purple
            self.pressed_color = (0.40, 0.20, 0.74, 1)
            self.color = (1, 1, 1, 1)
        elif style == "danger":
            self.normal_color = (0.88, 0.26, 0.36, 1)     # Rose red
            self.pressed_color = (0.75, 0.20, 0.28, 1)
            self.color = (1, 1, 1, 1)
        else:  # secondary / glass
            self.normal_color = (0.16, 0.22, 0.35, 0.75)
            self.pressed_color = (0.22, 0.30, 0.46, 0.85)
            self.color = (0.85, 0.92, 1, 1)

        self.current_bg = self.normal_color
        self.bind(pos=self._update_bg, size=self._update_bg)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.current_bg = self.pressed_color
            self._update_bg()
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        self.current_bg = self.normal_color
        self._update_bg()
        return super().on_touch_up(touch)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.current_bg)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[(dp(self.radius), dp(self.radius))] * 4
            )
            # Specular edge highlight
            Color(1, 1, 1, 0.18)
            Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(self.radius)),
                width=1.0
            )


class CounterWidget(BoxLayout):
    """Stepper widget [ - ]  [ count ]  [ + ] for appliances and usage counters."""

    def __init__(self, label_text: str = "", default_val: int = 0, min_val: int = 0, **kwargs):
        super().__init__(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(50), **kwargs)
        self.min_val = min_val
        self._value = default_val

        self.label = Label(
            text=label_text,
            size_hint_x=0.55,
            font_size="14sp",
            color=(0.88, 0.92, 0.98, 1),
            halign="left",
            valign="middle"
        )
        self.label.bind(size=self.label.setter("text_size"))
        self.add_widget(self.label)

        controls = BoxLayout(size_hint_x=0.45, spacing=dp(6))

        # Minus button
        self.btn_minus = ModernButton(
            text="−",
            style="secondary",
            size_hint_x=0.33,
            radius=8
        )
        self.btn_minus.font_size = "18sp"
        self.btn_minus.bind(on_release=self._decrement)
        controls.add_widget(self.btn_minus)

        # Value display badge
        self.val_badge = Label(
            text=str(self._value),
            size_hint_x=0.34,
            bold=True,
            font_size="16sp",
            color=(0.02, 0.85, 0.95, 1)
        )
        self.val_badge.bind(pos=self._update_badge_bg, size=self._update_badge_bg)
        controls.add_widget(self.val_badge)

        # Plus button
        self.btn_plus = ModernButton(
            text="+",
            style="secondary",
            size_hint_x=0.33,
            radius=8
        )
        self.btn_plus.font_size = "18sp"
        self.btn_plus.bind(on_release=self._increment)
        controls.add_widget(self.btn_plus)

        self.add_widget(controls)

    def _update_badge_bg(self, instance, *args):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.12, 0.16, 0.26, 0.9)
            RoundedRectangle(
                pos=instance.pos,
                size=instance.size,
                radius=[(dp(8), dp(8))] * 4
            )
            Color(0.25, 0.35, 0.55, 0.4)
            Line(
                rounded_rectangle=(instance.x, instance.y, instance.width, instance.height, dp(8)),
                width=1.0
            )

    def _increment(self, *args):
        self._value += 1
        self.val_badge.text = str(self._value)

    def _decrement(self, *args):
        if self._value > self.min_val:
            self._value -= 1
            self.val_badge.text = str(self._value)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, v: int):
        self._value = max(self.min_val, int(v))
        self.val_badge.text = str(self._value)


class GlassHeader(BoxLayout):
    """Header bar with optional back button, category badge, and title."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        accent_color=(0.02, 0.78, 0.92, 1),
        on_back=None,
        **kwargs
    ):
        super().__init__(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(64), **kwargs)

        if on_back:
            back_btn = ModernButton(
                text="←",
                style="secondary",
                size_hint=(None, None),
                size=(dp(42), dp(42)),
                radius=10
            )
            back_btn.font_size = "20sp"
            back_btn.bind(on_release=lambda *a: on_back())
            self.add_widget(back_btn)

        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        lbl_title = Label(
            text=title,
            bold=True,
            font_size="19sp",
            color=(0.96, 0.98, 1, 1),
            halign="left",
            valign="middle"
        )
        lbl_title.bind(size=lbl_title.setter("text_size"))
        title_box.add_widget(lbl_title)

        if subtitle:
            lbl_sub = Label(
                text=subtitle,
                font_size="12sp",
                color=accent_color,
                halign="left",
                valign="middle"
            )
            lbl_sub.bind(size=lbl_sub.setter("text_size"))
            title_box.add_widget(lbl_sub)

        self.add_widget(title_box)


def show_success_popup(title: str, message: str, on_continue=None):
    """Display a glassmorphic success modal dialog."""
    content = BoxLayout(orientation="vertical", spacing=dp(16), padding=dp(20))

    # Icon / badge
    badge = Label(
        text="✓",
        font_size="36sp",
        bold=True,
        color=(0.05, 0.88, 0.60, 1),
        size_hint_y=None,
        height=dp(50)
    )
    content.add_widget(badge)

    msg_lbl = Label(
        text=message,
        font_size="14sp",
        color=(0.9, 0.94, 0.98, 1),
        halign="center",
        valign="middle"
    )
    msg_lbl.bind(size=msg_lbl.setter("text_size"))
    content.add_widget(msg_lbl)

    btn = ModernButton(text="Continue", style="primary", height=dp(44))
    content.add_widget(btn)

    popup = Popup(
        title=title,
        title_size="16sp",
        title_color=(0.95, 0.97, 1, 1),
        content=content,
        size_hint=(0.85, 0.42),
        auto_dismiss=False,
        background_color=(0.08, 0.11, 0.19, 0.95)
    )

    def _close(*args):
        popup.dismiss()
        if on_continue:
            on_continue()

    btn.bind(on_release=_close)
    popup.open()
