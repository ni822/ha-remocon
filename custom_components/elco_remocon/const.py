"""Constants for the Elco Remocon-Net integration."""

DOMAIN = "elco_remocon"
CONF_GATEWAY_ID = "gateway_id"
CONF_ZONE = "zone"
CONF_SYSTEM_TYPE = "system_type"

SYSTEM_HEAT_PUMP = "heat_pump"
SYSTEM_BOILER = "boiler"  # oil / gas boiler (conventional burner)
SYSTEM_TYPES = [SYSTEM_HEAT_PUMP, SYSTEM_BOILER]
DEFAULT_SYSTEM_TYPE = SYSTEM_HEAT_PUMP

DEFAULT_ZONE = "1"
DEFAULT_SCAN_INTERVAL = 120  # seconds (legacy default)

# Options: polling interval in minutes (1..1440)
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL_MIN = DEFAULT_SCAN_INTERVAL // 60
MIN_SCAN_INTERVAL_MIN = 1
MAX_SCAN_INTERVAL_MIN = 1440  # 24 h

# API mode values
MODE_PROTECTION = 0
MODE_AUTOMATIC = 1
MODE_REDUCTION = 2
MODE_COMFORT = 3


def uid_prefix(gateway_id: str, zone: str | int = DEFAULT_ZONE) -> str:
    """Prefix of entity/entry unique ids. Zone 1 keeps the historical ``<gateway>`` form.

    Other zones use ``<gateway>_zone_<n>``, the same scheme as upstream ha-remocon
    (identifiers.entity_unique_id), so entities keep their ids if you switch to it.
    """
    zone = str(zone).strip() or DEFAULT_ZONE
    return gateway_id if zone == DEFAULT_ZONE else f"{gateway_id}_zone_{zone}"
