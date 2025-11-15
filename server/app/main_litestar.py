from litestar import Litestar, get
from litestar.plugins.prometheus import PrometheusConfig, PrometheusController

prom_config = PrometheusConfig()

@get("/")
async def root() -> str:
    return "root"

app = Litestar(
    route_handlers=[root, PrometheusController],
    middleware=[prom_config.middleware],
)