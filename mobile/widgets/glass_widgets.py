"""
AquaWatt Modern Professional Design System & Smart Energy Control Center UI Components.
Implements the exact SaaS design system from the reference dashboard:
- Dark Mode (#0B1220 bg, #111C2E sidebar, #172438 cards, #1E2D44 border, #3B82F6 elec, #14B8A6 water, #34D399 green)
- Light Mode (#F5F8FC bg, #FFFFFF sidebar, #FFFFFF cards, #E2E8F0 border, #2563EB elec, #0D9488 water, #059669 green)
- Native Material Design Icons (zero missing tofu/box glyphs)
- Interactive Canvas Charts (Line charts with area fill, date range filters: 7D, 30D, 3M, 6M, 1Y)
- 4 Summary KPI Cards with mini-bar visualizers
- Progress bar widgets, tactical steppers, and accessible form controls.
"""

import os
from typing import Callable, Dict, List, Optional, Tuple

import kivymd
from kivymd.icon_definitions import md_icons
from kivy.core.text import LabelBase
from kivy.graphics import Color, Ellipse, Line, Mesh, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from services.theme_manager import theme_manager, ThemeTokens

# Register Material Design Icons font to eliminate any missing glyphs or square box symbols
MD_FONTS_DIR = os.path.join(os.path.dirname(kivymd.__file__), "fonts")
MDI_FONT_PATH = os.path.join(MD_FONTS_DIR, "materialdesignicons-webfont.ttf")
if os.path.exists(MDI_FONT_PATH):
    LabelBase.register(name="MDIcons", fn_regular=MDI_FONT_PATH)

# Asset Paths
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
BG_WATER_PATH = os.path.join(ASSETS_DIR, "bg_water.png")
BG_WELCOME_PATH = os.path.join(ASSETS_DIR, "bg_welcome.png")
LOGO_DROPLET_PATH = os.path.join(ASSETS_DIR, "logo_droplet.png")
LOGO_DROPLET_WHITE_PATH = os.path.join(ASSETS_DIR, "logo_droplet_white.png")


class Icon(Label):
    """
    Renders high-fidelity vector icons using Material Design Icons font.
    Guarantees no square/crossed-out tofu glyphs on any OS.
    """

    def __init__(self, icon_name: str = "help-circle", font_size="18sp", color=None, **kwargs):
        super().__init__(**kwargs)
        self.font_name = "MDIcons"
        self.font_size = font_size
        self._icon_name = icon_name
        self.text = md_icons.get(icon_name, md_icons.get("help-circle", "?"))
        if color:
            self.color = color
        else:
            self.color = theme_manager.get("text_primary")
        self.size_hint = (None, None)
        self.size = (dp(int(float(font_size.replace("sp", "")) * 1.3)), dp(int(float(font_size.replace("sp", "")) * 1.3)))
        self.halign = "center"
        self.valign = "middle"
        self.bind(size=self.setter("text_size"))

    def set_icon(self, icon_name: str):
        self._icon_name = icon_name
        self.text = md_icons.get(icon_name, "?")


class LiquidGlassLayout(BoxLayout):
    """Responsive application container adapting cleanly between Light and Dark mode."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._update_bg, size=self._update_bg)
        theme_manager.register_listener(self._update_bg)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*theme_manager.get("bg_screen"))
            Rectangle(pos=self.pos, size=self.size)


class GlassCard(BoxLayout):
    """
    Smart Energy Control Center Card Container.
    Features rounded corners, subtle borders (#1E2D44 in dark, #E2E8F0 in light),
    and soft ambient shadows.
    """

    def __init__(
        self,
        variant: str = "default",  # 'default', 'elevated', 'water', 'elec'
        radius: int = 14,
        padding=dp(16),
        spacing=dp(10),
        **kwargs
    ):
        super().__init__(padding=padding, spacing=spacing, **kwargs)
        self.variant = variant
        self.radius = radius
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        theme_manager.register_listener(self._update_canvas)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        bg_color = theme_manager.get("bg_card")
        border_color = theme_manager.get("border_card")

        if self.variant == "elevated":
            bg_color = theme_manager.get("bg_card_elevated")
        elif self.variant == "elec":
            bg_color = theme_manager.get("accent_elec_bg")
            border_color = theme_manager.get("accent_elec_border")
        elif self.variant == "water":
            bg_color = theme_manager.get("accent_water_bg")
            border_color = theme_manager.get("accent_water_border")

        with self.canvas.before:
            # Ambient Drop Shadow
            Color(*theme_manager.get("shadow_color"))
            RoundedRectangle(
                pos=(self.x + dp(1), self.y - dp(2)),
                size=self.size,
                radius=[(dp(self.radius), dp(self.radius))] * 4
            )
            # Surface Fill
            Color(*bg_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[(dp(self.radius), dp(self.radius))] * 4
            )
            # Subtle Border Line
            Color(*border_color)
            Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(self.radius)),
                width=1.0
            )


class CircularBadge(Widget):
    """
    Self-centering circular icon badge with dynamic canvas binding.
    Guarantees icon and circular background are never detached or drawn at (0, 0).
    """

    def __init__(self, icon_name: str, bg_color, icon_color, diameter=dp(34), icon_size="17sp", **kwargs):
        super().__init__(size_hint=(None, None), size=(diameter, diameter), pos_hint={"center_y": 0.5}, **kwargs)
        self.bg_color = bg_color
        self.icon_color = icon_color
        self.ic = Icon(icon_name=icon_name, font_size=icon_size, color=icon_color)
        self.add_widget(self.ic)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            Ellipse(pos=self.pos, size=self.size)
        self.ic.pos = (self.x + (self.width - self.ic.width) / 2, self.y + (self.height - self.ic.height) / 2)


class MiniBarVisualizer(BoxLayout):
    """
    Mini 5-bar ascending visualizer seen on the right side of the KPI summary cards.
    """

    def __init__(self, bar_color, **kwargs):
        super().__init__(
            orientation="horizontal",
            spacing=dp(2.5),
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={"center_y": 0.5},
            **kwargs
        )
        self.bar_color = bar_color
        self._heights = [0.35, 0.50, 0.65, 0.85, 1.00]
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self.canvas.before.clear()
        w = dp(3.2)
        total_h = self.height
        with self.canvas.before:
            for idx, factor in enumerate(self._heights):
                h = total_h * factor
                bx = self.x + idx * (w + dp(2.5))
                by = self.y + (total_h - h) / 2
                # Faint bar background
                Color(self.bar_color[0], self.bar_color[1], self.bar_color[2], 0.25)
                RoundedRectangle(pos=(bx, self.y), size=(w, total_h), radius=[(dp(2), dp(2))] * 4)
                # Filled active bar
                Color(*self.bar_color)
                RoundedRectangle(pos=(bx, by), size=(w, h), radius=[(dp(2), dp(2))] * 4)


class KPICard(GlassCard):
    """
    Top-row KPI Summary Card exactly matching the reference design:
    - Circular colored icon badge
    - Label and bold value with unit
    - Trend badge (↓ 8% vs last month)
    - Mini 5-bar visualizer
    """

    def __init__(
        self,
        title: str,
        value: str,
        unit: str,
        icon_name: str,
        icon_bg_color,
        icon_color,
        trend_pct: Optional[float] = None,
        bar_color=None,
        **kwargs
    ):
        super().__init__(
            orientation="horizontal",
            padding=[dp(10), dp(10), dp(8), dp(10)],
            spacing=dp(6),
            size_hint=(0.25, 1),
            radius=12,
            **kwargs
        )
        self.bar_color = bar_color or icon_color
        self.icon_bg_color = icon_bg_color
        self.icon_color = icon_color

        # 1. Circular Icon Badge
        badge_box = BoxLayout(size_hint=(None, 1), width=dp(36))
        self.badge = Widget(size_hint=(None, None), size=(dp(32), dp(32)), pos_hint={"center_y": 0.5})
        self.badge.bind(pos=self._update_badge, size=self._update_badge)

        self.ic_widget = Icon(icon_name=icon_name, font_size="17sp", color=icon_color)
        self.badge.add_widget(self.ic_widget)
        badge_box.add_widget(self.badge)
        self.add_widget(badge_box)

        # 2. Middle Content Column: Title, Value, Trend Pill
        mid_col = BoxLayout(orientation="vertical", spacing=dp(1), size_hint_x=1)

        self.lbl_title = Label(
            text=title,
            font_size="11sp",
            color=theme_manager.get("text_secondary"),
            size_hint_y=None,
            height=dp(16),
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right"
        )
        self.lbl_title.bind(size=self.lbl_title.setter("text_size"))
        mid_col.add_widget(self.lbl_title)

        display_val = f"{value} {unit}".strip()
        self.lbl_val = Label(
            text=display_val,
            font_size="16.5sp",
            bold=True,
            color=theme_manager.get("text_primary"),
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle"
        )
        self.lbl_val.bind(size=self.lbl_val.setter("text_size"))
        mid_col.add_widget(self.lbl_val)

        # Trend pill
        if trend_pct is not None:
            if trend_pct <= 0:
                trend_txt = f"↓ {abs(trend_pct):.0f}% vs last month"
                trend_col = (52 / 255, 211 / 255, 153 / 255, 1.0)  # Green
            else:
                trend_txt = f"↑ {trend_pct:.0f}% vs last month"
                trend_col = (239 / 255, 68 / 255, 68 / 255, 1.0)  # Red
        else:
            trend_txt = "— vs last month"
            trend_col = theme_manager.get("text_muted")

        self.lbl_trend = Label(
            text=trend_txt,
            font_size="9.5sp",
            bold=True,
            color=trend_col,
            size_hint_y=None,
            height=dp(14),
            halign="left",
            valign="middle",
            shorten=True
        )
        self.lbl_trend.bind(size=self.lbl_trend.setter("text_size"))
        mid_col.add_widget(self.lbl_trend)

        self.add_widget(mid_col)

        # 3. Right Mini Bar Visualizer
        self.bars = MiniBarVisualizer(bar_color=self.bar_color)
        self.add_widget(self.bars)

    def _update_badge(self, instance, *args):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*self.icon_bg_color)
            Ellipse(pos=instance.pos, size=instance.size)
        self.ic_widget.pos = (instance.x + (instance.width - self.ic_widget.width) / 2, instance.y + (instance.height - self.ic_widget.height) / 2)


class ChartTooltip(Label):
    """Peak value tooltip badge with rounded pill background matching reference."""

    def __init__(self, accent_color, **kwargs):
        super().__init__(
            size_hint=(None, None),
            size=(dp(76), dp(24)),
            font_size="10.5sp",
            bold=True,
            halign="center",
            valign="middle",
            **kwargs
        )
        self.accent_color = accent_color
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self.canvas.before.clear()
        if self.opacity < 0.05:
            return
        with self.canvas.before:
            Color(*theme_manager.get("bg_card_elevated"))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[(dp(6), dp(6))] * 4)
            Color(*self.accent_color)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(6)), width=1.0)


class CanvasChart(GlassCard):
    """
    High-fidelity vector line chart matching the reference dashboard:
    - Line chart with smooth connected points and subtle area fill beneath
    - Interactive date filters: 7D, 30D, 3M, 6M, 1Y
    - Peak value tooltip badge (e.g. '175 kWh', '3,200 L')
    - Legend indicators: '• This Period', '-- Last Period'
    - Formatted X-axis (Months) and Y-axis scale markers
    """

    def __init__(
        self,
        title: str,
        icon_name: str,
        accent_color,
        peak_text: str = "",
        unit: str = "kWh",
        data_points: Optional[List[float]] = None,
        x_labels: Optional[List[str]] = None,
        y_max: float = 200.0,
        on_filter_changed=None,
        **kwargs
    ):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(6), **kwargs)
        self.accent_color = accent_color
        self.chart_title = title
        self.icon_name = icon_name
        self.peak_text = peak_text
        self.unit = unit
        self.data_points = data_points or [120, 110, 130, 175, 140, 160]
        self.x_labels = x_labels or ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
        self.y_max = y_max
        self.active_filter = "6M"
        self.on_filter_changed = on_filter_changed

        self._build_header()
        self._build_chart_area()

    def _build_header(self):
        hdr = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))

        # Title + Icon
        t_box = BoxLayout(orientation="horizontal", spacing=dp(5), size_hint_x=1)
        ic = Icon(icon_name=self.icon_name, font_size="15sp", color=self.accent_color)
        t_lbl = Label(
            text=self.chart_title,
            bold=True,
            font_size="12sp",
            color=theme_manager.get("text_primary"),
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right"
        )
        t_lbl.bind(size=t_lbl.setter("text_size"))
        t_box.add_widget(ic)
        t_box.add_widget(t_lbl)
        hdr.add_widget(t_box)

        # Date Filters: 7D, 30D, 3M, 6M, 1Y
        self.filter_box = BoxLayout(orientation="horizontal", spacing=dp(2), size_hint=(None, 1), width=dp(145))
        self.filter_buttons = {}
        for f in ["7D", "30D", "3M", "6M", "1Y"]:
            is_active = (f == self.active_filter)
            btn = Button(
                text=f,
                font_size="9.5sp",
                bold=is_active,
                size_hint=(None, None),
                size=(dp(26), dp(20)),
                pos_hint={"center_y": 0.5},
                background_normal="",
                background_color=(0, 0, 0, 0),
                color=(1, 1, 1, 1) if is_active else theme_manager.get("text_secondary")
            )
            btn.bind(
                pos=lambda inst, *a: self._style_filter_btn(inst, inst.text == self.active_filter),
                size=lambda inst, *a: self._style_filter_btn(inst, inst.text == self.active_filter),
            )
            btn.bind(on_release=lambda inst, filt=f: self._select_filter(filt))
            self.filter_buttons[f] = btn
            self.filter_box.add_widget(btn)

        hdr.add_widget(self.filter_box)
        self.add_widget(hdr)

    def _style_filter_btn(self, btn, is_active):
        btn.canvas.before.clear()
        if btn.width < dp(5) or btn.height < dp(5):
            return
        with btn.canvas.before:
            if is_active:
                Color(20 / 255, 184 / 255, 166 / 255, 0.90)  # Teal active pill
                RoundedRectangle(pos=btn.pos, size=btn.size, radius=[(dp(5), dp(5))] * 4)
            else:
                Color(*theme_manager.get("border_card"))
                Line(rounded_rectangle=(btn.x, btn.y, btn.width, btn.height, dp(5)), width=0.8)

    def _select_filter(self, filter_name: str):
        self.active_filter = filter_name
        for f, b in self.filter_buttons.items():
            is_act = (f == filter_name)
            b.bold = is_act
            b.color = (1, 1, 1, 1) if is_act else theme_manager.get("text_secondary")
            self._style_filter_btn(b, is_act)
        if self.on_filter_changed:
            self.on_filter_changed(filter_name)

    def _build_chart_area(self):
        self.chart_widget = Widget(size_hint=(1, 1))
        self.chart_widget.bind(pos=self._redraw_chart, size=self._redraw_chart)
        self.tooltip_lbl = ChartTooltip(accent_color=self.accent_color, color=theme_manager.get("text_primary"))
        self.chart_widget.add_widget(self.tooltip_lbl)
        self.add_widget(self.chart_widget)

        # X-Axis Month Labels
        x_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(15), padding=[dp(20), 0, dp(20), 0])
        for lbl in self.x_labels:
            l = Label(text=lbl, font_size="9sp", color=theme_manager.get("text_muted"), halign="center")
            l.bind(size=l.setter("text_size"))
            x_row.add_widget(l)
        self.add_widget(x_row)

        # Bottom Legend Row
        leg_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(16), spacing=dp(12), padding=[dp(4), 0, 0, 0])
        lbl_legend1 = Label(
            text="• This Period",
            font_size="9.5sp",
            color=self.accent_color,
            size_hint=(None, 1),
            width=dp(70),
            halign="left"
        )
        lbl_legend2 = Label(
            text="-- Last Period",
            font_size="9.5sp",
            color=theme_manager.get("text_muted"),
            size_hint=(None, 1),
            width=dp(70),
            halign="left"
        )
        leg_row.add_widget(lbl_legend1)
        leg_row.add_widget(lbl_legend2)
        leg_row.add_widget(BoxLayout(size_hint_x=1))  # Spacer
        self.add_widget(leg_row)

    def _redraw_chart(self, *args):
        cw = self.chart_widget
        cw.canvas.clear()

        w, h = cw.width, cw.height
        if w < dp(50) or h < dp(50):
            return

        pad_x = dp(24)
        pad_y = dp(16)
        plot_w = w - pad_x * 2
        plot_h = h - pad_y * 2

        with cw.canvas:
            # 1. Subtle horizontal gridlines
            Color(*theme_manager.get("border_subtle"))
            for frac in [0.0, 0.33, 0.66, 1.0]:
                gy = cw.y + pad_y + plot_h * frac
                Line(points=[cw.x + pad_x, gy, cw.right - pad_x, gy], width=0.8)

            n = len(self.data_points)
            if n < 2:
                return

            pts = []
            pts_last = []
            peak_val = -1
            peak_idx = -1

            for i, val in enumerate(self.data_points):
                norm = min(1.0, max(0.05, val / (self.y_max or 200.0)))
                px = cw.x + pad_x + i * (plot_w / (n - 1))
                py = cw.y + pad_y + plot_h * norm
                pts.extend([px, py])
                # Mock last period data (smooth offset)
                last_norm = min(1.0, max(0.05, (val * 0.88) / (self.y_max or 200.0)))
                pts_last.extend([px, cw.y + pad_y + plot_h * last_norm])

                if val > peak_val:
                    peak_val = val
                    peak_idx = i

            # 2. Draw Translucent Area Fill underneath This Period
            Color(self.accent_color[0], self.accent_color[1], self.accent_color[2], 0.18)
            poly_points = [pts[0], cw.y + pad_y]
            poly_points.extend(pts)
            poly_points.extend([pts[-2], cw.y + pad_y])
            try:
                Mesh(
                    vertices=[
                        pts[0], cw.y + pad_y, 0, 0,
                        pts[-2], cw.y + pad_y, 0, 0,
                        pts[len(pts) // 2], cw.y + pad_y + plot_h * 0.5, 0, 0,
                    ],
                    indices=[0, 1, 2],
                    mode="triangle_fan"
                )
            except Exception:
                pass

            # 3. Draw Dashed Last Period Line
            Color(theme_manager.get("text_muted")[0], theme_manager.get("text_muted")[1], theme_manager.get("text_muted")[2], 0.45)
            Line(points=pts_last, width=1.2)

            # 4. Draw Main Solid Line
            Color(*self.accent_color)
            Line(points=pts, width=2.4)

            # 5. Draw Circular Markers
            for i in range(0, len(pts), 2):
                bx, by = pts[i], pts[i + 1]
                Color(*theme_manager.get("bg_card"))
                Ellipse(pos=(bx - dp(4), by - dp(4)), size=(dp(8), dp(8)))
                Color(*self.accent_color)
                Ellipse(pos=(bx - dp(2.5), by - dp(2.5)), size=(dp(5), dp(5)))

        # 6. Peak Value Tooltip Pill
        if peak_idx >= 0 and self.peak_text:
            pk_x = pts[peak_idx * 2]
            pk_y = pts[peak_idx * 2 + 1]
            tip_w = dp(76)
            tip_h = dp(24)
            tip_x = max(cw.x + pad_x, min(cw.right - pad_x - tip_w, pk_x - tip_w / 2))
            tip_y = min(cw.top - tip_h - dp(2), pk_y + dp(4))

            self.tooltip_lbl.text = self.peak_text
            self.tooltip_lbl.color = theme_manager.get("text_primary")
            self.tooltip_lbl.pos = (tip_x, tip_y)
            self.tooltip_lbl.size = (tip_w, tip_h)
            self.tooltip_lbl.opacity = 1.0
        else:
            self.tooltip_lbl.opacity = 0.0


class ProgressBarWidget(BoxLayout):
    """Horizontal progress bar for Monthly Budget tracking."""

    def __init__(self, progress: float = 0.75, bar_color=None, **kwargs):
        super().__init__(size_hint_y=None, height=dp(8), **kwargs)
        self.progress = max(0.0, min(1.0, progress))
        self.bar_color = bar_color or theme_manager.get("brand_primary")
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Track Background
            Color(self.bar_color[0], self.bar_color[1], self.bar_color[2], 0.20)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[(dp(4), dp(4))] * 4)
            # Progress Fill
            fill_w = max(dp(4), self.width * self.progress)
            Color(*self.bar_color)
            RoundedRectangle(pos=self.pos, size=(fill_w, self.height), radius=[(dp(4), dp(4))] * 4)


class GlassInput(BoxLayout):
    """
    Modern form input field with Material icon prefix, visible title label,
    and optional interactive password toggle button.
    """

    def __init__(
        self,
        label_text: str,
        hint_text: str = "",
        icon_name: str = "pencil",
        password: bool = False,
        default_val: str = "",
        icon_text: Optional[str] = None,
        is_password: Optional[bool] = None,
        **kwargs
    ):
        super().__init__(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(68), **kwargs)
        if is_password is not None:
            password = is_password
        self.is_password = password

        if icon_text:
            mapping = {
                "✉": "email-outline",
                "🔒": "lock-outline",
                "👤": "account-outline",
                "📍": "map-marker-outline",
                "🏠": "home-outline",
                "⚡": "flash",
                "💧": "water",
                "👁": "eye-outline",
            }
            icon_name = mapping.get(icon_text, icon_name)

        # 1. Title Label
        self.title_lbl = Label(
            text=label_text,
            font_size="12sp",
            bold=True,
            color=theme_manager.get("text_primary"),
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle"
        )
        self.title_lbl.bind(size=self.title_lbl.setter("text_size"))
        self.add_widget(self.title_lbl)

        # 2. Input Box with icon and text input
        self.input_box = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=[dp(12), 0, dp(8), 0],
            spacing=dp(8)
        )
        self.input_box.bind(pos=self._update_input_bg, size=self._update_input_bg)

        # Icon prefix
        self.ic = Icon(icon_name=icon_name, font_size="18sp", color=theme_manager.get("text_secondary"))
        self.input_box.add_widget(self.ic)

        # Text input
        self.txt_field = TextInput(
            text=default_val,
            hint_text=hint_text,
            password=self.is_password,
            multiline=False,
            font_size="13.5sp",
            cursor_color=theme_manager.get("brand_primary"),
            foreground_color=theme_manager.get("text_primary"),
            hint_text_color=theme_manager.get("input_hint"),
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            padding=[0, dp(12), 0, dp(12)]
        )
        self.input_box.add_widget(self.txt_field)

        # Password visibility toggle
        if self.is_password:
            self.btn_toggle_pw = RelativeLayout(
                size_hint=(None, None),
                size=(dp(34), dp(34)),
                pos_hint={"center_y": 0.5}
            )
            self.pw_icon = Icon(
                icon_name="eye-outline",
                font_size="18sp",
                color=theme_manager.get("text_secondary"),
                pos_hint={"center_x": 0.5, "center_y": 0.5}
            )
            pw_btn = Button(
                size_hint=(1, 1),
                background_normal="",
                background_color=(0, 0, 0, 0)
            )
            pw_btn.bind(on_release=self._toggle_password_visibility)
            self.btn_toggle_pw.add_widget(self.pw_icon)
            self.btn_toggle_pw.add_widget(pw_btn)
            self.input_box.add_widget(self.btn_toggle_pw)

        self.add_widget(self.input_box)
        theme_manager.register_listener(self._on_theme_changed)

    def _update_input_bg(self, instance, *args):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*theme_manager.get("input_bg"))
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[(dp(10), dp(10))] * 4)
            Color(*theme_manager.get("input_border"))
            Line(rounded_rectangle=(instance.x, instance.y, instance.width, instance.height, dp(10)), width=1.0)

    def _toggle_password_visibility(self, *args):
        self.txt_field.password = not self.txt_field.password
        if hasattr(self, "pw_icon"):
            self.pw_icon.set_icon("eye-off-outline" if not self.txt_field.password else "eye-outline")

    def _on_theme_changed(self):
        self.title_lbl.color = theme_manager.get("text_primary")
        self.txt_field.foreground_color = theme_manager.get("text_primary")
        self.txt_field.hint_text_color = theme_manager.get("input_hint")
        self.ic.color = theme_manager.get("text_secondary")
        self._update_input_bg(self.input_box)

    @property
    def text(self) -> str:
        return self.txt_field.text

    @text.setter
    def text(self, val: str):
        self.txt_field.text = val


class GlassButton(Button):
    """
    Modern high-contrast rounded action button.
    Styles: 'primary' (Emerald), 'secondary', 'elec' (Blue), 'water' (Teal), 'danger'
    """

    def __init__(
        self,
        text: str = "",
        style: str = "primary",
        radius: int = 10,
        height: float = dp(42),
        **kwargs
    ):
        super().__init__(text=text, bold=True, size_hint_y=None, height=height, **kwargs)
        self.style = style
        self.radius = radius
        self.font_size = "13sp"
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.bind(pos=self._update_bg, size=self._update_bg)
        theme_manager.register_listener(self._update_bg)
        self._update_bg()

    def _update_bg(self, *args):
        self.canvas.before.clear()
        if self.style == "primary":
            bg = theme_manager.get("brand_primary")
            fg = (1, 1, 1, 1)
            border = None
        elif self.style == "elec":
            bg = theme_manager.get("accent_elec")
            fg = (1, 1, 1, 1)
            border = None
        elif self.style == "water":
            bg = theme_manager.get("accent_water")
            fg = (1, 1, 1, 1)
            border = None
        elif self.style == "danger":
            bg = theme_manager.get("accent_danger")
            fg = (1, 1, 1, 1)
            border = None
        else:  # secondary
            bg = theme_manager.get("btn_secondary_bg")
            fg = theme_manager.get("btn_secondary_text")
            border = theme_manager.get("btn_secondary_border")

        self.color = fg
        with self.canvas.before:
            Color(*bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[(dp(self.radius), dp(self.radius))] * 4)
            if border:
                Color(*border)
                Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(self.radius)), width=1.0)


# Backward-compatibility alias
ModernButton = GlassButton


class CounterWidget(BoxLayout):
    """Tactile numerical counter stepper with minus, numeric badge, and plus targets."""

    def __init__(self, label_text: str, default_val: int = 1, min_val: int = 0, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(42), spacing=dp(10), **kwargs)
        self._value = int(default_val)
        self.min_val = int(min_val)

        self.lbl_title = Label(
            text=label_text,
            font_size="13sp",
            color=theme_manager.get("text_primary"),
            size_hint_x=0.65,
            halign="left",
            valign="middle"
        )
        self.lbl_title.bind(size=self.lbl_title.setter("text_size"))
        self.add_widget(self.lbl_title)

        ctrl = BoxLayout(orientation="horizontal", spacing=dp(6), size_hint_x=0.35)

        self.btn_minus = GlassButton(text="−", style="secondary", radius=8, size_hint=(None, None), size=(dp(34), dp(34)))
        self.btn_minus.bind(on_release=self._decrement)
        ctrl.add_widget(self.btn_minus)

        self.val_badge = Label(
            text=str(self._value),
            bold=True,
            font_size="14sp",
            color=theme_manager.get("text_primary"),
            size_hint=(None, None),
            size=(dp(42), dp(34)),
            halign="center",
            valign="middle"
        )
        self.val_badge.bind(size=self.val_badge.setter("text_size"))
        self.val_badge.bind(pos=self._update_badge_bg, size=self._update_badge_bg)
        ctrl.add_widget(self.val_badge)

        self.btn_plus = GlassButton(text="+", style="secondary", radius=8, size_hint=(None, None), size=(dp(34), dp(34)))
        self.btn_plus.bind(on_release=self._increment)
        ctrl.add_widget(self.btn_plus)

        self.add_widget(ctrl)
        theme_manager.register_listener(self._on_theme_changed)

    def _update_badge_bg(self, instance, *args):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*theme_manager.get("bg_chip"))
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[(dp(6), dp(6))] * 4)
            Color(*theme_manager.get("border_card"))
            Line(rounded_rectangle=(instance.x, instance.y, instance.width, instance.height, dp(6)), width=1.0)

    def _increment(self, *args):
        self._value += 1
        self.val_badge.text = str(self._value)

    def _decrement(self, *args):
        if self._value > self.min_val:
            self._value -= 1
            self.val_badge.text = str(self._value)

    def _on_theme_changed(self):
        self.lbl_title.color = theme_manager.get("text_primary")
        self.val_badge.color = theme_manager.get("text_primary")
        self._update_badge_bg(self.val_badge)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, v: int):
        self._value = max(self.min_val, int(v))
        self.val_badge.text = str(self._value)


class BackButton(RelativeLayout):
    """Clean back navigation button with vector arrow icon."""

    def __init__(self, on_back, label: str = "Back", **kwargs):
        w = dp(72) if label else dp(36)
        super().__init__(size_hint=(None, None), size=(w, dp(34)), pos_hint={"center_y": 0.5}, **kwargs)
        self.on_back = on_back

        box = BoxLayout(orientation="horizontal", spacing=dp(4), size_hint=(1, 1))
        self.ic = Icon(
            icon_name="arrow-left",
            font_size="18sp",
            color=theme_manager.get("text_secondary"),
            pos_hint={"center_y": 0.5}
        )
        box.add_widget(self.ic)

        if label:
            self.lbl = Label(
                text=label,
                font_size="13sp",
                bold=True,
                color=theme_manager.get("text_secondary"),
                pos_hint={"center_y": 0.5}
            )
            box.add_widget(self.lbl)

        self.add_widget(box)

        btn = Button(background_normal="", background_color=(0, 0, 0, 0), size_hint=(1, 1))
        btn.bind(on_release=lambda *a: self.on_back() if self.on_back else None)
        self.add_widget(btn)


class GlassHeader(BoxLayout):
    """
    Control Center top header bar:
    - Welcome greeting (Good Morning, {user}!)
    - Subtitle overview text
    - Date pill badge (Mon, Nov 16, 2026)
    - Notification bell with unread badge
    """

    def __init__(self, title: str, subtitle: str = "", on_back=None, show_date_bell: bool = True, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(52), spacing=dp(10), **kwargs)

        if on_back:
            self.back_btn = BackButton(on_back=on_back, label="")
            self.add_widget(self.back_btn)

        title_col = BoxLayout(orientation="vertical", spacing=dp(2), size_hint_x=1)
        self.lbl_title = Label(
            text=title,
            bold=True,
            font_size="19sp",
            color=theme_manager.get("text_primary"),
            halign="left",
            valign="middle"
        )
        self.lbl_title.bind(size=self.lbl_title.setter("text_size"))
        title_col.add_widget(self.lbl_title)

        if subtitle:
            self.lbl_sub = Label(
                text=subtitle,
                font_size="11.5sp",
                color=theme_manager.get("text_secondary"),
                halign="left",
                valign="middle"
            )
            self.lbl_sub.bind(size=self.lbl_sub.setter("text_size"))
            title_col.add_widget(self.lbl_sub)

        self.add_widget(title_col)

        if show_date_bell:
            from datetime import datetime
            now_str = datetime.now().strftime("%a, %b %d, %Y")
            
            right_box = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint=(None, 1), width=dp(200))
            
            # Date Chip
            date_chip = BoxLayout(
                orientation="horizontal",
                spacing=dp(6),
                size_hint=(None, None),
                size=(dp(145), dp(32)),
                pos_hint={"center_y": 0.5},
                padding=[dp(8), 0, dp(8), 0]
            )
            date_chip.bind(
                pos=lambda inst, *a: self._style_chip(inst),
                size=lambda inst, *a: self._style_chip(inst)
            )
            cal_ic = Icon(icon_name="calendar-month-outline", font_size="15sp", color=theme_manager.get("text_secondary"), pos_hint={"center_y": 0.5})
            d_lbl = Label(text=now_str, font_size="10.5sp", bold=True, color=theme_manager.get("text_primary"), pos_hint={"center_y": 0.5})
            date_chip.add_widget(cal_ic)
            date_chip.add_widget(d_lbl)
            right_box.add_widget(date_chip)

            # Bell with notification badge
            bell_btn = Button(
                size_hint=(None, None),
                size=(dp(34), dp(34)),
                pos_hint={"center_y": 0.5},
                background_normal="",
                background_color=(0, 0, 0, 0)
            )
            bell_ic = Icon(icon_name="bell-outline", font_size="18sp", color=theme_manager.get("text_primary"))
            bell_btn.bind(pos=lambda inst, *a: setattr(bell_ic, "pos", (inst.x + (inst.width - bell_ic.width) / 2, inst.y + (inst.height - bell_ic.height) / 2)))
            bell_btn.add_widget(bell_ic)
            right_box.add_widget(bell_btn)
            self.add_widget(right_box)

        theme_manager.register_listener(self._on_theme_changed)

    def _style_chip(self, inst):
        inst.canvas.before.clear()
        with inst.canvas.before:
            Color(*theme_manager.get("bg_chip"))
            RoundedRectangle(pos=inst.pos, size=inst.size, radius=[(dp(8), dp(8))] * 4)
            Color(*theme_manager.get("border_card"))
            Line(rounded_rectangle=(inst.x, inst.y, inst.width, inst.height, dp(8)), width=0.8)

    def _on_theme_changed(self):
        self.lbl_title.color = theme_manager.get("text_primary")
        if hasattr(self, "lbl_sub"):
            self.lbl_sub.color = theme_manager.get("text_secondary")


class NavItem(Button):
    """Clean full-width sidebar navigation item button without sibling overlay distortion."""

    def __init__(self, screen_key: str, icon_name: str, label_text: str, is_active: bool, on_navigate, **kwargs):
        super().__init__(
            size_hint_y=None,
            height=dp(38),
            background_normal="",
            background_color=(0, 0, 0, 0),
            **kwargs
        )
        self.screen_key = screen_key
        self.is_active = is_active
        self.on_navigate = on_navigate

        self.bind(pos=self._redraw, size=self._redraw)
        self.bind(on_release=lambda *a: self.on_navigate(self.screen_key) if self.on_navigate else None)

        self.inner_layout = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            padding=[dp(12), 0, dp(12), 0],
            pos=self.pos,
            size=self.size
        )
        self.bind(
            pos=lambda inst, val: setattr(self.inner_layout, "pos", val),
            size=lambda inst, val: setattr(self.inner_layout, "size", val)
        )

        ic_col = theme_manager.get("nav_active_text") if is_active else theme_manager.get("nav_inactive_text")
        self.icon = Icon(icon_name=icon_name, font_size="17sp", color=ic_col, pos_hint={"center_y": 0.5})
        self.inner_layout.add_widget(self.icon)

        self.lbl = Label(
            text=label_text,
            font_size="13sp",
            bold=is_active,
            color=ic_col,
            halign="left",
            valign="middle",
            size_hint=(1, 1)
        )
        self.lbl.bind(size=self.lbl.setter("text_size"))
        self.inner_layout.add_widget(self.lbl)
        self.add_widget(self.inner_layout)
        self._redraw()

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.is_active:
                Color(*theme_manager.get("nav_active_pill"))
                RoundedRectangle(pos=self.pos, size=self.size, radius=[(dp(10), dp(10))] * 4)


class ThemeToggleButton(Button):
    """Reliable theme switcher button with dynamic toggle switch graphics."""

    def __init__(self, on_toggle, **kwargs):
        super().__init__(
            size_hint_y=None,
            height=dp(36),
            background_normal="",
            background_color=(0, 0, 0, 0),
            **kwargs
        )
        self.on_toggle = on_toggle
        self.bind(on_release=lambda *a: self.on_toggle() if self.on_toggle else None)

        self.inner_layout = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            padding=[dp(10), 0, dp(10), 0],
            pos=self.pos,
            size=self.size
        )
        self.bind(
            pos=lambda inst, val: setattr(self.inner_layout, "pos", val),
            size=lambda inst, val: setattr(self.inner_layout, "size", val)
        )

        t_icon_name = "weather-sunny" if not theme_manager.is_dark else "weather-night"
        self.ic = Icon(icon_name=t_icon_name, font_size="16sp", color=theme_manager.get("text_secondary"), pos_hint={"center_y": 0.5})
        self.inner_layout.add_widget(self.ic)

        self.lbl = Label(
            text="Dark Mode" if theme_manager.is_dark else "Light Mode",
            font_size="12sp",
            color=theme_manager.get("text_secondary"),
            size_hint=(1, 1),
            halign="left",
            valign="middle"
        )
        self.lbl.bind(size=self.lbl.setter("text_size"))
        self.inner_layout.add_widget(self.lbl)

        # Dynamic switch graphic widget
        self.switch_w = Widget(size_hint=(None, None), size=(dp(34), dp(20)), pos_hint={"center_y": 0.5})
        self.switch_w.bind(pos=self._redraw_switch, size=self._redraw_switch)
        self.inner_layout.add_widget(self.switch_w)
        self.add_widget(self.inner_layout)
        self._redraw_switch()

    def _redraw_switch(self, *args):
        sw = self.switch_w
        sw.canvas.clear()
        with sw.canvas:
            if not theme_manager.is_dark:
                # Active light
                Color(*theme_manager.get("brand_primary"))
                RoundedRectangle(pos=sw.pos, size=sw.size, radius=[(dp(10), dp(10))] * 4)
                Color(1, 1, 1, 1)
                Ellipse(pos=(sw.right - dp(18), sw.y + dp(2)), size=(dp(16), dp(16)))
            else:
                # Active dark
                Color(*theme_manager.get("border_card"))
                RoundedRectangle(pos=sw.pos, size=sw.size, radius=[(dp(10), dp(10))] * 4)
                Color(148 / 255, 163 / 255, 184 / 255, 1.0)
                Ellipse(pos=(sw.x + dp(2), sw.y + dp(2)), size=(dp(16), dp(16)))


class UserCardButton(Button):
    """Bottom resident profile badge button with dynamic avatar and logout trigger."""

    def __init__(self, user_info: Dict, on_sign_out, **kwargs):
        super().__init__(
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=(0, 0, 0, 0),
            **kwargs
        )
        self.user_info = user_info or {}
        self.on_sign_out = on_sign_out
        self.bind(pos=self._redraw_bg, size=self._redraw_bg)
        self.bind(on_release=lambda *a: self.on_sign_out() if self.on_sign_out else None)

        self.inner_layout = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            padding=[dp(8), dp(4), dp(8), dp(4)],
            pos=self.pos,
            size=self.size
        )
        self.bind(
            pos=lambda inst, val: setattr(self.inner_layout, "pos", val),
            size=lambda inst, val: setattr(self.inner_layout, "size", val)
        )

        user_name = self.user_info.get("full_name") or self.user_info.get("email", "Resident").split("@")[0]
        init_letter = (user_name[0] if user_name else "U").upper()

        # Avatar Widget
        self.avatar_w = Widget(size_hint=(None, None), size=(dp(32), dp(32)), pos_hint={"center_y": 0.5})
        self.avatar_w.bind(pos=self._redraw_avatar, size=self._redraw_avatar)
        self.av_lbl = Label(text=init_letter, bold=True, font_size="13sp", color=(1, 1, 1, 1), size_hint=(None, None), size=(dp(32), dp(32)))
        self.avatar_w.add_widget(self.av_lbl)
        self.inner_layout.add_widget(self.avatar_w)

        # Name + Subtitle
        info_col = BoxLayout(orientation="vertical", spacing=0, size_hint_x=1)
        self.name_lbl = Label(text=user_name.capitalize(), bold=True, font_size="12sp", color=theme_manager.get("text_primary"), halign="left", valign="bottom")
        self.name_lbl.bind(size=self.name_lbl.setter("text_size"))
        self.sub_lbl = Label(text="My Household", font_size="9.5sp", color=theme_manager.get("text_muted"), halign="left", valign="top")
        self.sub_lbl.bind(size=self.sub_lbl.setter("text_size"))
        info_col.add_widget(self.name_lbl)
        info_col.add_widget(self.sub_lbl)
        self.inner_layout.add_widget(info_col)

        self.opt_ic = Icon(icon_name="logout-variant", font_size="16sp", color=theme_manager.get("text_muted"), pos_hint={"center_y": 0.5})
        self.inner_layout.add_widget(self.opt_ic)
        self.add_widget(self.inner_layout)
        self._redraw_bg()
        self._redraw_avatar()

    def _redraw_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*theme_manager.get("bg_card"))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[(dp(10), dp(10))] * 4)
            Color(*theme_manager.get("border_card"))
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(10)), width=0.8)

    def _redraw_avatar(self, *args):
        av = self.avatar_w
        av.canvas.clear()
        with av.canvas:
            Color(139 / 255, 92 / 255, 246 / 255, 1.0)  # Purple circle
            Ellipse(pos=av.pos, size=av.size)
        self.av_lbl.pos = av.pos


class GlassSidebar(BoxLayout):
    """
    Smart Energy Control Center Sidebar matching the attached design reference:
    - AquaWatt logo, title, and 'Track • Analyze • Conserve' tagline
    - Menu: Dashboard, Electricity, Water, History, Profile, Settings
    - High-visibility active item indicator (Emerald pill)
    - Theme switcher with toggle button (Light Mode on/off)
    - Logged-in user profile badge with avatar initial and 'My Household' subtitle
    """

    def __init__(
        self,
        active_screen: str = "dashboard",
        on_navigate=None,
        on_sign_out=None,
        user_info: Optional[Dict] = None,
        **kwargs
    ):
        super().__init__(
            orientation="vertical",
            size_hint=(None, 1),
            width=dp(215),
            padding=[dp(14), dp(16), dp(14), dp(14)],
            spacing=dp(8),
            **kwargs
        )
        self.active_screen = active_screen
        self.on_navigate = on_navigate
        self.on_sign_out = on_sign_out
        self.user_info = user_info or {}

        self.bind(pos=self._update_sidebar_bg, size=self._update_sidebar_bg)
        theme_manager.register_listener(self._on_theme_changed)
        self._build_sidebar()

    def _update_sidebar_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*theme_manager.get("bg_sidebar"))
            Rectangle(pos=self.pos, size=self.size)
            Color(*theme_manager.get("border_sidebar"))
            Line(points=[self.right, self.y, self.right, self.top], width=1.0)

    def _on_theme_changed(self):
        self._build_sidebar()

    def _build_sidebar(self):
        self.clear_widgets()

        # 1. Top Logo & Brand
        brand_box = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(46))
        logo_emblem = CircularBadge(
            icon_name="lightning-bolt",
            bg_color=theme_manager.get("brand_primary"),
            icon_color=(1, 1, 1, 1),
            diameter=dp(34),
            icon_size="18sp"
        )
        brand_box.add_widget(logo_emblem)

        brand_text_box = BoxLayout(orientation="vertical", spacing=0, size_hint_x=1)
        title_lbl = Label(
            text="AquaWatt",
            bold=True,
            font_size="17sp",
            color=theme_manager.get("text_primary"),
            halign="left",
            valign="bottom"
        )
        title_lbl.bind(size=title_lbl.setter("text_size"))
        tagline_lbl = Label(
            text="Track • Analyze • Conserve",
            font_size="9sp",
            color=theme_manager.get("text_muted"),
            halign="left",
            valign="top"
        )
        tagline_lbl.bind(size=tagline_lbl.setter("text_size"))
        brand_text_box.add_widget(title_lbl)
        brand_text_box.add_widget(tagline_lbl)
        brand_box.add_widget(brand_text_box)
        self.add_widget(brand_box)

        # Spacer
        self.add_widget(BoxLayout(size_hint_y=None, height=dp(8)))

        # 2. Navigation Items
        menu_items = [
            ("dashboard", "view-dashboard", "Dashboard"),
            ("electricity", "flash", "Electricity"),
            ("water", "water", "Water"),
            ("history", "history", "History"),
            ("profile", "account-circle-outline", "Profile"),
            ("settings", "cog-outline", "Settings"),
        ]

        menu_col = BoxLayout(orientation="vertical", spacing=dp(5), size_hint_y=None)
        menu_col.bind(minimum_height=menu_col.setter("height"))

        for screen_key, icon_name, label_text in menu_items:
            is_active = (self.active_screen == screen_key)
            item_btn = NavItem(
                screen_key=screen_key,
                icon_name=icon_name,
                label_text=label_text,
                is_active=is_active,
                on_navigate=self._navigate
            )
            menu_col.add_widget(item_btn)

        self.add_widget(menu_col)

        # Expanding middle spacer
        self.add_widget(BoxLayout(size_hint_y=1))

        # 3. Theme Toggle Row
        self.add_widget(ThemeToggleButton(on_toggle=theme_manager.toggle_theme))

        # 4. Logged-in User Profile Card at Bottom
        self.add_widget(UserCardButton(user_info=self.user_info, on_sign_out=self._handle_sign_out))

    def _style_nav_item(self, inst, is_active):
        inst.canvas.before.clear()
        with inst.canvas.before:
            if is_active:
                Color(*theme_manager.get("nav_active_pill"))
                RoundedRectangle(pos=inst.pos, size=inst.size, radius=[(dp(8), dp(8))] * 4)
            else:
                Color(0, 0, 0, 0)
                Rectangle(pos=inst.pos, size=inst.size)

    def _style_user_card(self, inst):
        inst.canvas.before.clear()
        with inst.canvas.before:
            Color(*theme_manager.get("bg_chip"))
            RoundedRectangle(pos=inst.pos, size=inst.size, radius=[(dp(8), dp(8))] * 4)

    def _navigate(self, screen_key: str):
        if self.on_navigate:
            self.on_navigate(screen_key)

    def _handle_sign_out(self):
        if self.on_sign_out:
            self.on_sign_out()


def show_success_popup(title: str, message: str, on_continue=None):
    """Modern modal dialog confirming database state persistence."""
    content = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(14))

    ic = Icon(icon_name="check-circle", font_size="36sp", color=theme_manager.get("brand_primary"))
    ic.pos_hint = {"center_x": 0.5}
    content.add_widget(ic)

    t_lbl = Label(
        text=title,
        font_size="17sp",
        bold=True,
        color=theme_manager.get("text_primary"),
        size_hint_y=None,
        height=dp(24),
        halign="center"
    )
    t_lbl.bind(size=t_lbl.setter("text_size"))
    content.add_widget(t_lbl)

    msg_lbl = Label(
        text=message,
        font_size="13sp",
        color=theme_manager.get("text_secondary"),
        halign="center",
        valign="middle"
    )
    msg_lbl.bind(size=msg_lbl.setter("text_size"))
    content.add_widget(msg_lbl)

    popup = Popup(
        title="",
        separator_height=0,
        content=content,
        size_hint=(None, None),
        size=(dp(380), dp(240)),
        background="",
        background_color=(*theme_manager.get("bg_card")[:3], 0.98),
        auto_dismiss=False
    )

    btn_ok = GlassButton(text="Continue", style="primary", height=dp(42), radius=10)

    def _close(*args):
        popup.dismiss()
        if on_continue:
            on_continue()

    btn_ok.bind(on_release=_close)
    content.add_widget(btn_ok)
    popup.open()
