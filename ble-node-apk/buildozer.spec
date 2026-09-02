[app]
title = BLE Indoor Navigation
package.name = blenode
package.domain = org.indoor.navigation
source.dir = .
source.include_exts = py,kv,png,jpg,atlas,java
version = 0.1.0
requirements = python3,kivy,pyjnius,android
orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 23
android.ndk_api = 23
android.archs = arm64-v8a
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.add_src = android_src
android.allow_backup = False
android.logcat_filters = *:S python:D BLE:D Permission:D

[buildozer]
log_level = 2
warn_on_root = 1
