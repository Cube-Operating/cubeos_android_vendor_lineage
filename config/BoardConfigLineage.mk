# CubeOS boot animation, a prebuilt bootanimation.zip (bootanimation/cubeos) per line, instead of
# the generated logo:
#   CubeOS 1.x (ContiSX phones): ContiSX / "powered by cubeOS" (make-bootanimation.py)
#   CubeOS 2.x (Cube Phones): the Cube mark's three plates, after Runyee's signed Cube logo
#                             (make-bootanimation-cube.py)
#   Cube SmartTV (lineage_gsi_tv_arm on the CVTE TV): Cube mark + "Cube SmartTV" + progress bar,
#                             1920x1080 with trimmed strips (cubeos-tv/make-tv-boot.py)
ifeq ($(TARGET_PRODUCT),lineage_gsi_tv_arm)
TARGET_BOOTANIMATION ?= vendor/lineage/bootanimation/cubeos-tv/bootanimation.zip
endif
ifeq ($(CUBEOS_VERSION_MAJOR),2)
TARGET_BOOTANIMATION ?= vendor/lineage/bootanimation/cubeos/bootanimation-cube.zip
endif
TARGET_BOOTANIMATION ?= vendor/lineage/bootanimation/cubeos/bootanimation.zip

# SPDX-FileCopyrightText: 2017-2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0

# Recovery
BOARD_USES_FULL_RECOVERY_IMAGE ?= true

include vendor/lineage/config/BoardConfigKernel.mk

ifeq ($(BOARD_USES_QCOM_HARDWARE),true)
    include hardware/qcom-caf/common/BoardConfigQcom.mk
endif

include vendor/lineage/config/BoardConfigSoong.mk

# CubeOS: Face Unlock (org.cubeapp.face) runs as the system uid and opens the front camera
# from the face service at the lock screen. See sepolicy/face_unlock.
ifneq ($(CUBE_FACE_UNLOCK),false)
SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS += vendor/lineage/sepolicy/face_unlock/private
endif
