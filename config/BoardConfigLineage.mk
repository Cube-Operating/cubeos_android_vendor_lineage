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
