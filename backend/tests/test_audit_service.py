from starlette.requests import Request

from app.config import settings
from app.services import audit_service


def _build_request(client_host, headers=None):
    raw_headers = []
    for key, value in (headers or {}).items():
      raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    scope = {
      "type": "http",
      "method": "GET",
      "path": "/api/v1/auth/login",
      "headers": raw_headers,
      "query_string": b"",
      "client": (client_host, 12345),
    }
    return Request(scope)


def test_audit_ip_ignores_forwarded_headers_from_untrusted_proxy(monkeypatch):
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", "10.0.0.1")

    request = _build_request(
      "203.0.113.50",
      {
        "x-forwarded-for": "198.51.100.9",
        "x-real-ip": "198.51.100.10",
      },
    )

    assert audit_service.get_client_ip(request) == "203.0.113.50"


def test_audit_ip_accepts_forwarded_header_from_trusted_proxy(monkeypatch):
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", "10.0.0.1")

    request = _build_request(
      "10.0.0.1",
      {
        "x-forwarded-for": "198.51.100.9, 10.0.0.1",
      },
    )

    assert audit_service.get_client_ip(request) == "198.51.100.9"
