PRODUCT_VERSION_MAJOR = 22
PRODUCT_VERSION_MINOR = 2

ifeq ($(LINEAGE_VERSION_APPEND_TIME_OF_DAY),true)
    LINEAGE_BUILD_DATE := $(shell date -u +%Y%m%d_%H%M%S)
else
    LINEAGE_BUILD_DATE := $(shell date -u +%Y%m%d)
endif

# Set LINEAGE_BUILDTYPE from the env RELEASE_TYPE, for jenkins compat

ifndef LINEAGE_BUILDTYPE
    ifdef RELEASE_TYPE
        # Starting with "LINEAGE_" is optional
        RELEASE_TYPE := $(shell echo $(RELEASE_TYPE) | sed -e 's|^LINEAGE_||g')
        LINEAGE_BUILDTYPE := $(RELEASE_TYPE)
    endif
endif

# Filter out random types, so it'll reset to UNOFFICIAL
ifeq ($(filter RELEASE NIGHTLY SNAPSHOT EXPERIMENTAL,$(LINEAGE_BUILDTYPE)),)
    LINEAGE_BUILDTYPE := UNOFFICIAL
    LINEAGE_EXTRAVERSION :=
endif

ifeq ($(LINEAGE_BUILDTYPE), UNOFFICIAL)
    ifneq ($(TARGET_UNOFFICIAL_BUILD_ID),)
        LINEAGE_EXTRAVERSION := -$(TARGET_UNOFFICIAL_BUILD_ID)
    endif
endif

LINEAGE_VERSION_SUFFIX := $(LINEAGE_BUILD_DATE)-$(LINEAGE_BUILDTYPE)$(LINEAGE_EXTRAVERSION)-$(LINEAGE_BUILD)

# Internal version
LINEAGE_VERSION := $(PRODUCT_VERSION_MAJOR).$(PRODUCT_VERSION_MINOR)-$(LINEAGE_VERSION_SUFFIX)

# Display version
LINEAGE_DISPLAY_VERSION := $(PRODUCT_VERSION_MAJOR)-$(LINEAGE_VERSION_SUFFIX)

# LineageOS version properties
PRODUCT_SYSTEM_PROPERTIES += \
    ro.lineage.version=$(LINEAGE_VERSION) \
    ro.lineage.display.version=$(LINEAGE_DISPLAY_VERSION) \
    ro.lineage.build.version=$(PRODUCT_VERSION_MAJOR).$(PRODUCT_VERSION_MINOR) \
    ro.lineage.releasetype=$(LINEAGE_BUILDTYPE)

# CubeOS version
# CubeOS numbers its own releases. The LineageOS/Android base it is built on
# is recorded in ro.cube.base and shown only in legal notices.
CUBEOS_VERSION_MAJOR := 1
CUBEOS_VERSION_MINOR := 7
# CubeOS 1.7.1 (owner, 2026-11-16): the ContiSX line after 1.0. Same major, so these phones
# stay on the 1.x update channel and 1.0 phones accept it (Cube Update compares major.minor).
CUBEOS_VERSION_PATCH := 1
CUBEOS_VERSION_NUMBER := $(CUBEOS_VERSION_MAJOR).$(CUBEOS_VERSION_MINOR).$(CUBEOS_VERSION_PATCH)

# Internal version, e.g. 1.7.1-20261116-UNOFFICIAL-ygf_f35
CUBEOS_VERSION := $(CUBEOS_VERSION_NUMBER)-$(LINEAGE_VERSION_SUFFIX)

# Display version, as shown in Settings > About phone
CUBEOS_DISPLAY_VERSION := $(CUBEOS_VERSION_NUMBER)-$(LINEAGE_VERSION_SUFFIX)

PRODUCT_PRODUCT_PROPERTIES += \
    ro.cube.version=$(CUBEOS_VERSION) \
    ro.cube.display.version=$(CUBEOS_DISPLAY_VERSION) \
    ro.cube.build.version=$(CUBEOS_VERSION_NUMBER) \
    ro.cube.releasetype=$(LINEAGE_BUILDTYPE) \
    ro.cube.base=LineageOS-$(PRODUCT_VERSION_MAJOR).$(PRODUCT_VERSION_MINOR)
