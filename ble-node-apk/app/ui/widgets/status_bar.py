from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label


class StatusBar(BoxLayout):
    def __init__(self, **kwargs) -> None:
        super().__init__(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(68), **kwargs)
        self.status_label = Label(text="Siap", bold=True, halign="left", valign="middle")
        self.detail_label = Label(text="BLE scan belum berjalan.", halign="left", valign="top", font_size="13sp")
        self.add_widget(self.status_label)
        self.add_widget(self.detail_label)
        self.bind(size=self._sync_text_size)

    def update(self, status: str, detail: str) -> None:
        self.status_label.text = status
        self.detail_label.text = detail

    def _sync_text_size(self, *_args) -> None:
        self.status_label.text_size = self.size
        self.detail_label.text_size = self.size
