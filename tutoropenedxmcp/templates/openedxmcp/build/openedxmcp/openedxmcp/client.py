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
_MAX_TEXT = 300

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


def _summarize_text(resp):
    """Short stand-in for a non-JSON body. Never forward a whole HTML page: an
    LMS error page carries the caller's username, profile-image URL and ~10 KB
    of markup into the model's context."""
    ctype = resp.headers.get("content-type", "")
    text = resp.text.strip()
    if "html" in ctype or text[:15].lower().startswith(("<!doctype", "<html")):
        return (f"Upstream returned an HTML page (HTTP {resp.status_code}) instead of "
                "JSON; see the LMS/CMS logs for the cause.")
    return text if len(text) <= _MAX_TEXT else text[:_MAX_TEXT] + "… [truncated]"


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
                detail = _summarize_text(resp)
            raise FacadeError(resp.status_code, detail)
        ctype = resp.headers.get("content-type", "")
        return resp.json() if ctype.startswith("application/json") else {"raw": _summarize_text(resp)}
