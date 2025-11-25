"""Die Stromkosten Rechner Integration."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

DOMAIN = "stromkosten_rechner"

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Richte die Stromkosten Rechner Komponente ein."""
    return True