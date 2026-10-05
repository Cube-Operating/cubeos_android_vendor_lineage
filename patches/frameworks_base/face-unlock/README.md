# Face Unlock — frameworks/base patches

Apply onto `frameworks/base` (Cube-Operating/cubeos_android_frameworks_base, branch
`cubeos-22.2`) before building with Face Unlock:

    cd frameworks/base
    git am ../../vendor/lineage/patches/frameworks_base/face-unlock/*.patch

| Patch | From | What |
|---|---|---|
| 0001 | crDroid 15.0 `231cdc8` (AOSPA ParanoidSense, Apache-2.0) | FaceSense provider: `services/core/.../biometrics/sensors/face/sense/*`, binds a face service in a system app; SystemUI bypass and privacy-chip tweaks |
| 0002 | crDroid 15.0 `6d38378` | haptic on successful face authentication |
| 0003 | crDroid 15.0 `bbef6ab` | FaceService: add the provider when `ro.face.sense_service` is set |
| 0004 | crDroid 15.0 `2805f32` | AuthService/FaceService: register it even without HIDL/AIDL face HALs |
| 0005 | CubeOS | point it at `org.cubeapp.face/.sense.SenseHalService` (action `org.cubeapp.face.SENSE_BIND`) and register it as **STRENGTH_CONVENIENCE** (Class 1) instead of WEAK |

Checked on 2026-10-05: the series applies cleanly (`git am -3`) to the touched files of both
LineageOS `lineage-22.2` and `cubeos_android_frameworks_base` `cubeos-22.2`. Not yet compiled —
that needs the Linux build machine (see CubeOSApps/face/FACE_UNLOCK.md, test plan).

`services/core` links the static library `vendor.aospa.biometrics.face`, which CubeOS builds
from `packages/apps/CubeOSApps/face/Android.bp` (the ParanoidSense AIDL, Apache-2.0). No
ParanoidSense binaries (its proprietary Megvii engine) are used anywhere.
