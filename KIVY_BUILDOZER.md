# Kivy Buildozer Android Build Notes

Catatan ini untuk project Kivy + Buildozer berikutnya supaya tidak mengulang error setup Android yang sama.

## Target Setup Yang Disarankan

Gunakan stack yang konservatif dan stabil:

```text
Host OS        : Linux/Ubuntu
Host Python    : Python 3.10 sampai 3.12
Buildozer      : 1.6.0
Cython         : 0.29.37
Java/JDK       : OpenJDK 17
Android SDK    : biarkan Buildozer install/manage
Android NDK    : r25b untuk python-for-android v2024.01.21
p4a            : python-for-android v2024.01.21
Android minapi : 24
Android ndk_api: 24
```

Buildozer boleh dijalankan dari sistem Python/user Python. Untuk build APK, jangan jalankan Buildozer dari `.venv` project karena python-for-android masih memakai beberapa proses `pip install --user`.

## Install Awal Di Mesin

Keluar dulu dari virtualenv:

```bash
deactivate 2>/dev/null || true
```

Install tool utama:

```bash
python3 -m pip install --user "buildozer==1.6.0"
python3 -m pip install --user "cython==0.29.37"
```

Pastikan binary user masuk `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Pastikan JDK 17 ada:

```bash
java -version
javac -version
ls -d /usr/lib/jvm/*17* 2>/dev/null
```

Kalau `java -version` default masih JDK 21, itu tidak masalah selama command build memaksa `JAVA_HOME` ke JDK 17.

## Template Command Build

Pakai pola ini di setiap project Kivy Android:

```bash
cd /path/to/kivy-project
deactivate 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
export PIP_BREAK_SYSTEM_PACKAGES=1
/home/ibrohim/.local/bin/buildozer android debug
```

Untuk install ke HP via ADB:

```bash
cd /path/to/kivy-project
deactivate 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
export PIP_BREAK_SYSTEM_PACKAGES=1
/home/ibrohim/.local/bin/buildozer android deploy run logcat
```

## Konfigurasi `buildozer.spec`

Minimal konfigurasi Android yang direkomendasikan:

```ini
[app]
source.dir = .
source.include_exts = py,kv,png,jpg,atlas,java
source.exclude_dirs = .buildozer,bin,docs,tools

requirements = python3,kivy,pyjnius,android

android.api = 35
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a

p4a.source_dir = tools/python-for-android-v2024.01.21
```

Untuk project yang butuh Java custom, tambahkan:

```ini
android.add_src = android_src
```

Untuk Bluetooth Android modern, contoh permission:

```ini
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
```

Permission di `buildozer.spec` hanya masuk manifest. Runtime permission tetap harus diminta dari aplikasi.

## Menyiapkan python-for-android Lokal

Untuk menghindari perubahan mendadak dari p4a master, clone versi yang jelas:

```bash
mkdir -p tools
git clone --branch v2024.01.21 --single-branch https://github.com/kivy/python-for-android.git tools/python-for-android-v2024.01.21
```

Patch template Gradle lama supaya tidak memakai JCenter:

```bash
sed -i 's/jcenter()/mavenCentral()/g' tools/python-for-android-v2024.01.21/pythonforandroid/bootstraps/common/build/templates/build.tmpl.gradle
```

Lalu di `buildozer.spec`:

```ini
p4a.source_dir = tools/python-for-android-v2024.01.21
```

Folder `tools/python-for-android-v2024.01.21` sebaiknya tidak di-commit ke Git karena itu dependency eksternal besar. Simpan command setup ini di README project.

## Git Ignore Yang Wajib

Tambahkan minimal:

```gitignore
.venv/
__pycache__/
*.py[cod]
.buildozer/
**/.buildozer/
bin/
**/bin/
*.apk
*.aab
.gradle/
**/.gradle/
tools/python-for-android-*/
```

Kalau `.venv` sudah terlanjur ke-track Git, `.gitignore` tidak akan otomatis menghapus dari index. Jalankan:

```bash
git rm -r --cached .venv
```

Command itu tidak menghapus folder `.venv` lokal, hanya mengeluarkannya dari tracking Git.

## Error Yang Sering Muncul

### `Cython (cython) not found`

Penyebab umum:

```text
Buildozer dijalankan dari .venv, tetapi cython yang dibutuhkan tidak terlihat di PATH Buildozer.
```

Fix:

```bash
deactivate 2>/dev/null || true
python3 -m pip install --user "cython==0.29.37"
export PATH="$HOME/.local/bin:$PATH"
```

### `Can not perform a '--user' install`

Penyebab:

```text
Buildozer/python-for-android berjalan di virtualenv, lalu mencoba pip install --user.
```

Fix: jangan build dari `.venv`. Pakai `~/.local/bin/buildozer`.

### `externally-managed-environment`

Penyebab: Ubuntu/Python modern menerapkan PEP 668.

Fix untuk build command:

```bash
export PIP_BREAK_SYSTEM_PACKAGES=1
```

### `checking for preadv... no` atau `checking for pwritev... no`

Penyebab: Android NDK API terlalu rendah untuk native Python yang sedang dibuild.

Fix:

```ini
android.minapi = 24
android.ndk_api = 24
```

### `charset_normalizer ... cp314 ... is not a supported wheel`

Penyebab: p4a master/versi baru memilih Python Android 3.14 dan dependency wheel Android belum cocok dengan pip host.

Fix: pin p4a ke versi stabil yang memakai Python 3.11.5, misalnya `v2024.01.21`.

### `Unsupported class file major version 65`

Penyebab: Gradle berjalan dengan JDK 21. Major version 65 adalah Java 21.

Fix:

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
```

### `Could not resolve ... jcenter.bintray.com ... Read timed out`

Penyebab: template Gradle lama masih memakai `jcenter()`.

Fix: patch template p4a dari `jcenter()` ke `mavenCentral()`.

### `No space left on device`

Build Android butuh ruang besar. Sisakan minimal 8-10 GB, lebih aman 15 GB.

Cache yang biasanya besar:

```bash
du -sh .buildozer ~/.buildozer ~/.gradle 2>/dev/null
```

Kalau cache build lokal rusak atau sudah tidak cocok:

```bash
mv .buildozer/android/platform/build-arm64-v8a .buildozer/android/platform/build-arm64-v8a.stale-$(date +%Y%m%d-%H%M%S)
```

## Checklist Project Baru

1. Buat project Kivy dan `buildozer.spec`.
2. Tambahkan `.gitignore` sebelum build pertama.
3. Install Buildozer dan Cython di user Python, bukan `.venv`.
4. Paksa JDK 17 saat build.
5. Set `android.minapi = 24` dan `android.ndk_api = 24`.
6. Pin p4a ke versi jelas.
7. Patch p4a template dari JCenter ke Maven Central jika memakai p4a lama.
8. Exclude `.buildozer`, `bin`, `docs`, dan `tools` dari source APK.
9. Pastikan storage kosong minimal 8-10 GB.
10. Build dengan command environment lengkap, bukan hanya `buildozer android debug`.
