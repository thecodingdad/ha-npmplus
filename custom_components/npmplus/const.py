"""Constants for the NPMplus integration."""

from homeassistant.const import Platform

DOMAIN = "npmplus"

PLATFORMS: list[Platform] = [Platform.SWITCH]

DEFAULT_SCAN_INTERVAL = 30  # seconds
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 3600

CONF_SCAN_INTERVAL = "scan_interval"
