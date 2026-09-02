# Arsitektur & Struktur File Android APK (Python Kivy / BLE Indoor Navigation)

Dokumen ini menjelaskan rancangan arsitektur untuk aplikasi Android berbasis **Python Kivy** yang bertugas membaca banyak anchor ESP32-C6 lewat BLE scanning, mengambil RSSI, lalu menghitung estimasi posisi indoor. Fokus aplikasi ini adalah **passive multi-beacon scanning**, bukan pairing, bukan connect ke satu device, dan bukan memilih satu BLE seperti flow Web Bluetooth browser.

Target awal proyek ini adalah POC Android APK untuk membuktikan bahwa konsep indoor navigation dapat berjalan lebih reliable dibanding website, karena APK native bisa memakai Android BLE API langsung melalui `BluetoothLeScanner`.

## 1. Tujuan Sistem

Aplikasi Android berperan sebagai receiver seperti GPS client:

1. Aplikasi meminta izin Bluetooth dan lokasi sesuai aturan Android.
2. Aplikasi menjalankan BLE scan secara pasif.
3. Aplikasi menerima banyak advertisement dari anchor ESP32-C6.
4. Setiap advertisement dibaca sebagai sample RSSI.
5. Sample RSSI disimpan per anchor berdasarkan iBeacon `major:minor` atau identitas stabil lain.
6. RSSI difilter agar tidak terlalu loncat.
7. Jarak diperkirakan dari RSSI.
8. Posisi pengguna dihitung dari kumpulan anchor yang aktif.
9. UI menampilkan anchor aktif, RSSI raw, RSSI filtered, jarak, dan estimasi posisi.

## 2. Batasan Penting Android

Android native lebih cocok untuk kasus ini daripada website, tetapi tetap ada permission dan policy yang harus dipenuhi.

1. BLE scan dilakukan dengan Android API `BluetoothLeScanner.startScan(...)`.
2. Hasil scan datang melalui callback `ScanCallback`, biasanya berisi device, RSSI, dan `ScanRecord`.
3. Android 12/API 31 ke atas membutuhkan runtime permission `BLUETOOTH_SCAN`.
4. Karena aplikasi ini memakai RSSI BLE untuk memperkirakan posisi fisik indoor, aplikasi harus memperlakukan scan result sebagai data lokasi. Jangan memakai klaim `neverForLocation` untuk fitur indoor navigation ini.
5. Untuk Android 11/API 30 ke bawah, BLE scan masih bergantung pada permission lokasi seperti `ACCESS_FINE_LOCATION`.
6. Aplikasi harus meminta permission dari UI/controller layer, bukan dari driver secara tersembunyi.
7. Background scanning harus dianggap fase lanjutan. POC awal berjalan foreground saat aplikasi terbuka.

## 3. Konsep Arsitektur

Arsitektur mengikuti pola yang mirip dengan firmware ESP32: **Controller -> Service -> Driver**. Dependency bergerak satu arah. Driver tidak boleh tahu UI. Service tidak boleh membuat driver sendiri. Controller/main bertugas membuat object dan menyambungkan dependensi.

### A. Driver Layer

Driver adalah lapisan paling dekat dengan Android API.

Peran:

1. Membungkus API Android BLE dari Java/Kotlin melalui PyJNIus dan Java shim kecil jika API membutuhkan abstract class.
2. Menjalankan `BluetoothLeScanner.startScan(...)`.
3. Menghentikan scan dengan `stopScan(...)`.
4. Mengubah callback Java `ScanResult` menjadi data mentah Python.
5. Tidak menghitung jarak.
6. Tidak menyimpan state UI.
7. Tidak memanggil screen Kivy.

Contoh class:

```text
BleScannerDriver
AndroidPermissionDriver
AndroidBluetoothAdapterDriver
```

Aturan driver:

1. Driver harus berbentuk class.
2. Driver boleh import `jnius`, `android`, atau class Java Android.
3. Driver tidak boleh import `kivy.uix`, `Screen`, `Label`, atau widget UI.
4. Driver tidak boleh membuat object service.
5. Driver hanya emit raw event lewat callback/interface yang diberikan dari luar.

Catatan implementasi BLE:

`android.bluetooth.le.ScanCallback` adalah abstract Java class. PyJNIus `PythonJavaClass` hanya cocok untuk implement Java interface, bukan subclass abstract Java class. Karena itu project APK memakai Java shim `BleScanBridge` yang extend `ScanCallback`, lalu Python mengimplementasikan interface `BleAdvertisementListener`.

### B. Service Layer

Service adalah lapisan logika aplikasi.

Peran:

1. Menerima raw BLE advertisement dari driver.
2. Parsing payload iBeacon.
3. Filter anchor yang valid.
4. Menyimpan RSSI buffer per anchor.
5. Menghitung RSSI filtered, jarak, dan status stale.
6. Menghitung estimasi posisi.
7. Menyediakan snapshot data untuk controller/UI.

Contoh class:

```text
BeaconScanService
IBeaconParserService
RssiFilterService
DistanceEstimatorService
PositionEstimatorService
AnchorRegistryService
```

Aturan service:

1. Service harus berbentuk class.
2. Service tidak boleh membuat driver sendiri.
3. Driver harus diinjeksi lewat constructor.
4. Service tidak boleh import widget Kivy.
5. Service boleh punya state domain, misalnya map anchor, sample count, last seen, dan EMA RSSI.
6. Service harus mudah dites tanpa Android device selama input raw advertisement bisa disimulasikan.

### C. Controller Layer

Controller adalah jembatan antara aplikasi Kivy dan service.

Peran:

1. Menerima event dari UI seperti tombol Start/Stop Scan.
2. Meminta permission Android lewat permission driver.
3. Membuat dan menghubungkan object driver/service.
4. Memanggil service untuk start/stop scan.
5. Mengambil snapshot service secara berkala.
6. Mengirim data ke ViewModel atau langsung ke screen Kivy.

Contoh class:

```text
AppController
ScanController
PermissionController
```

Aturan controller:

1. Controller boleh tahu UI dan service.
2. Controller boleh memanggil `Clock.schedule_interval(...)`.
3. Controller boleh menangani pesan error untuk ditampilkan ke UI.
4. Controller adalah tempat orchestration, bukan tempat parsing iBeacon atau rumus RSSI.

### D. UI Layer

UI adalah lapisan Kivy screen/widget.

Peran:

1. Menampilkan tombol Start/Stop Scan.
2. Menampilkan status permission.
3. Menampilkan daftar anchor aktif.
4. Menampilkan raw RSSI, filtered RSSI, jarak, sample count, dan last seen.
5. Menampilkan estimasi posisi.

Aturan UI:

1. UI tidak boleh memanggil Android BLE API langsung.
2. UI tidak boleh parsing payload BLE.
3. UI hanya memanggil controller.
4. UI menerima data siap-render dari controller atau ViewModel.

## 4. Struktur Direktori

Struktur awal yang direkomendasikan:

```text
ble-node-apk/
├── README.md
├── buildozer.spec                 # Konfigurasi build APK
├── main.py                        # Entry point Kivy, membuat object utama
├── android_src/                   # Java shim Android untuk ScanCallback
│   └── org/indoor/navigation/
│       ├── BleAdvertisementListener.java
│       └── BleScanBridge.java
├── app/
│   ├── __init__.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── app_controller.py
│   │   ├── scan_controller.py
│   │   └── permission_controller.py
│   ├── drivers/
│   │   ├── __init__.py
│   │   ├── android_ble_scanner_driver.py
│   │   ├── android_bluetooth_adapter_driver.py
│   │   └── android_permission_driver.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── anchor.py
│   │   ├── ble_advertisement.py
│   │   └── position.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── anchor_registry_service.py
│   │   ├── beacon_scan_service.py
│   │   ├── distance_estimator_service.py
│   │   ├── ibeacon_parser_service.py
│   │   ├── position_estimator_service.py
│   │   └── rssi_filter_service.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_screen.py
│   │   └── widgets/
│   │       ├── __init__.py
│   │       ├── anchor_row.py
│   │       └── status_bar.py
│   └── utils/
│       ├── __init__.py
│       ├── constants.py
│       └── logger.py
└── docs/
    └── kivy_android_architecture.md
```

## 5. Dependency Injection & Object Ownership

Object dibuat di `main.py` atau `AppController`. Service dan driver tidak boleh membuat dependensi berat sendiri.

Contoh alur object:

```python
permission_driver = AndroidPermissionDriver()
bluetooth_adapter_driver = AndroidBluetoothAdapterDriver()
ble_scanner_driver = AndroidBleScannerDriver(bluetooth_adapter_driver)

ibeacon_parser = IBeaconParserService()
rssi_filter = RssiFilterService()
distance_estimator = DistanceEstimatorService()
position_estimator = PositionEstimatorService()
anchor_registry = AnchorRegistryService(rssi_filter, distance_estimator)

beacon_scan_service = BeaconScanService(
    ble_scanner_driver,
    ibeacon_parser,
    anchor_registry,
    position_estimator,
)

scan_controller = ScanController(permission_driver, beacon_scan_service)
```

Rule:

1. `main.py` atau controller boleh membuat object.
2. `BeaconScanService` menerima `AndroidBleScannerDriver`, bukan membuat sendiri.
3. `AndroidBleScannerDriver` tidak boleh tahu ada `BeaconScanService`.
4. Komunikasi driver ke service dilakukan lewat callback yang diset oleh service/controller.

## 6. BLE Scan Flow

Flow normal:

1. User tap **Start Scan**.
2. `MainScreen` memanggil `ScanController.start_scan()`.
3. `ScanController` meminta permission melalui `PermissionController`.
4. Jika permission granted, `ScanController` memanggil `BeaconScanService.start()`.
5. `BeaconScanService` memasang callback ke `BleScannerDriver`.
6. `BleScannerDriver` menjalankan Android `BluetoothLeScanner.startScan(...)`.
7. Android mengirim `ScanResult`.
8. Driver mengubah `ScanResult` menjadi `BleAdvertisement`.
9. Service parsing iBeacon dan update anchor registry.
10. Controller mengambil snapshot berkala.
11. UI merender snapshot.

Flow stop:

1. User tap **Stop Scan**.
2. Controller memanggil `BeaconScanService.stop()`.
3. Service memanggil `BleScannerDriver.stop_scan()`.
4. Driver memanggil Android `BluetoothLeScanner.stopScan(...)`.
5. UI menampilkan status stopped.

## 7. Data Model Minimum

### BleAdvertisement

```python
@dataclass
class BleAdvertisement:
    address: str
    name: str | None
    rssi: int
    tx_power: int | None
    manufacturer_data: dict[int, bytes]
    service_data: dict[str, bytes]
    timestamp_ms: int
```

### Anchor

```python
@dataclass
class Anchor:
    anchor_id: str
    major: int
    minor: int
    address: str
    name: str | None
    raw_rssi: int
    filtered_rssi: float
    distance_m: float | None
    sample_count: int
    last_seen_ms: int
    stale: bool
```

### Position

```python
@dataclass
class Position:
    x: float | None
    y: float | None
    quality: str
    anchor_count: int
```

## 8. Anchor Identification

Identitas anchor tidak boleh bergantung pada nama device saja, karena banyak ESP bisa memakai nama sama.

Prioritas identitas:

1. iBeacon `major:minor`.
2. Jika payload iBeacon tidak tersedia, fallback sementara ke BLE MAC address.
3. Nama device hanya untuk display, bukan ID utama.

Kontrak iBeacon ESP32-C6:

```text
Company ID : 0x004C
Type       : 0x02
Length     : 0x15
UUID       : fda50693-a4e2-4fb1-afcf-c6eb07647825
Major      : area/floor/group
Minor      : anchor unik per board
Tx Power   : measured power at 1 meter
```

## 9. Permission Rule

Permission harus ditangani sebagai fitur utama, bukan tempelan.

Manifest/build config minimal:

```text
BLUETOOTH
BLUETOOTH_ADMIN
BLUETOOTH_SCAN
BLUETOOTH_CONNECT
ACCESS_FINE_LOCATION
ACCESS_COARSE_LOCATION
```

Catatan:

1. Untuk Android 12+, `BLUETOOTH_SCAN` adalah runtime permission.
2. Untuk Android 11 ke bawah, BLE scan membutuhkan permission lokasi.
3. Karena aplikasi indoor navigation memakai RSSI untuk lokasi, jangan deklarasikan `BLUETOOTH_SCAN` dengan `neverForLocation`.
4. UI harus menjelaskan bahwa permission dipakai untuk membaca beacon indoor, bukan pairing.
5. POC awal tidak menggunakan background location.

## 10. Threading & Kivy Clock

Callback Android BLE tidak boleh langsung memodifikasi widget Kivy jika callback datang dari thread non-UI.

Rule:

1. Driver menerima callback Android.
2. Driver mengirim data mentah ke service.
3. Service update state internal.
4. Controller menjadwalkan update UI dengan `Clock.schedule_interval(...)`.
5. Semua perubahan widget dilakukan di main thread Kivy.

## 11. Logging & Diagnostics

Aplikasi harus punya diagnosa yang mirip website POC, tetapi lebih eksplisit.

Minimal counter:

```text
scan_state
permission_state
bluetooth_enabled
raw_ble_packets
accepted_esp_packets
rejected_packets
missing_rssi_packets
last_error
last_event_age_ms
```

Minimal log event:

```text
[Permission] requested: BLUETOOTH_SCAN, ACCESS_FINE_LOCATION
[Permission] granted/denied
[BLE] adapter enabled/disabled
[BLE] scan started
[BLE] scan failed: error_code
[BLE] advertisement received: address, name, rssi, manufacturer keys
[BLE] accepted anchor: major, minor, rssi
[BLE] rejected advertisement: reason
```

## 12. Buildozer / python-for-android Notes

Build awal direkomendasikan memakai Buildozer yang membungkus python-for-android.

Konsep awal `buildozer.spec`:

```text
requirements = python3,kivy,pyjnius,android
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.api = 35
android.minapi = 23
android.ndk_api = 23
```

Jika permission butuh atribut khusus yang tidak bisa ditulis langsung lewat `android.permissions`, gunakan manifest template/custom XML pada fase implementasi.

## 13. Aturan Pengembangan Wajib

1. Driver, service, controller wajib class-based.
2. `main.py` hanya bootstrap aplikasi dan wiring dependency.
3. Driver tidak boleh import service.
4. Service tidak boleh import UI/Kivy widget.
5. UI tidak boleh import PyJNIus Android BLE class.
6. BLE scanning tidak boleh connect/pair ke satu device.
7. RSSI harus disimpan sebagai stream sample per anchor.
8. Nama BLE tidak boleh dijadikan ID utama.
9. Semua permission failure harus terlihat di UI.
10. Semua BLE scan error code harus dilog.
11. Background scan tidak boleh ditambahkan sebelum foreground scan stabil.
12. Jangan memakai global singleton untuk driver/service kecuali ada alasan teknis yang ditulis di docs.
13. Jangan menjalankan scan dari import-time code.
14. Jangan update widget dari callback Android langsung.
15. Semua rumus RSSI/distance harus berada di service, bukan controller.

## 14. Roadmap Implementasi

### Phase 1 - Skeleton APK

1. Buat struktur folder.
2. Buat Kivy main screen sederhana.
3. Buat controller dan object wiring.
4. Buat permission flow.
5. Tampilkan status permission dan Bluetooth adapter.

### Phase 2 - BLE Scan Native Android

1. Implement `AndroidBleScannerDriver`.
2. Implement PyJNIus wrapper untuk `BluetoothLeScanner`.
3. Implement `ScanCallback`.
4. Tampilkan raw BLE count dan RSSI.
5. Pastikan tidak ada connect/pair flow.

### Phase 3 - ESP32-C6 Anchor Filtering

1. Parse manufacturer data.
2. Decode iBeacon major/minor/tx power.
3. Filter UUID proyek.
4. Tampilkan daftar anchor aktif.

### Phase 4 - RSSI Processing

1. Implement EMA filter.
2. Hitung jarak estimasi.
3. Tandai anchor stale.
4. Tambahkan sample count.

### Phase 5 - Indoor Position Estimate

1. Buat registry posisi anchor statis.
2. Implement weighted centroid untuk POC.
3. Tambah trilateration sederhana setelah minimal tiga anchor stabil.
4. Tampilkan confidence/quality.

### Phase 6 - Industrial Readiness

1. Stabilkan permission copy.
2. Tambah export log.
3. Tambah calibration mode.
4. Tambah device compatibility checklist.
5. Baru evaluasi background scan/foreground service jika memang diperlukan.

## 15. Acceptance Criteria POC

POC dianggap berhasil jika:

1. APK terinstall di Android.
2. User memberi permission Bluetooth/location.
3. Tombol Start Scan menjalankan BLE scan tanpa pairing.
4. Minimal dua ESP32-C6 beacon dengan nama sama tetap tampil sebagai anchor berbeda.
5. RSSI raw tampil dan berubah realtime.
6. RSSI filtered tampil per anchor.
7. Anchor stale hilang atau ditandai setelah tidak terdengar.
8. Tidak ada dependency ke browser Web Bluetooth.
9. Tidak ada dependency ke Python server lokal di laptop.
10. Build dan runtime log bisa menjelaskan jika scan gagal karena permission, Bluetooth off, atau Android BLE error code.

## 16. Referensi Utama

1. Android `BluetoothLeScanner`: API native untuk BLE scan dengan callback `ScanCallback`.
2. Android Bluetooth permissions: permission Android 12+ seperti `BLUETOOTH_SCAN`, `BLUETOOTH_CONNECT`, dan relasi dengan location.
3. python-for-android runtime permissions: cara meminta permission dari aplikasi Python Android.
4. python-for-android services: referensi fase lanjutan jika nanti butuh foreground/background service.
