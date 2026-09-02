# Arsitektur & Struktur File ESP32 (ESP-IDF 5.5.4)

Dokumen ini menjelaskan rancangan arsitektur, struktur direktori, dan aturan pengembangan untuk *firmware* ESP32 yang bertindak sebagai BLE Beacon menggunakan *framework* ESP-IDF versi 5.5.4. Pendekatan utama yang digunakan adalah **Modularitas** dan **Pemrograman Berorientasi Objek (OOP) dengan C++**.

## 1. Konsep Arsitektur (Layering)

Arsitektur sistem dibagi menjadi tiga lapisan utama dengan alur ketergantungan (dependency) yang ketat secara satu arah: **Controller -> Service -> Driver**.

### A. Driver Layer (Lapisan Perangkat Keras)
*   **Peran**: Bertanggung jawab langsung berinteraksi dengan API ESP-IDF dan *hardware* (misal: Register Bluetooth, GPIO, Timer).
*   **Karakteristik**: Berupa **Class (OOP)** murni. Tidak mengandung *business logic* (logika aplikasi). Driver hanya menyediakan antarmuka abstrak bagi perangkat keras.
*   **Contoh**: `BleRadioDriver` (menginisialisasi radio, mengatur *transmit power*), `LedDriver` (menghidupkan/mematikan LED).

### B. Service Layer (Lapisan Logika)
*   **Peran**: Membungkus Driver dan memberikan *business logic* yang spesifik.
*   **Karakteristik**: Berupa **Class (OOP)**. Service *tidak* membuat (instantiate) objek Driver sendiri. Objek Driver akan diinjeksi (*Dependency Injection*) ke dalam Service oleh Controller melalui *constructor*. Service mengendalikan murni Driver yang dimilikinya dan tidak boleh mengambil alih kontrol Driver milik Service lain.
*   **Contoh**: `BeaconBroadcasterService` (menerima `BleRadioDriver`, mengatur interval, membentuk *payload* data, lalu memerintahkan driver untuk *broadcast*).

### C. Controller Layer (Lapisan Orkestrasi & FreeRTOS)
*   **Peran**: Titik awal (*entry point*) aplikasi (`main.cpp`). 
*   **Karakteristik**: Bertanggung jawab untuk melakukan inisialisasi awal (*Bootstrapping*). Di sinilah objek-objek diciptakan. Controller juga merupakan tempat di mana *Task* FreeRTOS dibuat.
*   **Alur Inisialisasi**:
    1. Controller membuat (*create*) objek-objek **Driver**.
    2. Controller membuat objek-objek **Service** dengan mengoper (melalui *constructor*) objek Driver yang telah dibuat.
    3. Controller membuat **FreeRTOS Task** untuk masing-masing fungsi agar setiap tugas berjalan independen.

## 2. Struktur File dan Direktori

Direktori proyek akan diatur sedemikian rupa agar mematuhi kaidah modularitas di atas:

```text
ble-beacon-pointing/
├── CMakeLists.txt              # Build system utama
├── sdkconfig                   # Konfigurasi ESP-IDF
├── docs/                       # Dokumentasi
│   └── esp32_architecture.md   # File ini
└── main/                       # Folder kode sumber utama
    ├── CMakeLists.txt          # Build system untuk komponen main
    ├── main.cpp                # Controller Layer (Entry point & FreeRTOS Tasks)
    ├── drivers/                # Kumpulan Class Driver
    │   ├── ble_radio_driver.hpp
    │   ├── ble_radio_driver.cpp
    │   ├── led_driver.hpp
    │   └── led_driver.cpp
    ├── services/               # Kumpulan Class Service
    │   ├── beacon_service.hpp
    │   ├── beacon_service.cpp
    │   ├── indicator_service.hpp
    │   └── indicator_service.cpp
    └── utils/                  # Fungsi-fungsi pembantu umum
        └── constants.hpp       # Definisi UUID, TxPower, dll.
```

## 3. Konsep FreeRTOS

Setiap tugas (*task*) yang beroperasi secara kontinu akan memiliki FreeRTOS *Task*-nya sendiri.
*   **Isolasi Tugas**: Misalnya, ada satu Task khusus untuk *Beacon Broadcasting* dan satu Task khusus untuk *System Health/Blinking LED*.
*   **Komunikasi Antar Task**: Apabila Service satu perlu mengirim data ke Service lain, hal ini dijembatani oleh mekanisme bawaan FreeRTOS (*Queue*, *Semaphore*, atau *Event Group*) agar *thread-safe*.
*   **Non-Blocking**: Main function (`app_main`) di Controller hanya bertugas menyusun komponen dan *spawn* (membuat) FreeRTOS Tasks, setelah itu `app_main` akan kembali (return) atau menjadi *Idle Task*.

## 4. Aturan Pengembangan (Development Rules)

Untuk menjaga agar arsitektur ini tidak berantakan di kemudian hari, pengembang **harus** mematuhi aturan berikut:

1. **Bahasa C++**: Karena menggunakan konsep OOP (Class dan Object), kode dalam direktori `main/` menggunakan bahasa C++ (`.cpp` dan `.hpp`). Pastikan `app_main` dibungkus dengan `extern "C"`.
2. **Dependency Injection**: Jangan pernah melakukan inisialisasi Driver (`new BleRadioDriver()`) di dalam file *Service*. Driver harus dilempar dari `main.cpp` ke konstruktor Service.
    *   *Salah*: `class BeaconService { BleRadioDriver driver = new BleRadioDriver(); }`
    *   *Benar*: `class BeaconService { public: BeaconService(BleRadioDriver* driver) {...} }`
3. **Pure Control**: Sebuah Service secara prinsipil mengendalikan dan bertanggung jawab penuh atas *state* (kondisi) dari Driver yang dimilikinya. 
4. **Isolasi Hardware**: File `.cpp` di dalam folder `services/` dan `main.cpp` **tidak boleh** memanggil `#include <esp_bt.h>` atau register ESP-IDF secara langsung. Semua interaksi ESP-IDF API secara hardware murni harus dilakukan di dalam file `drivers/`.
5. **No God Classes**: Jangan membuat Service yang mengatur segalanya. Pisahkan fungsi dengan tegas (misal: Service untuk BLE terpisah dari Service untuk Sensor).

