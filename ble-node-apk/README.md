# BLE Node APK

Android APK POC untuk BLE indoor navigation berbasis Python Kivy.

Dokumen utama:

- [Arsitektur Android Kivy](docs/kivy_android_architecture.md)

Target konsep:

1. Scan banyak BLE advertisement dari anchor ESP32-C6.
2. Baca RSSI tanpa pairing dan tanpa connect ke satu device.
3. Pisahkan layer driver, service, controller, model, dan UI.
4. Gunakan object/class dan dependency injection seperti pola firmware ESP32.

## Cara Build

Install toolchain Buildozer/python-for-android dulu, lalu dari folder ini jalankan:

```bash
buildozer android debug
```

APK debug biasanya keluar di:

```text
bin/*.apk
```

Untuk install ke HP yang tersambung ADB:

```bash
buildozer android deploy run logcat
```

Catatan: aplikasi ini butuh Android runtime permission untuk Bluetooth scan dan lokasi. POC foreground dulu, belum background service.
