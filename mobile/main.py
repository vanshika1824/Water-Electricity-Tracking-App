"""
AquaWatt Tracker - Mobile Application
Final-Year Major Project MVP Foundation
"""

import os
import sys

# Ensure mobile packages can import cleanly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivymd.app import MDApp

from screens import (
    ElectricityScreen,
    LoginScreen,
    ProfileScreen,
    RegisterScreen,
    WaterScreen,
    WelcomeScreen,
)

# Standard mobile viewport emulation for desktop preview
Window.size = (400, 780)
Window.clearcolor = (0.05, 0.08, 0.14, 1.0)  # Deep midnight slate


class AquaWattApp(MDApp):
    def build(self):
        self.title = "AquaWatt - Water & Electricity Tracker"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"

        sm = ScreenManager(transition=SlideTransition(duration=0.25))

        sm.add_widget(WelcomeScreen(name="welcome"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(ProfileScreen(name="profile"))
        sm.add_widget(ElectricityScreen(name="electricity"))
        sm.add_widget(WaterScreen(name="water"))

        sm.current = "welcome"
        return sm


if __name__ == "__main__":
    AquaWattApp().run()
