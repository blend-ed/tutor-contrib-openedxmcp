"""
Thin HTTP client for the openedx-mcp facade.

Hosted-HTTP model: ONE MCP service serves many admins. The MCP key is NOT a
server secret — it arrives per request in the caller's Authorization header,
is stashed in a contextvar by the auth middleware, and forwarded to the facade
as X-MCP-Key. Two upstreams: LMS (/api/mcp/) and CMS (/api/mcp/cms/).
"""
import contextvars
import os

import httpx

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)

# Set per request by KeyHeaderMiddleware.
current_key: "contextvars.ContextVar[str | None]" = contextvars.ContextVar(
    "current_key", default=None)


class FacadeError(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"facade {status_code}: {detail}")


class MissingKeyError(Exception):
    pass


class FacadeClient:
    def __init__(self, base_url=None, path_prefix="api/mcp"):
        base_url = base_url or os.environ.get("OPENEDXMCP_LMS_BASE_URL")
        if not base_url:
            raise RuntimeError("OPENEDXMCP_LMS_BASE_URL is not set.")
        self._base = base_url.rstrip("/")
        self._prefix = path_prefix.strip("/")
        self._client = httpx.Client(timeout=_TIMEOUT, headers={"Accept": "application/json"})

    def _url(self, path):
        return f"{self._base}/{self._prefix}/{path.lstrip('/')}"

    def _auth_headers(self):
        key = current_key.get()
        if not key:
            raise MissingKeyError("No MCP key on request.")
        return {"X-MCP-Key": key}

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, json=None):
        return self._request("POST", path, json=json)

    def _request(self, method, path, params=None, json=None):
        resp = self._client.request(method, self._url(path), params=params, json=json,
                                    headers=self._auth_headers())
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:  # noqa: BLE001
                detail = resp.text
            raise FacadeError(resp.status_code, detail)
        ctype = resp.headers.get("content-type", "")
        return resp.json() if ctype.startswith("application/json") else {"raw": resp.text}
