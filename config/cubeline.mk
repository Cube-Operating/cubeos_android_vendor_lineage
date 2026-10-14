# Cubeline: the core of CubeOS. Every phone has a Cubeline account (an on-chain number, ENS on
# CUBEX): setup requires creating one, and it is the account every Cube app signs in with.
#
#   CubeApp       ng.cube.app           the Cubeline core: holds the phone's Cubeline identity
#                                       (Session account, private key), runs Cubeline sign-up /
#                                       log in for the system account, serves the CubeLine API
#   CubeAccount   org.cubeapp.account   the system Cubeline account (AccountManager type
#                                       org.cubeapp.cubeline), listed in common_mobile.mk
#   CubeMessages  org.cubeapp.messages  SMS/MMS + Cubeline chats; replaces AOSP Messaging (messaging)
#   CubePhone     org.cubeapp.phone     dialer and in-call screen; replaces Dialer
#
# Prebuilt system_ext apps (Gradle-built): CubeOSApps/prebuilts/{CubeApp,CubeMessages,CubePhone}.
# Messages and Phone are privileged and presigned with the platform key; Cube App keeps its own
# key. Each module pulls in its permission files through `required`.
# The overlay makes Phone the default dialer and Messages the default SMS app.
# Refresh with CubeOSApps/tools/update-prebuilts.sh (Messages, Phone) and
# CubeOSApps/tools/update-cubeapp.sh (Cube App). See CubeOSApps/CUBELINE_OS.md.
# The old CubeLine service (org.cubeapp.cubeline, CubeChat PINs) is no longer shipped.
#
# Set CUBE_LINE := false to build with the stock Dialer and Messaging instead.

ifneq ($(CUBE_LINE),false)

PRODUCT_PACKAGES += \
    CubeApp \
    CubeMessages \
    CubePhone

PRODUCT_PACKAGE_OVERLAYS += vendor/lineage/overlay/cubeline

endif
