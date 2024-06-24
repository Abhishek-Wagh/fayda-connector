# ruff: noqa: E402

from .config import Settings

_config = Settings.get_config()


from openg2p_fastapi_common.app import Initializer
from .services.fayda_connector import FaydaIdConnectorService
from .controllers.health_controller import HealthCheckController



class Initializer(Initializer):
    def initialize(self, **kwargs):
        super().initialize()
        # Initialize all Services, Controllers, any utils here.
        FaydaIdConnectorService()
        HealthCheckController().post_init()

