# Inherit common mobile Lineage stuff
$(call inherit-product, vendor/lineage/config/common.mk)

# Include AOSP audio files
$(call inherit-product-if-exists, frameworks/base/data/sounds/AudioPackage14.mk)
include vendor/lineage/config/aosp_audio.mk

# Include Lineage audio files
include vendor/lineage/config/lineage_audio.mk

# Default notification/alarm sounds
PRODUCT_PRODUCT_PROPERTIES += \
    ro.config.notification_sound=Argon.ogg \
    ro.config.alarm_alert=Hassium.ogg

# Apps
PRODUCT_PACKAGES += \
    AvatarPicker \
    Backgrounds \
    Glimpse \
    LatinIME

# CubeOS: AppHub, the CubeOS app store (packages/apps/AppHub). CubeOS ships no Play Store.
# Cube Account (packages/apps/CubeAccount): the system-wide Cubemail account, the way the
# Google account works on other Android phones. AppHub and Settings sign in through it.
# Cubemail (packages/apps/Cubemail): the mail app, signed in with the Cube Account.
PRODUCT_PACKAGES += \
    AppHub \
    CubeAccount \
    Cubemail

# CubeOS: CubeDEX (packages/apps/CubeDEX), the Cube decentralised exchange.
PRODUCT_PACKAGES += \
    CubeDEX

# CubeOS: Cube Health (packages/apps/CubeOSApps/prebuilts/CubeHealth), activity rings, step
# counting and health logs on the phone, with Health Connect.
PRODUCT_PACKAGES += \
    CubeHealth

# CubeOS: Cube Watch (packages/apps/CubeOSApps/prebuilts/CubeWatch), the companion for ContiSX /
# Cube watches over Bluetooth LE (watch/PROTOCOL.md): notifications, calls, heart rate into
# Health, Shield SOS and live safety status on the wrist. Privileged, platform-signed.
PRODUCT_PACKAGES += \
    CubeWatch

# CubeOS: everyday tools (packages/apps/CubeOSApps/prebuilts), all on the phone, no accounts:
# Scanner (documents to searchable PDFs with on-device text recognition, signature stamp),
# Cube Tools (torch, magnifier, measure incl. camera tape, QR scanner), Notes (voice notes
# transcribed on the phone; no internet) and Cube Recorder (on-device transcription and the
# speech service Notes uses; replaces LineageOS Recorder).
PRODUCT_PACKAGES += \
    CubeScanner \
    CubeTools \
    CubeNotes \
    CubeRecorder

# CubeOS: system essentials (packages/apps/CubeOSApps/prebuilts): Files (file manager with Clean
# and Recently Deleted; DocumentsUI stays for the system picker), Battery (health, history, NEPA
# mode; persistent), Clipboard (encrypted history that never keeps passwords or codes;
# persistent), PDF Tools (the PDF viewer and editor), Cube Share (offline encrypted transfer),
# Screen Recorder, Screenshots (the floating thumbnail and markup editor; SystemUI's own preview
# is off, see overlay/common SystemUI config) and Call Notes (on-device notes of CubeLine calls; no internet).
PRODUCT_PACKAGES += \
    CubeFiles \
    CubeBattery \
    CubeClipboard \
    CubePDF \
    CubeShare \
    CubeScreenRecorder \
    CubeScreenshots \
    CallNotes

# CubeOS: safety and everyday apps (packages/apps/CubeOSApps/prebuilts):
# Link Checker (checks every tapped link; the default link handler, see overlay),
# Up NEPA (power-supply tracker; persistent for instant mains detection),
# Go-Slow (live road intelligence) and Private Locker (hidden encrypted vault).
PRODUCT_PACKAGES += \
    LinkChecker \
    UpNepa \
    GoSlow \
    PrivateLocker

# CubeOS: Themes & Wallpapers (prebuilts/CubeThemes), signed, updating wallpaper and theme library;
# applies system accent colours, wallpapers and Cube Home appearance with Undo.
PRODUCT_PACKAGES += \
    CubeThemes

# CubeOS: everyday Nigerian essentials (prebuilts). Quick Codes (signed USSD shortcuts + balance
# checker), Cube Calculator (naira converter; overrides ExactCalculator), Weather (nowcast + flood
# alerts), Cube Clock (prayer times, Qibla, daily verse; overrides DeskClock) and FM Radio (MediaTek
# tuner via /dev/fm).
PRODUCT_PACKAGES += \
    QuickCodes \
    CubeCalculator \
    CubeWeather \
    CubeClock \
    CubeRadio

# CubeOS: Cube Camera is THE system camera (prebuilts/CubeCamera; overrides Camera2/Aperture and
# pulls in CubeCameraSystemUIOverlay so double-press power opens it).
PRODUCT_PACKAGES += \
    CubeCamera

# CubeOS: identity & security (prebuilts). Wallet (encrypted offline ID documents), Passwords
# (vault + AutoFill service) and Contacts Backup (end-to-end-encrypted contacts in the Cube Account).
PRODUCT_PACKAGES += \
    CubeWallet \
    CubePasswords \
    CubeContactsBackup

# CubeOS: Cube Island (prebuilts/CubeIsland), the live-activity island around the camera cutout:
# calls, media, timers, navigation, downloads, charging and notification banners. Privileged and
# persistent (status-bar panel window); not on AppHub. Its two overlays (packages/apps/CubeOSApps/
# island/overlays), switched on by the island while it runs: CubeIslandCutout reserves the
# centred band around the camera, CubeIslandStatusBar hides the status bar's notification icons,
# CubeStatusIcons (island/overlays/icons) are the iOS-style Wi-Fi icons.
PRODUCT_PACKAGES += \
    CubeIsland \
    CubeIslandCutout \
    CubeIslandStatusBar \
    CubeStatusIcons

# CubeOS: Face Unlock — camera-only, convenience-class (Class 1). See config/face_unlock.mk.
include vendor/lineage/config/face_unlock.mk

# CubeOS: the network location provider (Wi-Fi / cell positioning). See config/cube_location.mk.
include vendor/lineage/config/cube_location.mk

# CubeOS: CubeLine, and the Messages and Phone apps built on it (default SMS app and dialer).
# See config/cubeline.mk.
include vendor/lineage/config/cubeline.mk

# CubeOS: the thirteen ContiSX apps (vendor/contisx) — Exchange, Shield, Sage, Decision Lab,
# CSD, Boardroom, Vault, Goals, Collectives and the ContiSX Office apps (Inventory,
# Accounting, HR, Payments), on one ContiSX account.
$(call inherit-product-if-exists, vendor/contisx/contisx.mk)

ifeq ($(PRODUCT_TYPE), go)
PRODUCT_PACKAGES += \
    TrebuchetQuickStepGo

PRODUCT_DEXPREOPT_SPEED_APPS += \
    TrebuchetQuickStepGo
else
PRODUCT_PACKAGES += \
    TrebuchetQuickStep

PRODUCT_DEXPREOPT_SPEED_APPS += \
    TrebuchetQuickStep
endif

PRODUCT_PACKAGES += \
    TrebuchetOverlay

# Charger
PRODUCT_PACKAGES += \
    charger_res_images

ifneq ($(WITH_LINEAGE_CHARGER),false)
PRODUCT_PACKAGES += \
    lineage_charger_animation \
    lineage_charger_animation_vendor
endif

# Customizations
PRODUCT_PACKAGES += \
    IconPackCircularAndroidOverlay \
    IconPackCircularLauncherOverlay \
    IconPackCircularSettingsOverlay \
    IconPackCircularSystemUIOverlay \
    IconPackFilledAndroidOverlay \
    IconPackFilledLauncherOverlay \
    IconPackFilledSettingsOverlay \
    IconPackFilledSystemUIOverlay \
    IconPackKaiAndroidOverlay \
    IconPackKaiLauncherOverlay \
    IconPackKaiSettingsOverlay \
    IconPackKaiSystemUIOverlay \
    IconPackRoundedAndroidOverlay \
    IconPackRoundedLauncherOverlay \
    IconPackRoundedSettingsOverlay \
    IconPackRoundedSystemUIOverlay \
    IconPackSamAndroidOverlay \
    IconPackSamLauncherOverlay \
    IconPackSamSettingsOverlay \
    IconPackSamSystemUIOverlay \
    IconPackVictorAndroidOverlay \
    IconPackVictorLauncherOverlay \
    IconPackVictorSettingsOverlay \
    IconPackVictorSystemUIOverlay \
    IconShapePebbleOverlay \
    IconShapeRoundedRectOverlay \
    IconShapeSquareOverlay \
    IconShapeSquircleOverlay \
    IconShapeTaperedRectOverlay \
    IconShapeTeardropOverlay \
    IconShapeVesselOverlay

# Legal
PRODUCT_SYSTEM_PROPERTIES += \
    ro.lineagelegal.url=https://cubeapp.org/legal

# Media
PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    media.recorder.show_manufacturer_and_model=true

# SystemUI plugins
PRODUCT_PACKAGES += \
    QuickAccessWallet

# TextClassifier
PRODUCT_PACKAGES += \
    libtextclassifier_annotator_en_model \
    libtextclassifier_annotator_universal_model \
    libtextclassifier_actions_suggestions_universal_model \
    libtextclassifier_lang_id_model

PRODUCT_ARTIFACT_PATH_REQUIREMENT_ALLOWED_LIST += \
    system/etc/textclassifier/actions_suggestions.universal.model \
    system/etc/textclassifier/lang_id.model \
    system/etc/textclassifier/textclassifier.en.model \
    system/etc/textclassifier/textclassifier.universal.model

# Themes
PRODUCT_PACKAGES += \
    LineageBlackTheme \
    ThemePicker \
    ThemesStub
