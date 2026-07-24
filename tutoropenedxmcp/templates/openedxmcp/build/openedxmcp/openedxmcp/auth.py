"""
Per-request key extraction. Each admin's harness presents its own MCP key as a
Bearer token (or X-MCP-Key header). This middleware pulls it onto a contextvar
for the facade client to forward. No validation here — the openedx-mcp facade is
the sole authority (resolves user + live is_staff/superuser from the key).
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .client import current_key


def _extract_key(request):
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.headers.get("X-MCP-Key")


class KeyHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        key = _extract_key(request)
        if not key:
            return JSONResponse(
                {"error": "Missing MCP key. Send it as 'Authorization: Bearer <key>'."},
                status_code=401,
            )
        token = current_key.set(key)
        try:
            return await call_next(request)
        finally:
            current_key.reset(token)
