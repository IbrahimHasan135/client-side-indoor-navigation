from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from app.models.anchor import Anchor


class AnchorRow(BoxLayout):
    def __init__(self, anchor: Anchor, **kwargs) -> None:
        super().__init__(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(56), **kwargs)
        self.add_widget(self._make_label(anchor.anchor_id, bold=True))
        self.add_widget(self._make_label(anchor.address))
        self.add_widget(self._make_label(self._format_rssi(anchor.raw_rssi)))
        self.add_widget(self._make_label(self._format_rssi(anchor.filtered_rssi)))
        self.add_widget(self._make_label(self._format_distance(anchor.distance_m)))
        self.add_widget(self._make_label(str(anchor.sample_count)))

    def _make_label(self, text: str, bold: bool = False) -> Label:
        label = Label(text=text, bold=bold, halign="left", valign="middle", shorten=True)
        label.bind(size=lambda widget, _size: setattr(widget, "text_size", widget.size))
        return label

    def _format_rssi(self, value: int | float | None) -> str:
        return "-" if value is None else f"{value} dBm"

    def _format_distance(self, value: float | None) -> str:
        return "-" if value is None else f"{value} m"
