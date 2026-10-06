# CubeOS Location (packages/apps/CubeOSApps/location, org.cubeapp.location): the OS "network"
# location provider — Wi-Fi and cell positioning through the Google Geolocation API with
# BeaconDB as fallback — which Google Play services supplies on other Android phones. Every app
# that asks LocationManager / the fused provider for a location gets indoor fixes from it.
#
# Bound by LocationManagerService through the framework overlay in
# overlay/common/frameworks/base/core/res/res/values/config.xml
# (config_enableNetworkLocationOverlay=false, config_networkLocationProviderPackageName).
#
# The Google API key is not in any repository. Before `m`, run
#     CUBE_GEOLOCATION_API_KEY=... packages/apps/CubeOSApps/location/tools/install-api-key.sh
# Without a key the provider still works with BeaconDB only.
# Set CUBE_NETWORK_LOCATION := false to build without a network location provider.
# See CubeOSApps/location/CUBE_LOCATION.md.

ifneq ($(CUBE_NETWORK_LOCATION),false)

# CubeLocation pulls in, through `required`: its privapp/default-permissions/sysconfig files and
# CubeLocationWifiOverlay (the Wi-Fi scan-throttle exception).
PRODUCT_PACKAGES += \
    CubeLocation

endif
