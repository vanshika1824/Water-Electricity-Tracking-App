[app]

# (str) Title of your application
title = AquaWatt

# (str) Package name
package.name = aquawatt

# (str) Package domain (needed for android/ios packaging)
package.domain = org.aquawatt

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,ttf,txt

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, .venv, screenshots, __pycache__, .pytest_cache

# (list) List of exclusions using pattern matching
source.exclude_patterns = *.pyc, *.pyo, *~, .theme_pref.json, *.zip

# (str) Application versioning (method 1)
version = 2.4.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.1,kivymd==2.0.0,requests,urllib3,certifi,charset-normalizer,idna,pillow,materialyoucolor,materialshapes,asynckivy,asyncgui

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen
fullscreen = 0

# (string) Presplash background color (for new android toolchain)
android.presplash_color = #0A0F1D

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/logo_droplet.png

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# (int) Target Android API, should be as high as possible (>= 31)
android.api = 34

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android NDK API to use. This is the minimum API your code will compile against.
android.ndk_api = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (bool) automatically accept SDK licence
android.accept_sdk_license = True

# (str) The format used to package the app for release mode (aab or apk or default).
android.release_artifact = apk

# (str) The format used to package the app for debug mode (apk or aar).
android.debug_artifact = apk

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
