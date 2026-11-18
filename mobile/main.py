"""
AquaWatt Tracker - Mobile Application
Final-Year Major Project MVP Foundation
"""

import os
import sys

# Ensure KIVY_HOME resides inside the workspace for Windows sandbox compatibility
if "KIVY_HOME" not in os.environ:
    os.environ["KIVY_HOME"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".kivy"))

# Ensure mobile packages can import cleanly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivymd.app import MDApp

from services.theme_manager import theme_manager
from screens import (
    DashboardScreen,
    ElectricityScreen,
    HistoryScreen,
    LoginScreen,
    ProfileScreen,
    RegisterScreen,
    SettingsScreen,
    WaterScreen,
    WelcomeScreen,
)

# Desktop / Tablet widescreen layout matching Option A modern desktop UI
Window.size = (1280, 720)
Window.clearcolor = theme_manager.get("bg_screen")


class AquaWattApp(MDApp):
    def build(self):
        self.title = "AquaWatt — Water & Electricity Tracking"
        self.theme_cls.theme_style = "Dark" if theme_manager.is_dark else "Light"
        self.theme_cls.primary_palette = "Teal"

        theme_manager.register_listener(self._on_theme_updated)

        sm = ScreenManager(transition=SlideTransition(duration=0.20))

        sm.add_widget(WelcomeScreen(name="welcome"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(HistoryScreen(name="history"))
        sm.add_widget(ProfileScreen(name="profile"))
        sm.add_widget(ElectricityScreen(name="electricity"))
        sm.add_widget(WaterScreen(name="water"))
        sm.add_widget(SettingsScreen(name="settings"))

        sm.current = "welcome"
        return sm

    def _on_theme_updated(self):
        self.theme_cls.theme_style = "Dark" if theme_manager.is_dark else "Light"
        Window.clearcolor = theme_manager.get("bg_screen")


if __name__ == "__main__":
    AquaWattApp().run()
