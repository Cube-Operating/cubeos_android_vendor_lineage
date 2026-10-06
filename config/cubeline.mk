# CubeLine (packages/apps/CubeOSApps): free messaging and calls between CubeOS phones, and the
# phone's own Messages and Phone apps built on it.
#
#   CubeLine      org.cubeapp.cubeline  the persistent service: one connection for the phone,
#                                       end-to-end encryption, a Telecom ConnectionService
#   CubeMessages  org.cubeapp.messages  SMS/MMS + CubeLine; replaces AOSP Messaging (messaging)
#   CubePhone     org.cubeapp.phone     dialer and in-call screen; replaces Dialer
#
# Prebuilt privileged system_ext apps (Gradle-built; Compose, LiveKit/WebRTC), presigned with
# the platform key, like Cube Health: CubeOSApps/prebuilts/{CubeLine,CubeMessages,CubePhone}.
# Each module pulls in its privapp and default-permissions files (and CubeLine its power-save
# exemption) through `required`.
# The overlay makes Phone the default dialer and Messages the default SMS app.
# Refresh the APKs with CubeOSApps/tools/update-prebuilts.sh. See CubeOSApps/CUBELINE_OS.md.
#
# Set CUBE_LINE := false to build with the stock Dialer and Messaging instead.

ifneq ($(CUBE_LINE),false)

PRODUCT_PACKAGES += \
    CubeLine \
    CubeMessages \
    CubePhone

PRODUCT_PACKAGE_OVERLAYS += vendor/lineage/overlay/cubeline

endif
