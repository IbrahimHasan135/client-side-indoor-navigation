from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from app.models.scan_snapshot import ScanSnapshot
from app.ui.widgets.anchor_row import AnchorRow
from app.ui.widgets.status_bar import StatusBar


class MainScreen(BoxLayout):
    def __init__(self, scan_controller, **kwargs) -> None:
        super().__init__(orientation="vertical", padding=dp(16), spacing=dp(12), **kwargs)
        self._scan_controller = scan_controller
        self._scan_controller.set_ui_update_callback(self.render_snapshot)

        self.status_bar = StatusBar()
        self.start_button = Button(text="Start Scan", size_hint_y=None, height=dp(48))
        self.stop_button = Button(text="Stop Scan", size_hint_y=None, height=dp(48), disabled=True)
        self.summary_grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(160))
        self.position_label = Label(text="Posisi: -", size_hint_y=None, height=dp(36), halign="left")
        self.debug_label = Label(text="Diagnostik: -", size_hint_y=None, height=dp(92), halign="left", valign="top")
        self.anchor_list = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
        self.anchor_scroll = ScrollView()

        self._build_layout()
        self._bind_events()
        self.render_snapshot(self._scan_controller.snapshot(), None)

    def _build_layout(self) -> None:
        self.add_widget(self._make_title())
        self.add_widget(self.status_bar)

        button_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(48))
        button_row.add_widget(self.start_button)
        button_row.add_widget(self.stop_button)
        self.add_widget(button_row)

        self.summary_labels = {
            "anchors": self._add_metric("Anchor Aktif", "0"),
            "nearest": self._add_metric("Beacon Terdekat", "-"),
            "rssi": self._add_metric("RSSI Terdekat", "-"),
            "distance": self._add_metric("Estimasi Jarak", "-"),
        }
        self.add_widget(self.summary_grid)

        self.position_label.bind(size=lambda widget, _size: setattr(widget, "text_size", widget.size))
        self.debug_label.bind(size=lambda widget, _size: setattr(widget, "text_size", widget.size))
        self.add_widget(self.position_label)
        self.add_widget(self.debug_label)

        self.anchor_scroll.add_widget(self.anchor_list)
        self.add_widget(self.anchor_scroll)

    def _bind_events(self) -> None:
        self.start_button.bind(on_release=lambda _button: self._start_scan())
        self.stop_button.bind(on_release=lambda _button: self._stop_scan())

    def _make_title(self) -> Label:
        label = Label(
            text="BLE Indoor Navigation",
            bold=True,
            font_size="24sp",
            size_hint_y=None,
            height=dp(40),
            halign="left",
            valign="middle",
        )
        label.bind(size=lambda widget, _size: setattr(widget, "text_size", widget.size))
        return label

    def _add_metric(self, title: str, value: str) -> Label:
        label = Label(text=f"{title}\n[b]{value}[/b]", markup=True, halign="left", valign="middle")
        label.bind(size=lambda widget, _size: setattr(widget, "text_size", widget.size))
        self.summary_grid.add_widget(label)
        return label

    def _start_scan(self) -> None:
        self.start_button.disabled = True
        self.stop_button.disabled = False
        self._scan_controller.start_scan()

    def _stop_scan(self) -> None:
        self._scan_controller.stop_scan()
        self.start_button.disabled = False
        self.stop_button.disabled = True

    def render_snapshot(self, snapshot: ScanSnapshot, status_message: str | None = None) -> None:
        status = status_message or snapshot.scan_state
        detail = snapshot.last_error or self._detail_text(snapshot)
        self.status_bar.update(status, detail)

        nearest = snapshot.anchors[0] if snapshot.anchors else None
        self.summary_labels["anchors"].text = f"Anchor Aktif\n[b]{len([item for item in snapshot.anchors if not item.stale])}[/b]"
        self.summary_labels["nearest"].text = f"Beacon Terdekat\n[b]{nearest.anchor_id if nearest else '-'}[/b]"
        self.summary_labels["rssi"].text = f"RSSI Terdekat\n[b]{self._format_rssi(nearest.filtered_rssi if nearest else None)}[/b]"
        self.summary_labels["distance"].text = f"Estimasi Jarak\n[b]{self._format_distance(nearest.distance_m if nearest else None)}[/b]"

        position = snapshot.position
        if position and position.x is not None and position.y is not None:
            self.position_label.text = f"Posisi: X={position.x} m, Y={position.y} m | {position.quality}"
        else:
            self.position_label.text = f"Posisi: {position.quality if position else '-'}"

        self.debug_label.text = (
            "Diagnostik:\n"
            f"Permission={snapshot.permission_state} | Bluetooth={snapshot.bluetooth_enabled}\n"
            f"BLE={snapshot.raw_ble_packets} | ESP={snapshot.accepted_esp_packets} | "
            f"Ditolak={snapshot.rejected_packets} | RSSI kosong={snapshot.missing_rssi_packets}"
        )

        self._render_anchors(snapshot.anchors)

    def _render_anchors(self, anchors) -> None:
        self.anchor_list.clear_widgets()
        self.anchor_list.height = max(dp(56), dp(56) * max(len(anchors), 1))
        if not anchors:
            self.anchor_list.add_widget(Label(text="Belum ada anchor ESP32-C6 yang diterima.", size_hint_y=None, height=dp(56)))
            return

        for anchor in anchors:
            self.anchor_list.add_widget(AnchorRow(anchor))

    def _detail_text(self, snapshot: ScanSnapshot) -> str:
        if snapshot.scan_state == "idle":
            return "Tap Start Scan untuk membaca advertisement BLE ESP32-C6."
        if snapshot.scan_state == "scanning" and snapshot.raw_ble_packets == 0:
            return "Scan aktif. Menunggu advertisement BLE dari Android callback."
        if snapshot.accepted_esp_packets == 0 and snapshot.raw_ble_packets > 0:
            return "BLE sekitar masuk, tapi belum ada payload ESP32-C6 yang cocok."
        if snapshot.accepted_esp_packets > 0:
            return "RSSI ESP32-C6 masuk tanpa pairing dan tanpa connect."
        return "Menunggu data BLE."

    def _format_rssi(self, value: int | float | None) -> str:
        return "-" if value is None else f"{value} dBm"

    def _format_distance(self, value: float | None) -> str:
        return "-" if value is None else f"{value} m"
