from openg2p_fastapi_common.config import Settings
from pydantic_settings import SettingsConfigDict
from . import __version__

class Settings(Settings):
    model_config = SettingsConfigDict(env_prefix="fayda_connector_", env_file=".env", extra="allow")

    openapi_title: str = "OpenG2P Fayda Social Registry Connector"
    openapi_description: str = """
    This module implements G2P Connect Disburse APIs.
    It contains API layer and multiplexer for different payment backends.

    ***********************************
    Further details goes here
    ***********************************
    """
    openapi_version: str = __version__

    initial_delay_secs: int = 5  # Initial delay in seconds
    interval_secs: int = 10
    port: int = 8090



