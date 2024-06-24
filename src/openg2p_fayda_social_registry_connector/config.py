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
    reg_ids_api_url: str = "http://localhost:8069/api/v1/registry/get_ids"
    get_fayda_number_api_url: str = "http://localhost:8000/get-fayda-number"
    update_individual_api_url: str = "http://localhost:8069/api/v1/registry/update_individual"
    openg2p_authenticate_api_url: str = "http://localhost:8069/web/session/authenticate"
    openg2p_authenticate_database: str = ""
    openg2p_authenticate_username: str = ""
    openg2p_authenticate_password: str=""
    include_id_type: str = "rid"
    exclude_id_type: str = "UIN"
    id_type: str = "rid"
