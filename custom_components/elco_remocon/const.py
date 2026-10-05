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
