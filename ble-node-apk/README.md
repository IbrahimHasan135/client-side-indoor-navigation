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

Status terakhir di mesin ini: **build debug berhasil** pada 2026-09-03.

APK yang sudah terbentuk:

```text
bin/blenode-0.1.0-arm64-v8a-debug.apk
```

Ukuran APK hasil verifikasi sekitar 19 MB. Isi APK juga sudah dicek cepat: `libpython3.11.so`, `libpybundle.so`, `classes.dex`, dan `assets/private.tar` ada; folder `tools/python-for-android...` tidak ikut masuk ke APK.

### Command Build Yang Dipakai

Untuk mesin ini, **jangan pakai `.venv` repo saat build APK**. Buildozer/python-for-android akan menjalankan `pip install --user` untuk dependency internal, sehingga `.venv` membuat proses build bentrok dengan user-site Python.

Folder hasil build seperti `.buildozer/`, `bin/`, APK, dan salinan p4a lokal `tools/` sudah di-ignore dari Git. Jadi aman untuk push source code tanpa ikut mengupload cache build yang ukurannya besar.

Keluar dulu dari `.venv` jika prompt masih diawali `(.venv)`:

```bash
deactivate 2>/dev/null || true
```

```bash
cd /home/ibrohim/Documents/github/client-side-indoor-navigation/ble-node-apk
export PATH="$HOME/.local/bin:$PATH"
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
export PIP_BREAK_SYSTEM_PACKAGES=1
/home/ibrohim/.local/bin/buildozer android debug
```

Kalau `buildozer` atau `cython` belum ada di `~/.local/bin`, install dulu dari luar `.venv`:

```bash
deactivate 2>/dev/null || true
python3 -m pip install --user --upgrade buildozer cython
```

Kalau ini fresh clone dari GitHub, siapkan dulu python-for-android lokal karena folder `tools/` memang tidak di-commit:

```bash
cd /home/ibrohim/Documents/github/client-side-indoor-navigation/ble-node-apk
mkdir -p tools
git clone --branch v2024.01.21 --single-branch https://github.com/kivy/python-for-android.git tools/python-for-android-v2024.01.21
sed -i 's/jcenter()/mavenCentral()/g' tools/python-for-android-v2024.01.21/pythonforandroid/bootstraps/common/build/templates/build.tmpl.gradle
```

APK debug biasanya keluar di:

```text
bin/*.apk
```

Untuk install ke HP yang tersambung ADB:

```bash
cd /home/ibrohim/Documents/github/client-side-indoor-navigation/ble-node-apk
export PATH="$HOME/.local/bin:$PATH"
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
export PIP_BREAK_SYSTEM_PACKAGES=1
/home/ibrohim/.local/bin/buildozer android deploy run logcat
```

Catatan: aplikasi ini butuh Android runtime permission untuk Bluetooth scan dan lokasi. POC foreground dulu, belum background service.

### Konfigurasi Build Penting

Build ini sengaja memakai:

```text
android.api = 35
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
p4a.source_dir = tools/python-for-android-v2024.01.21
source.exclude_dirs = .buildozer,bin,docs,tools
```

Alasannya:

1. `android.minapi` dan `android.ndk_api` harus 24 supaya native Python build tidak kena error API rendah.
2. `p4a.source_dir` diarahkan ke salinan lokal python-for-android `v2024.01.21` supaya build memakai Python 3.11.5, Kivy 2.3.0, dan Pyjnius 1.6.1.
3. Template Gradle di p4a lokal sudah dipatch dari `jcenter()` ke `mavenCentral()` karena JCenter timeout saat resolve dependency Gradle.
4. `source.exclude_dirs` wajib berisi `tools`, `.buildozer`, `docs`, dan `bin` supaya toolchain lokal tidak ikut masuk ke APK.

### Catatan Error Yang Sudah Didiagnosa

Jangan jalankan command build dari prompt `(.venv)`. Error yang sudah terbukti muncul:

```text
Cython (cython) not found
Can not perform a '--user' install. User site-packages are not visible in this virtualenv.
externally-managed-environment
```

Diagnosis: `../.venv/bin/buildozer` mencari `cython` di environment yang salah, lalu python-for-android bentrok karena butuh `pip install --user`. Solusinya pakai Buildozer user/global dari `~/.local/bin`, bukan Buildozer dari `.venv`.

Error lain yang sudah muncul dan fix-nya:

```text
checking for preadv... no
checking for pwritev... no
```

Fix: set `android.minapi = 24` dan `android.ndk_api = 24`.

```text
charset_normalizer-...-cp314-...whl is not a supported wheel on this platform
```

Fix: jangan pakai python-for-android master/2026 untuk POC ini. Build diarahkan ke p4a `v2024.01.21` lokal supaya Python Android yang dipakai adalah 3.11.5, bukan 3.14.

```text
LLVM ERROR: IO failure on output stream: No space left on device
```

Diagnosis: partisi `/dev/sda2` sempat tinggal sekitar 33 MB. Cache lama Python 3.14 dan NDK r28c dibersihkan, lalu free space naik. Untuk build ulang yang nyaman, sisakan minimal 8-10 GB kosong; lebih aman 15 GB.

```text
Unsupported class file major version 65
```

Diagnosis: Java default mesin adalah JDK 21. Gradle 8.0.2 dari stack ini tidak cocok jalan dengan JDK 21. Fix: paksa build memakai JDK 17 lewat `JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64`.

```text
Could not resolve ... jcenter.bintray.com ... Read timed out
```

Diagnosis: template Gradle p4a lama masih memakai `jcenter()`. Fix: salinan p4a lokal di `tools/python-for-android-v2024.01.21` sudah dipatch supaya `build.gradle` memakai `google()` dan `mavenCentral()`.

Kalau build pernah putus setelah ganti p4a/Python/toolchain dan mulai muncul error aneh dari cache, pindahkan cache build lokal dulu:

```bash
cd /home/ibrohim/Documents/github/client-side-indoor-navigation/ble-node-apk
mv .buildozer/android/platform/build-arm64-v8a .buildozer/android/platform/build-arm64-v8a.stale-$(date +%Y%m%d-%H%M%S)
```

Setelah itu jalankan lagi command build utama di atas.
