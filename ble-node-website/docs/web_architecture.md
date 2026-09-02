# Arsitektur & Struktur File Website (PWA / Web Bluetooth)

Dokumen ini menjelaskan rancangan arsitektur, struktur direktori, dan aturan pengembangan untuk *frontend* berbasis *browser* (HTML/JS/CSS) yang akan menjadi *client* navigasi. Konsep utama yang digunakan adalah **Modularitas berbasis ES6 Modules**, pemisahan tanggung jawab (Separation of Concerns), dan kemudahan *maintainability*.

## 1. Konsep Arsitektur Web Modular

Sama seperti arsitektur mikrokontroler, aplikasi web ini juga tidak boleh disatukan dalam satu file `index.html` yang sangat panjang. Kode akan dipecah berdasarkan perannya menjadi tiga bagian utama (MVC/Service-based Pattern):

### A. Driver / API Layer
*   **Peran**: Bertanggung jawab langsung untuk memanggil antarmuka internal *browser*, terutama **Web Bluetooth API** (`navigator.bluetooth`).
*   **Karakteristik**: File murni berisi fungsi untuk *scanning* BLE atau mengambil data mentah dari API *browser*. Tidak ada modifikasi UI di sini.

### B. Service Layer (Data Processing)
*   **Peran**: Mesin pengolah data (*Brain*).
*   **Karakteristik**: Mengambil *raw data* (RSSI) dari Driver Layer dan menerapkan algoritma atau *business logic* (misalnya: Algoritma *Exponential Moving Average* untuk menghaluskan sinyal, kalkulasi konversi RSSI menjadi meter/jarak).

### C. Controller & UI Layer
*   **Peran**: Jembatan antara UI (HTML DOM) dengan Service Layer.
*   **Karakteristik**: Bertugas me-*listen* event interaktif (seperti klik dari tombol di HTML), memanggil fungsi di Service, lalu memperbarui tampilan web (`document.getElementById(...)`) berdasarkan hasil kalkulasi Service.

## 2. Struktur File dan Direktori

Pendekatan modular akan diterminologikan ke dalam bentuk struktur folder berikut:

```text
ble-node-website/
├── index.html                 # Struktur utama UI, memanggil main.js
├── css/
│   └── style.css              # File gaya/desain
├── docs/
│   └── web_architecture.md    # File ini
└── js/
    ├── main.js                # Entry Point (Module Orchestrator)
    ├── drivers/
    │   └── ble_scanner.js     # Driver untuk Web Bluetooth API
    ├── services/
    │   ├── rssi_filter.js     # Logika Smoothing EMA (Exponential Moving Average)
    │   ├── distance_calc.js   # Logika konversi RSSI dBm ke Meter
    │   └── navigation.js      # Logika orientasi ruang berdasarkan jarak beacon
    └── controllers/
        └── ui_controller.js   # Script memanipulasi DOM HTML & Event Listener
```

## 3. Konsep Eksekusi (Flow of Execution)

1. **Inisialisasi**: Web termuat. `index.html` memanggil modul utama dengan tag `<script type="module" src="js/main.js"></script>`.
2. **Setup**: `main.js` menginisialisasi `ui_controller.js` dan me-*wiring* berbagai dependensi jika ada.
3. **User Action**: Pengguna menekan tombol "Mulai Pindai". `ui_controller.js` menangkap event ini dan menginstruksikan `ble_scanner.js` (melalui *Service*) untuk meminta izin lokasi/bluetooth dari *browser*.
4. **Data Stream**: Saat `ble_scanner.js` menangkap sinyal BLE yang diiklankan, ia melempar datanya ke `rssi_filter.js` untuk dihaluskan, lalu ke `distance_calc.js` untuk diubah menjadi metrik jarak.
5. **Render**: *Service* memberikan data kalkulasi akhir secara berkala ke `ui_controller.js`, yang kemudian merender dan menulis hasilnya secara dinamis ke dalam elemen di DOM.

## 3.1 Implementasi Saat Ini

Implementasi website sekarang mengikuti flow persetujuan browser terlebih dahulu:

1. Pengguna menekan tombol **Minta Persetujuan BLE**.
2. Browser menampilkan dialog persetujuan Bluetooth.
3. Setelah disetujui, aplikasi menjalankan scan advertisement BLE.
4. ESP32 beacon difilter dari nama `BLE-NAV-ESP32*` atau payload iBeacon dengan Company ID `0x004C` dan UUID `fda50693-a4e2-4fb1-afcf-c6eb07647825`.
5. RSSI mentah dari browser difilter dengan Exponential Moving Average agar tampil lebih stabil.
6. Data disimpan dalam buffer per anchor, bukan koneksi ke satu device.
7. UI menampilkan jumlah anchor aktif, raw RSSI, EMA RSSI, estimasi jarak, jumlah sampel, last seen, dan estimasi posisi.

Catatan batasan browser:

- Website wajib memakai `navigator.bluetooth.requestLEScan()` karena mode ini bisa membaca banyak advertisement BLE dan RSSI secara langsung.
- Aplikasi tidak memakai `navigator.bluetooth.requestDevice()` karena API itu memilih satu device dan tidak cocok untuk indoor navigation multi-anchor.
- Web Bluetooth hanya berjalan pada secure context, yaitu HTTPS atau `localhost`.

## 4. Aturan Pengembangan (Development Rules)

Untuk menjamin kualitas dan modularitas kode HTML/JS, aturan berikut **harus** dipatuhi:

1. **Wajib ES6 Modules**: File Javascript saling terhubung dengan skema ekspor-impor modern (`import` dan `export`). Tidak diperkenankan meletakkan fungsi global secara implisit atau menggunakan fungsi pemanggil di atribut tag HTML (misalnya `<button onclick="doSomething()">`). Gunakan `addEventListener`.
2. **Isolasi DOM**: Hanya file-file di dalam direktori `controllers/` yang diizinkan untuk memanggil antarmuka pemanipulasi DOM (seperti `document.querySelector` atau `.innerHTML`). Lapisan *Driver* dan *Service* dilarang menyentuh antarmuka layar web.
3. **Pure Functions**: Pada lapisan *Service* (seperti penghitungan matematis RSSI), sebisa mungkin terapkan *pure functions* yang mana jika sebuah fungsi diberikan argumen tertentu (misal: RSSI = -60), maka ia selalu mengembalikan hasil (*return value*) yang sama tanpa me-mutasi status sistem eksternal. Hal ini sangat memudahkan *testing* dan mencegah *bug* asinkron.
4. **Asynchronous Handling**: Operasi Web Bluetooth pada *browser* bersifat asinkronus (*Promise-based*). Gunakan paradigma `async/await` dibandingkan pendekatan `Promise.then()` yang saling bersarang untuk mencegah *callback hell* dan membuat struktur kode lebih elegan.
5. **Responsif dan Bersih**: Pisahkan urusan styling layout, warna, dan posisi mutlak pada CSS. File HTML sebaiknya berfokus murni pada kerangka struktur dan semantiknya saja.
