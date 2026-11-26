[app]
title = PKPDCL Bill Calculator
package.name = pkpdclbilling
package.domain = org.pkpdcl

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 8.1

requirements = python3,kivy==2.3.1,cython>=3.0.11,charset_normalizer<3.5,pillow,qrcode,fpdf2,fonttools

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 34
android.minapi = 24
android.ndk = 27c
android.accept_sdk_license = True
android.archs = arm64-v8a

icon.filename = %(source.dir)s/pkpdcl_logo.png

[buildozer]
log_level = 2
warn_on_root = 1
