"""Traba mínima para el despliegue en la nube (ver config.basic_auth_*).

Esto NO es un sistema de autenticación — no hay usuarios, ni sesiones, ni
permisos. Es deliberadamente simple: un login HTTP básico (el cuadro de
usuario/contraseña que el navegador ya sabe mostrar solo) para que la
aplicación no quede completamente abierta a cualquiera que encuentre la
URL de Render. La autenticación real es trabajo de una fase posterior.
"""
import base64
import hmac

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings

_EXEMPT_PATHS = {"/health"}


class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not (settings.basic_auth_user and settings.basic_auth_password):
            return await call_next(request)  # sin credenciales configuradas = sin traba (uso local)
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        if _has_valid_credentials(request, settings.basic_auth_user, settings.basic_auth_password):
            return await call_next(request)

        return Response(
            status_code=401,
            # El valor del header debe ser ASCII puro (los headers HTTP no
            # aceptan UTF-8 de forma confiable): "realm" sin tildes, a
            # propósito, no es un error de tipeo.
            headers={"WWW-Authenticate": 'Basic realm="Segundo Cerebro"'},
        )


def _has_valid_credentials(request: Request, expected_user: str, expected_password: str) -> bool:
    header = request.headers.get("authorization", "")
    if not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header[len("Basic ") :]).decode("utf-8")
        user, _, password = decoded.partition(":")
    except Exception:  # noqa: BLE001
        return False
    # comparación en tiempo constante — evita filtrar la contraseña por timing
    return hmac.compare_digest(user, expected_user) and hmac.compare_digest(password, expected_password)
