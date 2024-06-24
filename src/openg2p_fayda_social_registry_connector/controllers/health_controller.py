from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import InternalServerError
from ..schemas.health_check_schema import HealthCheckStatus
from ..services.fayda_connector import FaydaIdConnectorService


class HealthCheckController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fayda_connector_services = FaydaIdConnectorService.get_component()
        self.router.tags += ["Health"]

        self.router.add_api_route(
            "/health",
            self.get_health,
            responses={200: {"model": HealthCheckStatus}},
            methods=["GET"],
        )

    async def get_health(self):
        if self.fayda_connector_services.is_runner_thread_alive():
            return HealthCheckStatus(status = "healthy")
        else:
            raise InternalServerError(code="G2P-FAYDA-500", message="Connector Job is not Active",)
