# client-side-indoor-navigation

Repository ini berisi POC indoor navigation client-side:

- `ble-beacon-pointing`: firmware ESP32-C6 BLE beacon.
- `ble-node-website`: POC website Web Bluetooth.
- `ble-node-apk`: POC Android APK berbasis Python Kivy.

Catatan build Kivy/Buildozer lintas project ada di [KIVY_BUILDOZER.md](KIVY_BUILDOZER.md).

Untuk APK Android, hasil build dan cache besar sudah di-ignore dari Git:

```text
ble-node-apk/.buildozer/
ble-node-apk/bin/
ble-node-apk/tools/
*.apk
*.aab
.venv/
```

Build ulang APK:

Kalau ini fresh clone dan folder `ble-node-apk/tools/python-for-android-v2024.01.21` belum ada, jalankan dulu setup p4a lokal yang ada di [ble-node-apk/README.md](ble-node-apk/README.md).

```bash
cd /home/ibrohim/Documents/github/client-side-indoor-navigation/ble-node-apk
deactivate 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
export PIP_BREAK_SYSTEM_PACKAGES=1
/home/ibrohim/.local/bin/buildozer android debug
```
