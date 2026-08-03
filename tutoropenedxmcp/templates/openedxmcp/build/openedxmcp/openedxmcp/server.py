"""
Open edX Admin MCP server — hosted HTTP (streamable-http) transport.

One always-on service per LMS deployment. Serves many admins; each sends its own
MCP key per request (Bearer). Stateless: all authz is enforced by the openedx-mcp
facade from the key (live is_staff/superuser). Run behind TLS.
"""
import logging
import os

import uvicorn
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse
from starlette.routing import Route

from .auth import KeyHeaderMiddleware
from .client import FacadeClient
from .tools import register_all


async def _health(_request):
    return JSONResponse({"status": "ok", "service": "openedx-mcp-server"})

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("openedxmcp")


def build_app():
    lms = FacadeClient(path_prefix="api/mcp")  # OPENEDXMCP_LMS_BASE_URL
    # Authoring tools live in the CMS (modulestore). Second upstream, same key.
    cms_base = os.environ.get("OPENEDXMCP_CMS_BASE_URL")
    cms = FacadeClient(base_url=cms_base or None, path_prefix="api/mcp/cms")
    security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
    mcp = MCPServer("openedx-admin")
    register_all(mcp, lms, cms)
    # stateless_http and transport_security moved off the constructor onto
    # streamable_http_app() in mcp 2.0.
    app = mcp.streamable_http_app(stateless_http=True, transport_security=security)
    # Unauthenticated liveness route for container/k8s probes (the middleware
    # lets /health through without a key).
    app.router.routes.append(Route("/health", _health, methods=["GET"]))
    app.add_middleware(KeyHeaderMiddleware)
    return app


def main():
    host = os.environ.get("OPENEDXMCP_HOST", "0.0.0.0")
    port = int(os.environ.get("OPENEDXMCP_PORT", "8080"))
    log.info("Starting Open edX Admin MCP server (streamable-http) on %s:%s", host, port)
    uvicorn.run(build_app(), host=host, port=port)


if __name__ == "__main__":
    main()
