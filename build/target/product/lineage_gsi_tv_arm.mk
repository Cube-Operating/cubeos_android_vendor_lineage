# Copyright (C) 2018-2020 The LineageOS Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

$(call inherit-product, build/target/product/gsi_release.mk)
$(call inherit-product, device/google/atv/products/aosp_tv_arm.mk)

include vendor/lineage/build/target/product/lineage_generic_tv_target.mk

TARGET_NO_KERNEL_OVERRIDE := true

PRODUCT_NAME := lineage_gsi_tv_arm

# Cube SmartTV (CVTE V3520N0E, Android 12 vendor = VNDK 31): its system partition is a fixed
# 1024 MiB, and the five VNDK snapshots from gsi_release.mk (30-34, ~117 MB) don't fit beside the
# rest. The TV only needs v31.
PRODUCT_EXTRA_VNDK_VERSIONS := 31

# DEBUG ONLY (remove before any release): save cubeOS's boot log to the TV's cache partition.
PRODUCT_COPY_FILES += \
    vendor/lineage/prebuilt/cube-smarttv-debug/cubedbg.sh:$(TARGET_COPY_OUT_SYSTEM)/bin/cubedbg.sh \
    vendor/lineage/prebuilt/cube-smarttv-debug/cubedbg.rc:$(TARGET_COPY_OUT_SYSTEM)/etc/init/cubedbg.rc

PRODUCT_ENFORCE_ARTIFACT_PATH_REQUIREMENTS :=
