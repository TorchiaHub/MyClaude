from urllib.parse import urlsplit

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp

__all__ = ["MUTATING_METHODS", "is_allowed_origin", "OriginGuardMiddleware"]

MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def is_allowed_origin(origin: str, *, scheme: str, hostname: str | None, port: int | None) -> bool:
    parsed = urlsplit(origin)
    return bool(parsed.scheme) and (parsed.scheme, parsed.hostname, parsed.port) == (
        scheme,
        hostname,
        port,
    )


class OriginGuardMiddleware:
    """Rejects state-changing requests whose `Origin` header doesn't match
    this server's own scheme/host/port — a CSRF defense for a local,
    single-user app with no other auth boundary. Requests with no `Origin`
    header (curl, the SessionStart hook, non-browser tooling) are allowed
    through: the threat model here is a malicious page open in the same
    browser, and browsers always send `Origin` on state-changing fetches,
    same-origin or not."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http" and self._rejects(scope):
            response = JSONResponse(
                {"detail": "Origin non consentita per questa richiesta."}, status_code=403
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

    def _rejects(self, scope) -> bool:
        request = Request(scope)
        if request.method not in MUTATING_METHODS:
            return False
        origin = request.headers.get("origin")
        if not origin:
            return False
        return not is_allowed_origin(
            origin,
            scheme=request.url.scheme,
            hostname=request.url.hostname,
            port=request.url.port,
        )
