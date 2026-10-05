# CubeOS Face Unlock (packages/apps/CubeOSApps/face, org.cubeapp.face).
#
# A camera-only face match: Android biometric Class 1 ("convenience"). It may dismiss the
# keyguard, always with the PIN/pattern/password as fallback (and required after a restart,
# after 4 hours and after 5 failed attempts). It is never offered to BiometricPrompt, payments,
# Vault or Keystore auth-bound keys. See CubeOSApps/face/FACE_UNLOCK.md.
#
# Needs the frameworks/base FaceSense provider patches in
# vendor/lineage/patches/frameworks_base/face-unlock (git am onto frameworks/base).
# Set CUBE_FACE_UNLOCK := false to build without it.

ifneq ($(CUBE_FACE_UNLOCK),false)

PRODUCT_PACKAGES += \
    CubeFaceUnlock

# Turns on the FaceSense provider in FaceService / AuthService.
PRODUCT_SYSTEM_EXT_PROPERTIES += \
    ro.face.sense_service=true

# FaceService only starts on devices that declare the face feature.
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.biometrics.face.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/android.hardware.biometrics.face.xml

endif
