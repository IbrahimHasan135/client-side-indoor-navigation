from __future__ import annotations

from kivy.app import App

from app.controllers.app_controller import AppController
from app.ui.main_screen import MainScreen


class BleNodeApp(App):
    title = "BLE Indoor Navigation"

    def build(self):
        self.controller = AppController()
        return MainScreen(self.controller.scan_controller)

    def on_stop(self) -> None:
        self.controller.scan_controller.stop_scan()


if __name__ == "__main__":
    BleNodeApp().run()
